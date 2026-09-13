import json
import time
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from recommendations.graph_sync import sync_event_to_graph

try:
    from kafka import KafkaConsumer
except ImportError:
    from kafka_ng import KafkaConsumer

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Consumes events from Kafka topic 'ecommerce-events' and updates recommendation graph DB."

    def handle(self, *args, **options):
        bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
        self.stdout.write(f"[Kafka Consumer] Connecting to {bootstrap_servers}...")

        consumer = None
        while not consumer:
            try:
                consumer = KafkaConsumer(
                    'ecommerce-events',
                    bootstrap_servers=bootstrap_servers,
                    group_id='recommendation_service_group',
                    auto_offset_reset='earliest',
                    enable_auto_commit=True,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
                )
                self.stdout.write(self.style.SUCCESS("[Kafka Consumer] Connected successfully!"))
            except Exception as e:
                logger.warning(f"[Kafka Consumer] Connection failed: {e}. Retrying in 5 seconds...")
                time.sleep(5)

        for message in consumer:
            try:
                data = message.value
                event_type = data.get('event_type')
                event_id = data.get('event_id')
                payload = data.get('payload', {})

                self.stdout.write(f"[Kafka Consumer] Received event: {event_type} (id: {event_id})")

                if event_type:
                    success = sync_event_to_graph(event_type=event_type, payload=payload, event_id=event_id)
                    if success:
                        self.stdout.write(self.style.SUCCESS(f"Processed event {event_type} successfully."))
                    else:
                        self.stdout.write(self.style.WARNING(f"Event {event_type} skipped or ignored."))

            except Exception as err:
                logger.error(f"[Kafka Consumer] Error processing message: {err}")
                self.stdout.write(self.style.ERROR(f"Error processing message: {err}"))
