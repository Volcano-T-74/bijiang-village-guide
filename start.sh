#!/usr/bin/env bash
set -o errexit

python manage.py migrate --noinput
python manage.py import_local_voices
python manage.py seed_demo_data
if [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" && -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]]; then
  python manage.py ensure_admin
fi
gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
