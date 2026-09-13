import json
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

def publish_notification_event(event_type, payload, topic="notifications"):
    """
    Publishes a notification event to Kafka.
    Payload expected format:
      - user_id / recipient_ids
      - title
      - message
      - notification_type (ORDER, PAYMENT, SYSTEM, etc.)
      - metadata (dict)
    """
    bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'))
    
    try:
        try:
            from kafka import KafkaProducer
        except ImportError:
            from kafka_ng import KafkaProducer

        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            request_timeout_ms=5000,
            retries=3
        )
        
        event_data = {
            'event_type': event_type,
            'payload': payload
        }
        
        producer.send(topic, event_data)
        producer.flush()
        producer.close()
        logger.info(f"Published Kafka event '{event_type}' to topic '{topic}'")
        return True
    except Exception as e:
        logger.error(f"Failed to publish Kafka event to topic '{topic}': {e}")
        return False
