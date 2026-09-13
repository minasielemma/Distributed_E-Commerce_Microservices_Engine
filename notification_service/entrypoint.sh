#!/bin/sh

echo "Waiting for postgres..."
while ! nc -z ${POSTGRES_HOST:-notification_db} ${POSTGRES_PORT:-5432}; do
  sleep 0.5
done
echo "PostgreSQL started"

echo "Waiting for redis..."
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
  sleep 0.5
done
echo "Redis started"

python manage.py makemigrations notifications --noinput
python manage.py migrate --noinput

if [ "$SERVICE_TYPE" = "kafka_consumer" ]; then
    echo "Starting Notification Kafka Consumer Worker..."
    exec python manage.py run_kafka_consumer
else
    echo "Starting Daphne ASGI Web & WebSocket Server..."
    exec daphne -b 0.0.0.0 -p 8000 notification_project.asgi:application
fi
