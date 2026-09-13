#!/bin/bash
set -e

echo "[Media Service] Running database migrations..."
python manage.py makemigrations media
python manage.py migrate --noinput

echo "[Media Service] Starting Gunicorn REST server on port 8000..."
exec gunicorn media_project.wsgi:application --bind 0.0.0.0:8000 --workers 2
