from django.core.management.base import BaseCommand
from notifications.kafka_consumer import start_kafka_consumer

class Command(BaseCommand):
    help = 'Runs the Kafka Consumer loop for Notification Service'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Notification Service Kafka Consumer...'))
        start_kafka_consumer()
