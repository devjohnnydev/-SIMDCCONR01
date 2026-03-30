web: gunicorn saas_nr01.wsgi:application --bind 0.0.0.0:$PORT
release: python manage.py migrate --noinput && python manage.py setup_initial_data
