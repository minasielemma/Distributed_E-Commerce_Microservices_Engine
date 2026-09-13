#!/bin/bash
set -e

echo "[Catalog Service] Running database migrations..."
python manage.py makemigrations catalog
python manage.py migrate --noinput

echo "[Catalog Service] Starting gRPC server in background on port 50051..."
python manage.py run_grpc &

if [ "$1" != "" ]; then
    exec "$@"
fi

echo "[Catalog Service] Starting Gunicorn REST server on port 8000..."
exec gunicorn catalog_project.wsgi:application --bind 0.0.0.0:8000 --workers 2
