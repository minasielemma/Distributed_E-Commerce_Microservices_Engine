import json
import logging
import os
import time
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from notifications.models import Notification

logger = logging.getLogger(__name__)


def process_notification_message(message_data):
    """
    Process raw event dictionary consumed from Kafka.
    Expected schema:
      {
        "event_type": "notification.send" | "order.shipped" | ...,
        "payload": {
          "user_id": 123,
          "recipient_ids": [123, 456],
          "tenant_id": "tenant-uuid",
          "broadcast": false,
          "title": "...",
          "message": "...",
          "notification_type": "ORDER",
          "metadata": {...}
        }
      }
    """
    try:
        event_type = message_data.get('event_type')
        payload = message_data.get('payload', {})
        if not payload and isinstance(message_data, dict):
            # Fallback if message_data itself is payload
            payload = message_data

        title = payload.get('title') or f"Event: {event_type}"
        message = payload.get('message', '')
        notification_type = payload.get('notification_type') or 'SYSTEM'
        metadata = payload.get('metadata', {})
        tenant_id = payload.get('tenant_id')
        is_broadcast = payload.get('broadcast', False)

        recipients = set()
        if payload.get('user_id'):
            recipients.add(str(payload['user_id']))
        if payload.get('customer_id'):
            recipients.add(str(payload['customer_id']))
        if payload.get('user'):
            recipients.add(str(payload['user']))
        if payload.get('recipient_id'):
            recipients.add(str(payload['recipient_id']))
        if payload.get('recipient_ids') and isinstance(payload['recipient_ids'], list):
            for rid in payload['recipient_ids']:
                recipients.add(str(rid))
        if payload.get('user_ids') and isinstance(payload['user_ids'], list):
            for uid in payload['user_ids']:
                recipients.add(str(uid))

        # Handle specific domain events to generate plain English non-technical text
        if event_type in ['shipment.created', 'shipment.status_changed']:
            notification_type = "SHIPMENT"
            status = str(payload.get('new_status') or payload.get('status') or metadata.get('status') or '').upper()
            tracking_code = payload.get('tracking_code') or metadata.get('tracking_code', '')
            carrier = payload.get('carrier') or metadata.get('carrier', 'Standard Carrier')
            tracking_str = f" ({tracking_code})" if tracking_code else ""

            if status == 'SHIPPED':
                title = "Package Shipped"
                message = f"Your package{tracking_str} via {carrier} has been shipped."
            elif status == 'IN_TRANSIT':
                title = "Package In Transit"
                message = f"Your package{tracking_str} is currently in transit."
            elif status == 'OUT_FOR_DELIVERY':
                title = "Out for Delivery"
                message = f"Your package{tracking_str} is out for delivery today!"
            elif status == 'DELIVERED':
                title = "Package Delivered"
                message = f"Your package{tracking_str} has been delivered successfully."
            elif status in ['LABEL_CREATED', 'PREPARING']:
                title = "Shipment Prepared"
                message = f"Shipping details created for your package{tracking_str}."
            else:
                title = "Shipment Update"
                status_display = status.replace('_', ' ').title() if status else 'Updated'
                message = f"Your package{tracking_str} status is now {status_display}."
        elif event_type == 'payment.succeeded':
            title = "Payment Confirmed"
            order_id = str(payload.get('order_id', ''))
            message = f"Your payment for order #{order_id[:8]} was successful."
            notification_type = "PAYMENT"
        elif event_type in ['order.created', 'order.paid']:
            order_id = str(payload.get('order_id', ''))
            title = "Order Paid" if event_type == 'order.paid' else "Order Placed"
            message = f"Order #{order_id[:8]} has been updated to paid." if event_type == 'order.paid' else f"Your order #{order_id[:8]} has been placed."
            notification_type = "ORDER"

        # Sanitize any remaining raw event title strings
        if title.startswith("Event:") or "event" in title.lower():
            title = title.replace("Event:", "").replace("_", " ").strip().title()

        channel_layer = get_channel_layer()
        created_notifs = []

        if recipients:
            for uid in recipients:
                notif = Notification.objects.create(
                    user_id=uid,
                    tenant_id=tenant_id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    metadata=metadata
                )
                created_notifs.append(notif)

                # Push to user's real-time WebSocket channel
                if channel_layer:
                    group_name = f"notifications_{uid}"
                    ws_payload = {
                        'id': str(notif.id),
                        'user_id': uid,
                        'tenant_id': tenant_id,
                        'title': notif.title,
                        'message': notif.message,
                        'notification_type': notif.notification_type,
                        'is_read': notif.is_read,
                        'metadata': notif.metadata,
                        'created_at': notif.created_at.isoformat(),
                    }
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {
                            'type': 'notification_message',
                            'data': ws_payload
                        }
                    )

        elif tenant_id:
            # Push to tenant group
            if channel_layer:
                ws_payload = {
                    'title': title,
                    'message': message,
                    'notification_type': notification_type,
                    'metadata': metadata,
                    'tenant_id': tenant_id,
                }
                async_to_sync(channel_layer.group_send)(
                    f"notifications_tenant_{tenant_id}",
                    {
                        'type': 'notification_message',
                        'data': ws_payload
                    }
                )

        logger.info(f"Successfully processed notification event '{event_type}' for {len(recipients)} recipients.")
        return created_notifs
    except Exception as e:
        logger.error(f"Error processing notification message: {e}", exc_info=True)
        return []


def start_kafka_consumer():
    """Run blocking Kafka consumer loop."""
    bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'))
    topics = ['notifications', 'ecommerce-events']

    try:
        try:
            from kafka import KafkaConsumer
        except ImportError:
            from kafka_ng import KafkaConsumer

        logger.info(f"Connecting Notification Kafka Consumer to {bootstrap_servers} on topics {topics}...")

        consumer = None
        while not consumer:
            try:
                consumer = KafkaConsumer(
                    *topics,
                    bootstrap_servers=bootstrap_servers,
                    group_id='notification_service_group',
                    auto_offset_reset='latest',
                    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
                )
            except Exception as conn_err:
                logger.warning(f"Kafka connection pending ({conn_err}). Retrying in 5 seconds...")
                time.sleep(5)

        logger.info(f"Notification Kafka Consumer successfully connected and listening on topics {topics}.")

        for msg in consumer:
            try:
                data = msg.value
                logger.info(f"Kafka message received on topic '{msg.topic}' offset {msg.offset}: {data}")
                process_notification_message(data)
            except Exception as e:
                logger.error(f"Error handling Kafka message on offset {msg.offset}: {e}")

    except Exception as e:
        logger.critical(f"Kafka Consumer crashed: {e}")
