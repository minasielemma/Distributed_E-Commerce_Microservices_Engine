#!/bin/bash
set -e

echo "[Identity Service] Generating RSA keys and gRPC mTLS certs if absent..."
python generate_keys.py

echo "[Identity Service] Running database migrations..."
python manage.py makemigrations authentication
python manage.py migrate --noinput

echo "[Identity Service] Creating default superuser if absent..."
python manage.py create_default_admin

echo "[Identity Service] Starting Gunicorn server..."
exec gunicorn identity_project.wsgi:application --bind 0.0.0.0:8000 --workers 2
