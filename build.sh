#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
pip install -r requirements.txt

corepack pnpm --dir frontend install --frozen-lockfile
corepack pnpm --dir frontend build

python manage.py collectstatic --noinput
