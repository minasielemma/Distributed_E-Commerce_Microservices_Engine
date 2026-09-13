import os
import sys
import json
import time
import logging
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_project.settings")
django.setup()

from django.db import transaction, models
from inventory.models import InventoryItem, StockMovement, OutboxEvent, ProcessedEvent

try:
    from kafka import KafkaConsumer
except ImportError:
    from kafka_ng import KafkaConsumer

logger = logging.getLogger("inventory_saga_consumer")
logging.basicConfig(level=logging.INFO)


def process_payment_succeeded(event_id, payload):
    order_id = payload.get('order_id')
    items = payload.get('items', [])
    product_id = payload.get('product_id')
    quantity = payload.get('quantity', 1)

    if not items and product_id:
        items = [{'product_id': product_id, 'quantity': quantity}]

    with transaction.atomic():
        if ProcessedEvent.objects.filter(event_id=event_id).exists():
            logger.info(f"[Inventory Saga] Event {event_id} already processed. Skipping.")
            return

        all_reserved = True
        reservations = []

        for item in items:
            p_id = str(item.get('product_id'))
            qty = int(item.get('quantity', 1))

            inv_item = InventoryItem.objects.filter(product_id=p_id).first()
            if not inv_item or inv_item.quantity_available < qty:
                all_reserved = False
                logger.warning(f"[Inventory Saga] Insufficient stock for product {p_id} (requested {qty})")
                break
            reservations.append((inv_item, qty))

        if all_reserved and reservations:
            for inv_item, qty in reservations:
                inv_item.quantity_available -= qty
                inv_item.quantity_reserved += qty
                inv_item.save(update_fields=['quantity_available', 'quantity_reserved', 'updated_at'])

                StockMovement.objects.create(
                    tenant_id=inv_item.tenant_id,
                    inventory_item=inv_item,
                    movement_type='RESERVED',
                    quantity=qty,
                    reference_id=f"ORDER-{order_id}"
                )

            OutboxEvent.objects.create(
                event_type='inventory.reserved',
                payload={
                    'order_id': str(order_id),
                    'items': items
                }
            )
            logger.info(f"[Inventory Saga] Stock RESERVED successfully for order {order_id}")
        else:
            OutboxEvent.objects.create(
                event_type='inventory.failed',
                payload={
                    'order_id': str(order_id),
                    'reason': 'Insufficient stock during reservation'
                }
            )
            logger.info(f"[Inventory Saga] Stock reservation FAILED for order {order_id}")

        ProcessedEvent.objects.create(event_id=event_id, event_type='payment.succeeded')


def process_stock_release(event_id, payload):
    order_id = payload.get('order_id')
    ref_id = f"ORDER-{order_id}"

    with transaction.atomic():
        if ProcessedEvent.objects.filter(event_id=event_id).exists():
            logger.info(f"[Inventory Saga] Event {event_id} already processed. Skipping.")
            return

        reserved_movements = StockMovement.objects.filter(reference_id=ref_id, movement_type='RESERVED')
        for movement in reserved_movements:
            inv_item = movement.inventory_item
            inv_item.quantity_reserved = max(0, inv_item.quantity_reserved - movement.quantity)
            inv_item.quantity_available += movement.quantity
            inv_item.save(update_fields=['quantity_available', 'quantity_reserved', 'updated_at'])

            StockMovement.objects.create(
                tenant_id=inv_item.tenant_id,
                inventory_item=inv_item,
                movement_type='RELEASED',
                quantity=movement.quantity,
                reference_id=f"RELEASE-{order_id}"
            )
            logger.info(f"[Inventory Saga] Released {movement.quantity} of item {inv_item.id} for order {order_id}")

        OutboxEvent.objects.create(
            event_type='inventory.released',
            payload={'order_id': str(order_id)}
        )

        ProcessedEvent.objects.create(event_id=event_id, event_type='stock.released')


def run_consumer():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    topic = os.getenv("KAFKA_TOPIC", "ecommerce-events")
    group_id = "inventory-saga-choreography-group"

    logger.info(f"[Inventory Saga Consumer] Connecting to Kafka at {bootstrap_servers}...")

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
            logger.info(f"[Inventory Saga Consumer] Connected to topic '{topic}'. Listening...")
        except Exception as conn_err:
            logger.warning(f"[Inventory Saga Consumer] Connection pending ({conn_err}). Retrying in 5s...")
            time.sleep(5)

    for message in consumer:
        try:
            data = message.value
            event_id = data.get('event_id') or f"{message.topic}-{message.partition}-{message.offset}"
            event_type = data.get('event_type')
            payload = data.get('payload', {})

            if event_type == 'payment.succeeded':
                process_payment_succeeded(event_id, payload)
                consumer.commit()
            elif event_type in ['payment.failed', 'order.cancelled', 'inventory.release']:
                process_stock_release(event_id, payload)
                consumer.commit()
            else:
                consumer.commit()
        except Exception as proc_err:
            logger.error(f"[Inventory Saga Consumer] Error processing message: {proc_err}")


if __name__ == "__main__":
    run_consumer()
