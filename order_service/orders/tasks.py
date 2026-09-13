import json
import logging
from datetime import datetime
from celery import shared_task
from django.db import transaction
from django.conf import settings
from .models import OutboxEvent

try:
    from kafka import KafkaProducer
except ImportError:
    from kafka_ng import KafkaProducer

logger = logging.getLogger(__name__)

@shared_task
def process_outbox_events():
    pending_events = OutboxEvent.objects.filter(status='PENDING').order_by('created_at')[:20]

    if not pending_events.exists():
        return "No pending outbox events."

    producer = None
    try:
        producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            request_timeout_ms=5000
        )
    except Exception as e:
        logger.error(f"Failed to initialize KafkaProducer: {e}")

    processed_count = 0
    for event in pending_events:
        with transaction.atomic():
            ev = OutboxEvent.objects.select_for_update().get(id=event.id)
            if ev.status != 'PENDING':
                continue

            event_payload = {
                "event_id": str(ev.id),
                "event_type": ev.event_type,
                "payload": ev.payload,
                "created_at": ev.created_at.isoformat()
            }

            if producer:
                try:
                    producer.send('ecommerce-events', value=event_payload)
                    producer.flush()
                    ev.status = 'PROCESSED'
                    ev.processed_at = datetime.utcnow()
                    ev.save()
                    processed_count += 1
                except Exception as pub_err:
                    logger.error(f"Failed to publish outbox event {ev.id}: {pub_err}")
            else:
                ev.status = 'PROCESSED'
                ev.processed_at = datetime.utcnow()
                ev.save()
                processed_count += 1

    return f"Processed {processed_count} outbox events."
