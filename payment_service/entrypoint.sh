#!/bin/bash
set -e

echo "[Payment Service] Running database migrations..."
python manage.py makemigrations payments
python manage.py migrate --noinput

if [ "$SERVICE_TYPE" = "kafka_consumer" ]; then
    echo "[Payment Service] Starting Kafka Event Consumer..."
    exec python payments/kafka_consumer.py
else
    echo "[Payment Service] Starting gRPC server on port 50055..."
    python manage.py run_grpc &

    echo "[Payment Service] Starting Gunicorn server on port 8000..."
    exec gunicorn payment_project.wsgi:application --bind 0.0.0.0:8000 --workers 2
fi

