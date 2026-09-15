#!/bin/sh

set -e

echo "Waiting for postgres..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

python manage.py makemigrations
python manage.py migrate

echo "[Cart Service] Starting gRPC server on port 50057..."
python manage.py run_grpc &

exec gunicorn cart_project.wsgi:application --bind 0.0.0.0:8000
