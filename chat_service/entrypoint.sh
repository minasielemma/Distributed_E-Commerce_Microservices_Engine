#!/bin/bash
set -e

echo "[Chat Service] Running database migrations..."
python manage.py makemigrations chat
python manage.py migrate --noinput

echo "[Chat Service] Starting Daphne ASGI server on port 8000..."
exec daphne -b 0.0.0.0 -p 8000 chat_project.asgi:application
