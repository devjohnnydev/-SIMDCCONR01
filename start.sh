#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# Makemigrations should be run locally and committed to Git
# python manage.py makemigrations --noinput

echo "Running migrate..."
python manage.py migrate --noinput || python manage.py migrate --fake reports 0003

echo "Running fix_db..."
python fix_db.py

echo "Running setup_initial_data..."
python manage.py setup_initial_data

echo "Starting Gunicorn..."
exec gunicorn saas_nr01.wsgi:application --bind 0.0.0.0:$PORT
