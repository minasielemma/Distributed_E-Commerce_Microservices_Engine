import os 
import sys 
import json 
import time 
import django 
from decimal import Decimal 

sys .path .append (os .path .dirname (os .path .dirname (os .path .abspath (__file__ ))))
os .environ .setdefault ("DJANGO_SETTINGS_MODULE","finance_project.settings")
django .setup ()

from finance .accounting_utils import seed_default_accounts ,post_journal_entry ,record_payment_ledger_and_invoice 
from finance .risk_engine import assess_payment_event 

try :
    from kafka import KafkaConsumer 
except ImportError :
    from kafka_ng import KafkaConsumer 


_PROCESSED_ORDER_IDS :set =set ()


def run_consumer ():
    bootstrap_servers =os .getenv ("KAFKA_BOOTSTRAP_SERVERS","kafka:9092")
    topic ="ecommerce-events"

    print (f"[Finance Kafka Consumer] Connecting to Kafka at {bootstrap_servers }...")
    consumer =None 
    while consumer is None :
        try :
            consumer =KafkaConsumer (
            topic ,
            bootstrap_servers =bootstrap_servers ,
            value_deserializer =lambda m :json .loads (m .decode ('utf-8')),
            auto_offset_reset ='earliest',
            group_id ='finance-accounting-group',
            enable_auto_commit =False ,
            )
            print (f"[Finance Kafka Consumer] Connected to topic '{topic }'. Listening for events...")
        except Exception as conn_err :
            print (f"[Finance Kafka Consumer] Kafka connection pending ({conn_err }). Retrying in 5s...")
            time .sleep (5 )

    for message in consumer :
        try :
            data =message .value 
            event_type =data .get ('event_type')
            print (f"[Finance Kafka Consumer] Received event: {event_type } -> Payload: {data }")

            if event_type =='payment.succeeded':
                _handle_payment_succeeded (data )

        except Exception as proc_err :
            print (f"[Finance Kafka Consumer] Error processing message: {proc_err }")
        finally :

            consumer .commit ()


def _handle_payment_succeeded (data :dict ):
    """Process a payment.succeeded event exactly once (idempotent)."""
    from django .db .models import Q 
    from finance .models import Invoice 

    order_id =data .get ('order_id')
    customer_id =data .get ('customer_id')
    tenant_id =data .get ('tenant_id')
    amount_val =Decimal (str (data .get ('amount','0.00')))
    discount_code =data .get ('discount_code')
    discount_amount =Decimal (str (data .get ('discount_amount','0.00')))
    items_summary =data .get ('items',[])

    if not order_id :
        print ("[Finance Kafka Consumer] Skipping event: missing order_id")
        return 


    if order_id in _PROCESSED_ORDER_IDS :
        print (f"[Finance Kafka Consumer] DUPLICATE: order {order_id } already in memory set — skipping.")
        return 


    if Invoice .objects .filter (order_id =order_id ).exists ():
        print (f"[Finance Kafka Consumer] DUPLICATE: Invoice for order {order_id } already exists — skipping.")
        _PROCESSED_ORDER_IDS .add (order_id )
        return 

    if amount_val <=Decimal ('0.00')and discount_amount <=Decimal ('0.00'):
        print (f"[Finance Kafka Consumer] Skipping zero-value event for order {order_id }")
        return 


    entry ,invoice ,ledger_entry =record_payment_ledger_and_invoice (
    order_id =order_id ,
    customer_id =customer_id ,
    tenant_id =tenant_id ,
    total_amount =amount_val ,
    items_summary =items_summary ,
    discount_code =discount_code ,
    discount_amount =discount_amount ,
    )
    print (
    f"[Finance Kafka Consumer] SUCCESS: Posted Journal Entry "
    f"#{getattr (entry ,'entry_number','')}, "
    f"Invoice #{getattr (invoice ,'invoice_number','')} for Order #{order_id }."
    )


    risk_events =assess_payment_event (data )
    if risk_events :
        print (
        f"[Finance Kafka Consumer] RISK: {len (risk_events )} risk event(s) flagged "
        f"for order {order_id }."
        )


    _PROCESSED_ORDER_IDS .add (order_id )


if __name__ =="__main__":
    run_consumer ()
