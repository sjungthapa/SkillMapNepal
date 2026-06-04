# Deployment Checklist for SkillMap Nepal

## Pre-Deployment

### 1. Environment Configuration
- [ ] Set `DEBUG=False` in production
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` with actual domain
- [ ] Set up production database (PostgreSQL with pgvector)
- [ ] Configure Redis instance
- [ ] Obtain Cloudinary credentials
- [ ] Obtain Anthropic API key
- [ ] Set up SSL certificates

### 2. Database Setup
```sql
-- Create production database
CREATE DATABASE skillmap_prod;
CREATE USER skillmap_prod WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE skillmap_prod TO skillmap_prod;

-- Enable pgvector extension
\c skillmap_prod
CREATE EXTENSION vector;
```

### 3. Security Hardening
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS only
- [ ] Configure CORS if needed
- [ ] Set secure cookie flags
- [ ] Implement rate limiting
- [ ] Set up firewall rules
- [ ] Enable database backups

### 4. Static Files & Media
- [ ] Run `python manage.py collectstatic`
- [ ] Configure Cloudinary properly
- [ ] Set up CDN for static files (optional)
- [ ] Configure proper file permissions

### 5. Monitoring & Logging
- [ ] Set up error tracking (Sentry recommended)
- [ ] Configure log aggregation
- [ ] Set up uptime monitoring
- [ ] Configure Celery Flower for task monitoring
- [ ] Set up database monitoring
- [ ] Configure alerts

## Deployment Options

### Option 1: Docker Deployment (AWS ECS, Azure Container, etc.)

1. **Build and Push Image**
```bash
docker build -t skillmap-nepal:latest .
docker tag skillmap-nepal:latest your-registry/skillmap-nepal:latest
docker push your-registry/skillmap-nepal:latest
```

2. **Deploy Stack**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. **Run Migrations**
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py setup_site
docker-compose exec web python manage.py createsuperuser
```

### Option 2: Traditional Server (Ubuntu 22.04)

1. **Install Dependencies**
```bash
sudo apt update
sudo apt install python3.11 python3-pip postgresql-16 redis nginx
```

2. **Setup Application**
```bash
git clone <repository>
cd SkillMapNepal
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_md
playwright install chromium
```

3. **Configure Systemd Services**

**Django (gunicorn.service)**
```ini
[Unit]
Description=SkillMap Nepal Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/skillmap
Environment="PATH=/var/www/skillmap/venv/bin"
ExecStart=/var/www/skillmap/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:8000 skillmap.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Celery Worker (celery-worker.service)**
```ini
[Unit]
Description=SkillMap Celery Worker
After=network.target redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/skillmap
Environment="PATH=/var/www/skillmap/venv/bin"
ExecStart=/var/www/skillmap/venv/bin/celery -A skillmap worker --loglevel=info

[Install]
WantedBy=multi-user.target
```

**Celery Beat (celery-beat.service)**
```ini
[Unit]
Description=SkillMap Celery Beat
After=network.target redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/skillmap
Environment="PATH=/var/www/skillmap/venv/bin"
ExecStart=/var/www/skillmap/venv/bin/celery -A skillmap beat --loglevel=info

[Install]
WantedBy=multi-user.target
```

4. **Nginx Configuration**
```nginx
server {
    listen 80;
    server_name skillmap.np www.skillmap.np;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name skillmap.np www.skillmap.np;

    ssl_certificate /etc/letsencrypt/live/skillmap.np/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/skillmap.np/privkey.pem;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/skillmap/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

5. **Start Services**
```bash
sudo systemctl enable gunicorn celery-worker celery-beat nginx
sudo systemctl start gunicorn celery-worker celery-beat nginx
```

### Option 3: Platform as a Service (Heroku, Railway, etc.)

1. **Add Procfile**
```
web: gunicorn skillmap.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A skillmap worker --loglevel=info
beat: celery -A skillmap beat --loglevel=info
```

2. **Add runtime.txt**
```
python-3.11.8
```

3. **Configure Buildpacks**
- Python
- Playwright (custom buildpack)

4. **Add Required Add-ons**
- PostgreSQL (with pgvector support)
- Redis
- Scheduler (for beat)

## Post-Deployment

### 1. Verify Installation
- [ ] Check web interface loads
- [ ] Test user registration
- [ ] Test CV upload
- [ ] Verify Celery tasks run
- [ ] Test job scraping
- [ ] Check admin panel
- [ ] Verify static files load
- [ ] Test all features end-to-end

### 2. Initial Data Setup
```bash
# Run scrapers to populate job data
python manage.py scrape_jobs

# Verify in admin
# Check ScrapeJob records
```

### 3. Performance Optimization
- [ ] Enable pgvector indexes for large datasets
```sql
CREATE INDEX ON extracted_skills USING ivfflat (skill_vector vector_cosine_ops);
CREATE INDEX ON job_skills USING ivfflat (skill_vector vector_cosine_ops);
```
- [ ] Configure database connection pooling
- [ ] Set up Redis caching
- [ ] Enable Gzip compression
- [ ] Optimize Celery concurrency

### 4. Backup Strategy
- [ ] Database backups (daily)
- [ ] Media files backup (Cloudinary handles this)
- [ ] Application code backup (Git)
- [ ] Configuration backup

### 5. Monitoring Setup
- [ ] Application logs
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring (New Relic/DataDog)
- [ ] Uptime monitoring (UptimeRobot)
- [ ] Celery monitoring (Flower)

## Production Settings

**settings.py additions for production:**
```python
# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/skillmap/django.log',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'sentry_sdk.integrations.logging.EventHandler',
        },
    },
    'root': {
        'handlers': ['file', 'sentry'],
        'level': 'INFO',
    },
}
```

## Scaling Considerations

### Horizontal Scaling
- [ ] Multiple Gunicorn workers
- [ ] Multiple Celery workers
- [ ] PostgreSQL read replicas
- [ ] Redis cluster
- [ ] Load balancer (Nginx/HAProxy)

### Database Optimization
- [ ] Connection pooling (pgBouncer)
- [ ] Query optimization
- [ ] Proper indexing
- [ ] Regular VACUUM

### Caching Strategy
- [ ] Redis cache for queries
- [ ] Template fragment caching
- [ ] API response caching
- [ ] CDN for static assets

## Maintenance

### Regular Tasks
- [ ] Weekly database backups verification
- [ ] Monthly dependency updates
- [ ] Quarterly security audits
- [ ] Monitor disk usage
- [ ] Review error logs
- [ ] Update spaCy models as needed
- [ ] Review and optimize Celery tasks

### Updating Application
```bash
# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart gunicorn celery-worker celery-beat
```

## Troubleshooting

### Common Issues

1. **Tasks not executing**
   - Check Celery worker is running
   - Verify Redis connection
   - Check Celery logs

2. **CV parsing fails**
   - Verify Cloudinary credentials
   - Check spaCy model installed
   - Review parser logs

3. **Scraping fails**
   - Check Playwright installation
   - Verify network connectivity
   - Job sites may have changed structure

4. **High memory usage**
   - Reduce Celery concurrency
   - Optimize database queries
   - Check for memory leaks

5. **Slow response times**
   - Enable database query optimization
   - Add Redis caching
   - Use CDN for static files
   - Scale workers horizontally

## Support

- Check logs in `/var/log/skillmap/`
- Review Celery task logs
- Monitor Sentry for errors
- Check system resources (CPU, RAM, disk)
