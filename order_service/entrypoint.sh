#!/bin/bash
set -e

echo "[Order Service] Running database migrations..."
python manage.py makemigrations orders
python manage.py migrate --noinput

if [ "$SERVICE_TYPE" = "celery_worker" ]; then
    echo "[Order Service] Starting Celery Worker..."
    exec celery -A order_project worker -l info --concurrency=2
elif [ "$SERVICE_TYPE" = "celery_beat" ]; then
    echo "[Order Service] Starting Celery Beat..."
    exec celery -A order_project beat -l info -s /tmp/celerybeat-schedule
elif [ "$SERVICE_TYPE" = "kafka_consumer" ]; then
    echo "[Order Service] Starting Kafka Event Consumer..."
    exec python manage.py consume_kafka_events
else
    echo "[Order Service] Starting gRPC server on port 50054..."
    python manage.py run_grpc &

    echo "[Order Service] Starting Daphne ASGI server on port 8000..."
    exec daphne -b 0.0.0.0 -p 8000 order_project.asgi:application
fi
