import os
import sys
import json
import time
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "payment_project.settings")
django.setup()

from payments.polar_provider import PolarPaymentProvider

try:
    from kafka import KafkaConsumer
except ImportError:
    from kafka_ng import KafkaConsumer

def run_consumer():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    topic = "ecommerce-events"

    print(f"[Payment Kafka Consumer] Connecting to Kafka at {bootstrap_servers}...")
    consumer = None
    while consumer is None:
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                group_id='payment-polar-sync-group'
            )
            print(f"[Payment Kafka Consumer] Connected to topic '{topic}'. Listening for events...")
        except Exception as conn_err:
            print(f"[Payment Kafka Consumer] Kafka connection pending ({conn_err}). Retrying in 5s...")
            time.sleep(5)

    provider = PolarPaymentProvider()

    for message in consumer:
        try:
            data = message.value
            event_type = data.get('event_type')

            if event_type in ['product.created', 'product.updated']:
                product_id = data.get('product_id')
                name = data.get('name')
                description = data.get('description', '')
                price = data.get('price')
                existing_polar_id = data.get('polar_product_id')

                print(f"[Payment Kafka Consumer] Processing {event_type} for product {product_id} ('{name}')")

                polar_id = provider.sync_product_to_polar(product_id, name, price, description, existing_polar_id=existing_polar_id)
                if polar_id:
                    print(f"[Payment Kafka Consumer] SUCCESS: Synced/Verified product {product_id} (Polar ID: {polar_id}, Price: ${price})")
                else:
                    print(f"[Payment Kafka Consumer] WARNING: Sync returned no Polar ID for product {product_id}")
        except Exception as proc_err:
            print(f"[Payment Kafka Consumer] Error processing message: {proc_err}")

if __name__ == "__main__":
    run_consumer()
