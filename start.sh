#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# Makemigrations should be run locally and committed to Git
python manage.py makemigrations companies --noinput

echo "Checking for existing DB columns (Faking old migrations)..."
# Consolidate fake migrations into fewer calls if possible
python manage.py migrate --fake reports 0003 --noinput || true
python manage.py migrate --fake accounts 0003 --noinput || true
python manage.py migrate --fake reports 0004 --noinput || true
python manage.py migrate --fake accounts 0004 --noinput || true
python manage.py migrate --fake accounts 0005 --noinput || true
python manage.py migrate --fake reports 0005 --noinput || true
python manage.py migrate --fake reports 0006 --noinput || true
python manage.py migrate --fake reports 0007 --noinput || true

echo "Running migrate..."
python manage.py migrate --noinput

echo "Running fix_db..."
python fix_db.py

# echo "Running setup_initial_data..."
# python manage.py setup_initial_data

# echo "Running fix_missing_options..."
# python fix_missing_options.py

echo "Ensuring media directory exists..."
mkdir -p media

echo "Running collectstatic..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn saas_nr01.wsgi:application --bind 0.0.0.0:$PORT
