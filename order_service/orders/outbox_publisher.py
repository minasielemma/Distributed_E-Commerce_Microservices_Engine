import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "order_project.settings")
django.setup()

from django.db import transaction
from orders.models import OutboxEvent

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
except ImportError:
    from kafka_ng import KafkaProducer
    from kafka_ng.errors import KafkaError

logger = logging.getLogger("outbox_publisher")
logging.basicConfig(level=logging.INFO)


def create_producer():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        acks='all',
        retries=5,
        max_in_flight_requests_per_connection=1,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        request_timeout_ms=10000,
    )


def publish_pending_events():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    topic = os.getenv("KAFKA_TOPIC", "ecommerce-events")

    producer = None
    try:
        producer = create_producer()
    except Exception as e:
        logger.error(f"[Outbox Publisher] Failed to connect to Kafka broker at {bootstrap_servers}: {e}")
        return

    pending_events = OutboxEvent.objects.filter(status='PENDING').order_by('created_at')[:50]
    if not pending_events.exists():
        return

    for ev in pending_events:
        event_msg = {
            'event_id': str(ev.id),
            'event_type': ev.event_type,
            'payload': ev.payload,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        try:
            future = producer.send(topic, value=event_msg)
            record_metadata = future.get(timeout=10)
            
            with transaction.atomic():
                ev.status = 'PROCESSED'
                ev.processed_at = datetime.now(timezone.utc)
                ev.save(update_fields=['status', 'processed_at'])

            logger.info(
                f"[Outbox Publisher] Published event {ev.id} ({ev.event_type}) to "
                f"topic={record_metadata.topic} partition={record_metadata.partition} offset={record_metadata.offset}"
            )
        except KafkaError as k_err:
            logger.error(f"[Outbox Publisher] Kafka error publishing event {ev.id}: {k_err}")
        except Exception as err:
            logger.error(f"[Outbox Publisher] Unexpected error publishing event {ev.id}: {err}")

    try:
        producer.flush()
        producer.close()
    except Exception:
        pass


def run_loop(poll_interval=3):
    logger.info("[Outbox Publisher] Starting Outbox Publisher loop...")
    while True:
        try:
            publish_pending_events()
        except Exception as loop_err:
            logger.error(f"[Outbox Publisher] Error in loop iteration: {loop_err}")
        time.sleep(poll_interval)


if __name__ == "__main__":
    run_loop()
