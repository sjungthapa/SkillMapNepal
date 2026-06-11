FROM python:3.12-slim

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install spaCy model
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.7.1/en_core_web_md-3.7.1-py3-none-any.whl

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media

# Collect static files
RUN python manage.py collectstatic --noinput || true

EXPOSE $PORT

CMD python manage.py migrate && python manage.py shell -c "from django.contrib.sites.models import Site; Site.objects.update_or_create(id=1, defaults={'domain': 'skillmapnepal.onrender.com', 'name': 'SkillMap Nepal'})" && gunicorn skillmap.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120

RUN echo "Scraper will run via Celery beat in production"

CMD python manage.py migrate && python manage.py scrape_jobs && gunicorn skillmap.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120