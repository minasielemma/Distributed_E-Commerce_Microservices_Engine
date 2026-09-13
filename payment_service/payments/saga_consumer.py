import os
import sys
import json
import time
import logging
from decimal import Decimal
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "payment_project.settings")
django.setup()

from django.db import transaction
from payments.models import Payment, OutboxEvent, ProcessedEvent

try:
    from kafka import KafkaConsumer
except ImportError:
    from kafka_ng import KafkaConsumer

logger = logging.getLogger("payment_saga_consumer")
logging.basicConfig(level=logging.INFO)


def process_order_created(event_id, payload):
    order_id = payload.get('order_id')
    customer_id = payload.get('customer_id')
    tenant_id = payload.get('tenant_id')
    total_amount = Decimal(str(payload.get('total_amount', '0.00')))

    with transaction.atomic():
        if ProcessedEvent.objects.filter(event_id=event_id).exists():
            logger.info(f"[Payment Saga] Event {event_id} already processed. Skipping.")
            return

        payment, created = Payment.objects.get_or_create(
            order_id=order_id,
            defaults={
                'customer_id': customer_id,
                'tenant_id': tenant_id if tenant_id and tenant_id != 'None' else None,
                'amount': total_amount,
                'status': 'PENDING'
            }
        )

        # Process payment logic (simulate success unless total_amount == 999.99 for test failure simulation)
        if total_amount == Decimal('999.99'):
            payment.status = 'FAILED'
            payment.save()
            OutboxEvent.objects.create(
                event_type='payment.failed',
                payload={
                    'order_id': str(order_id),
                    'customer_id': str(customer_id),
                    'reason': 'Payment authorization declined'
                }
            )
            logger.info(f"[Payment Saga] Payment FAILED for order {order_id}")
        else:
            payment.status = 'PAID'
            payment.save()
            OutboxEvent.objects.create(
                event_type='payment.succeeded',
                payload={
                    'order_id': str(order_id),
                    'payment_id': str(payment.id),
                    'customer_id': str(customer_id),
                    'amount': float(total_amount),
                    'items': payload.get('items', [])
                }
            )
            logger.info(f"[Payment Saga] Payment SUCCESS for order {order_id}")

        ProcessedEvent.objects.create(event_id=event_id, event_type='order.created')


def process_payment_refund(event_id, payload):
    order_id = payload.get('order_id')

    with transaction.atomic():
        if ProcessedEvent.objects.filter(event_id=event_id).exists():
            logger.info(f"[Payment Saga] Event {event_id} already processed. Skipping.")
            return

        try:
            payment = Payment.objects.get(order_id=order_id)
            if payment.status in ['PAID', 'PENDING']:
                payment.status = 'REFUNDED'
                payment.save()
                OutboxEvent.objects.create(
                    event_type='payment.refunded',
                    payload={'order_id': str(order_id), 'payment_id': str(payment.id)}
                )
                logger.info(f"[Payment Saga] Compensating transaction: Refunded payment for order {order_id}")
        except Payment.DoesNotExist:
            logger.warning(f"[Payment Saga] Payment for order {order_id} not found for refund.")

        ProcessedEvent.objects.create(event_id=event_id, event_type='payment.refund')


def run_consumer():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    topic = os.getenv("KAFKA_TOPIC", "ecommerce-events")
    group_id = "payment-saga-choreography-group"

    logger.info(f"[Payment Saga Consumer] Connecting to Kafka at {bootstrap_servers}...")

    consumer = None
    while consumer is None:
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                group_id=group_id
            )
            logger.info(f"[Payment Saga Consumer] Connected to topic '{topic}'. Listening...")
        except Exception as conn_err:
            logger.warning(f"[Payment Saga Consumer] Connection pending ({conn_err}). Retrying in 5s...")
            time.sleep(5)

    for message in consumer:
        try:
            data = message.value
            event_id = data.get('event_id') or f"{message.topic}-{message.partition}-{message.offset}"
            event_type = data.get('event_type')
            payload = data.get('payload', {})

            if event_type == 'order.created':
                process_order_created(event_id, payload)
                consumer.commit()
            elif event_type in ['payment.refund', 'order.cancelled', 'inventory.failed']:
                # If inventory failed after payment succeeded, process compensating refund
                process_payment_refund(event_id, payload)
                consumer.commit()
            else:
                consumer.commit()
        except Exception as proc_err:
            logger.error(f"[Payment Saga Consumer] Error processing message: {proc_err}")


if __name__ == "__main__":
    run_consumer()
