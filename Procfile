web: gunicorn skillmap.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
worker: celery -A skillmap worker -l info
beat: celery -A skillmap beat -l info
