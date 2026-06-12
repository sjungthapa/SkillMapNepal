FROM python:3.12-slim

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MALLOC_ARENA_MAX=2

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

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media

# Collect static files
RUN python manage.py collectstatic --noinput || true

EXPOSE $PORT

# Run migrations then start gunicorn with 1 worker to fit in 512MB free tier RAM
CMD python manage.py migrate && \
    python manage.py shell -c "from django.contrib.sites.models import Site; Site.objects.update_or_create(id=1, defaults={'domain': 'skillmapnepal.onrender.com', 'name': 'SkillMap Nepal'})" && \
    gunicorn skillmap.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 300 --preload