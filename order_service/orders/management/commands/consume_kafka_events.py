import os
import json
import time
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from orders.models import Order

try:
    from kafka import KafkaConsumer
except ImportError:
    from kafka_ng import KafkaConsumer


def send_kafka_notification(user_id=None, tenant_id=None, title="", message="", notif_type="SYSTEM", metadata=None):
    metadata = metadata or {}
    try:
        try:
            from kafka import KafkaProducer
        except ImportError:
            from kafka_ng import KafkaProducer

        bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'))
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        payload = {
            'title': title,
            'message': message,
            'notification_type': notif_type,
            'metadata': metadata,
        }
        if user_id:
            payload['user_id'] = str(user_id)
        if tenant_id and not user_id:
            payload['tenant_id'] = str(tenant_id)

        event_data = {
            'event_type': 'notification.send',
            'payload': payload
        }
        producer.send('notifications', event_data)
        producer.flush()
        producer.close()
    except Exception as e:
        print(f"[Order Consumer] Failed to publish notification to Kafka: {e}")


class Command(BaseCommand):
    help = 'Runs Kafka event consumer daemon for order_service'

    def handle(self, *args, **options):
        print(f"[Order Kafka Consumer] Connecting to Kafka at {settings.KAFKA_BOOTSTRAP_SERVERS}...")
        
        consumer = None
        while not consumer:
            try:
                consumer = KafkaConsumer(
                    'ecommerce-events',
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    group_id='order_service_group',
                    auto_offset_reset='earliest'
                )
                print("[Order Kafka Consumer] Connected successfully to Kafka topic 'ecommerce-events'. Listening...")
            except Exception as e:
                print(f"[Order Kafka Consumer] Kafka connection pending ({e}). Retrying in 5s...")
                time.sleep(5)

        for message in consumer:
            try:
                data = message.value
                event_type = data.get('event_type')
                payload = data.get('payload', data)
                print(f"[Order Kafka Consumer] Received event: {event_type} -> Payload: {payload}")

                if event_type == 'payment.succeeded':
                    order_id = payload.get('order_id')
                    customer_id = payload.get('customer_id')
                    tenant_id = payload.get('tenant_id')

                    if order_id:
                        with transaction.atomic():
                            try:
                                order = Order.objects.select_for_update().get(id=order_id)
                                order.status = 'PAID'
                                order.save()
                                customer_id = customer_id or str(order.customer_id)
                                tenant_id = tenant_id or str(order.tenant_id)

                                # Create order.paid OutboxEvent for recommendation_service
                                from orders.models import OutboxEvent
                                items_payload = [
                                    {
                                        'product_id': str(item.product_id),
                                        'quantity': item.quantity,
                                        'unit_price': float(item.unit_price)
                                    } for item in order.items.all()
                                ]
                                OutboxEvent.objects.create(
                                    event_type='order.paid',
                                    payload={
                                        'order_id': str(order.id),
                                        'customer_id': str(order.customer_id),
                                        'tenant_id': str(order.tenant_id) if order.tenant_id else None,
                                        'total_amount': float(order.total_amount),
                                        'items': items_payload
                                    },
                                    status='PENDING'
                                )
                                print(f"[Order Kafka Consumer] SUCCESS: Order {order_id} status updated to 'PAID' and order.paid OutboxEvent created.")
                            except Order.DoesNotExist:
                                print(f"[Order Kafka Consumer] Order {order_id} not found in order_db.")

                    # 1. Notify Customer (1 distinct notification for customer)
                    if customer_id:
                        send_kafka_notification(
                            user_id=customer_id,
                            title="Payment Confirmed!",
                            message=f"Your payment for order #{str(order_id)[:8]} was successful.",
                            notif_type="PAYMENT",
                            metadata={'order_id': str(order_id)}
                        )

                    # 2. Notify Shop Owner (1 distinct notification for store owner)
                    if tenant_id:
                        send_kafka_notification(
                            tenant_id=tenant_id,
                            title="New Payment Received!",
                            message=f"New payment received for order #{str(order_id)[:8]}.",
                            notif_type="PAYMENT",
                            metadata={'order_id': str(order_id)}
                        )

                elif event_type in ['shipment.created', 'shipment.status_changed']:
                    customer_id = payload.get('customer_id')
                    tenant_id = payload.get('tenant_id')
                    tracking_code = payload.get('tracking_code')
                    new_status = payload.get('new_status') or payload.get('status')
                    carrier = payload.get('carrier') or 'Standard Carrier'

                    status_upper = str(new_status or '').upper()
                    tracking_str = f" ({tracking_code})" if tracking_code else ""

                    if status_upper == 'SHIPPED':
                        title = "Package Shipped"
                        msg = f"Your package{tracking_str} via {carrier} has been shipped."
                    elif status_upper == 'IN_TRANSIT':
                        title = "Package In Transit"
                        msg = f"Your package{tracking_str} is currently in transit."
                    elif status_upper == 'OUT_FOR_DELIVERY':
                        title = "Out for Delivery"
                        msg = f"Your package{tracking_str} is out for delivery today!"
                    elif status_upper == 'DELIVERED':
                        title = "Package Delivered"
                        msg = f"Your package{tracking_str} has been delivered successfully."
                    elif status_upper in ['LABEL_CREATED', 'PREPARING']:
                        title = "Shipment Prepared"
                        msg = f"Shipping details created for your package{tracking_str}."
                    else:
                        status_display = status_upper.replace('_', ' ').title() if status_upper else 'Updated'
                        title = f"Shipment Update"
                        msg = f"Your package{tracking_str} status is now {status_display}."

                    if customer_id:
                        send_kafka_notification(
                            user_id=customer_id,
                            title=title,
                            message=msg,
                            notif_type="SHIPMENT",
                            metadata={
                                'shipment_id': payload.get('shipment_id'),
                                'order_id': payload.get('order_id'),
                                'tracking_code': tracking_code,
                                'status': new_status,
                                'carrier': carrier,
                                'location': payload.get('location') or payload.get('current_location', ''),
                                'estimated_delivery': payload.get('estimated_delivery') or payload.get('estimated_delivery_date', ''),
                                'notes': payload.get('notes', msg),
                                'timestamp': datetime.now(timezone.utc).isoformat(),
                            }
                        )

            except Exception as msg_err:
                print(f"[Order Kafka Consumer] Error processing message: {msg_err}")

