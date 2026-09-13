#!/bin/bash
set -e

echo "[Inventory Service] Running database migrations..."
python manage.py makemigrations inventory
python manage.py migrate --noinput

echo "[Inventory Service] Starting Gunicorn server on port 8000..."
exec gunicorn inventory_project.wsgi:application --bind 0.0.0.0:8000 --workers 2
