#!/bin/bash
cd diploma_pj
python manage.py makemigrations
python manage.py migrate
python manage.py create_superuser --email='admin@example.com' --password='admin'
python manage.py runserver 0.0.0.0:8000
