web: python manage.py collectstatic --no-input && python manage.py migrate && daphne -b 0.0.0.0 -p $PORT locallibrary.asgi:application
