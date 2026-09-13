#!/bin/bash
set -e

echo "[Recommendation Service] Running database migrations..."
python manage.py makemigrations recommendations
python manage.py migrate --noinput

if [ "$SERVICE_TYPE" = "celery_worker" ]; then
    echo "[Recommendation Service] Starting Celery Worker..."
    exec celery -A recommendation_project worker -l info
elif [ "$SERVICE_TYPE" = "celery_beat" ]; then
    echo "[Recommendation Service] Starting Celery Beat..."
    exec celery -A recommendation_project beat -l info
elif [ "$SERVICE_TYPE" = "kafka_consumer" ]; then
    echo "[Recommendation Service] Starting Kafka Event Consumer..."
    exec python manage.py consume_recommendation_events
else
    echo "[Recommendation Service] Starting Daphne ASGI server on port 8000..."
    exec daphne -b 0.0.0.0 -p 8000 recommendation_project.asgi:application
fi
