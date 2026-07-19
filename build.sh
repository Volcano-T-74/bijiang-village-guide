#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
pip install -r requirements.txt

npm install --prefix frontend
npm run build --prefix frontend

python manage.py collectstatic --noinput
