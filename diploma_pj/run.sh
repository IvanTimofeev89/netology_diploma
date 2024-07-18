#!/bin/bash
set -e
wait-for-it postgres_db:5432 -t 30
python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate
python manage.py create_superuser
gunicorn diploma_pj.wsgi:application --bind 0.0.0.0:8000
