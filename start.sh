#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

echo "Running makemigrations..."
python manage.py makemigrations --noinput

echo "Running migrate..."
python manage.py migrate --noinput

echo "Running fix_db..."
python fix_db.py

echo "Running setup_initial_data..."
python manage.py setup_initial_data

echo "Starting Gunicorn..."
exec gunicorn saas_nr01.wsgi:application --bind 0.0.0.0:$PORT
