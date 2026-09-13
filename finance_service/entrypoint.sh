#!/bin/sh

set -e

echo "Waiting for postgres..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

python manage.py makemigrations
python manage.py migrate

if [ "$SERVICE_TYPE" = "kafka_consumer" ]; then
    exec python finance/kafka_consumer.py
else
    exec gunicorn finance_project.wsgi:application --bind 0.0.0.0:8000
fi
