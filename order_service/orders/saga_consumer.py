import os
import sys
import json
import time
import logging
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "order_project.settings")
django.setup()

from django.db import transaction
from orders.models import Order, OutboxEvent, ProcessedEvent

try:
    from kafka import KafkaConsumer
except ImportError:
    from kafka_ng import KafkaConsumer

logger = logging.getLogger("order_saga_consumer")
logging.basicConfig(level=logging.INFO)


def process_inventory_reserved(event_id, payload):
    order_id = payload.get('order_id')

    with transaction.atomic():
        if ProcessedEvent.objects.filter(event_id=event_id).exists():
            logger.info(f"[Order Saga] Event {event_id} already processed. Skipping.")
            return

        try:
            order = Order.objects.get(id=order_id)
            if order.status != 'PAID':
                order.status = 'PAID'
                order.save(update_fields=['status', 'updated_at'])

                OutboxEvent.objects.create(
                    event_type='order.confirmed',
                    payload={
                        'order_id': str(order.id),
                        'customer_id': str(order.customer_id),
                        'total_amount': float(order.total_amount)
                    }
                )
                logger.info(f"[Order Saga] Order {order_id} CONFIRMED and marked PAID.")
        except Order.DoesNotExist:
            logger.warning(f"[Order Saga] Order {order_id} not found.")

        ProcessedEvent.objects.create(event_id=event_id, event_type='inventory.reserved')


def process_inventory_failed(event_id, payload):
    order_id = payload.get('order_id')
    reason = payload.get('reason', 'Stock reservation failed')

    with transaction.atomic():
        if ProcessedEvent.objects.filter(event_id=event_id).exists():
            logger.info(f"[Order Saga] Event {event_id} already processed. Skipping.")
            return

        try:
            order = Order.objects.get(id=order_id)
            order.status = 'FAILED'
            order.save(update_fields=['status', 'updated_at'])

            # Compensating Event: Refund payment since inventory reservation failed
            OutboxEvent.objects.create(
                event_type='payment.refund',
                payload={
                    'order_id': str(order.id),
                    'reason': reason
                }
            )
            logger.info(f"[Order Saga] Order {order_id} marked FAILED. Emitted payment.refund compensating event.")
        except Order.DoesNotExist:
            logger.warning(f"[Order Saga] Order {order_id} not found.")

        ProcessedEvent.objects.create(event_id=event_id, event_type='inventory.failed')


def process_payment_failed(event_id, payload):
    order_id = payload.get('order_id')
    reason = payload.get('reason', 'Payment failed')

    with transaction.atomic():
        if ProcessedEvent.objects.filter(event_id=event_id).exists():
            logger.info(f"[Order Saga] Event {event_id} already processed. Skipping.")
            return

        try:
            order = Order.objects.get(id=order_id)
            order.status = 'FAILED'
            order.save(update_fields=['status', 'updated_at'])

            # Compensating Event: Release any inventory reserved if applicable
            OutboxEvent.objects.create(
                event_type='inventory.release',
                payload={
                    'order_id': str(order.id),
                    'reason': reason
                }
            )
            logger.info(f"[Order Saga] Order {order_id} marked FAILED. Emitted inventory.release compensating event.")
        except Order.DoesNotExist:
            logger.warning(f"[Order Saga] Order {order_id} not found.")

        ProcessedEvent.objects.create(event_id=event_id, event_type='payment.failed')


def run_consumer():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    topic = os.getenv("KAFKA_TOPIC", "ecommerce-events")
    group_id = "order-saga-choreography-group"

    logger.info(f"[Order Saga Consumer] Connecting to Kafka at {bootstrap_servers}...")

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
            logger.info(f"[Order Saga Consumer] Connected to topic '{topic}'. Listening...")
        except Exception as conn_err:
            logger.warning(f"[Order Saga Consumer] Connection pending ({conn_err}). Retrying in 5s...")
            time.sleep(5)

    for message in consumer:
        try:
            data = message.value
            event_id = data.get('event_id') or f"{message.topic}-{message.partition}-{message.offset}"
            event_type = data.get('event_type')
            payload = data.get('payload', {})

            if event_type == 'inventory.reserved':
                process_inventory_reserved(event_id, payload)
                consumer.commit()
            elif event_type == 'inventory.failed':
                process_inventory_failed(event_id, payload)
                consumer.commit()
            elif event_type == 'payment.failed':
                process_payment_failed(event_id, payload)
                consumer.commit()
            else:
                consumer.commit()
        except Exception as proc_err:
            logger.error(f"[Order Saga Consumer] Error processing message: {proc_err}")


if __name__ == "__main__":
    run_consumer()
