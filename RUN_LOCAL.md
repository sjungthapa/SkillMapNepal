# Quick Local Run (Without Docker)

This guide helps you run SkillMap Nepal locally for testing without Docker or external services.

## Quick Start (5 Minutes)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Download spaCy Model

```bash
python -m spacy download en_core_web_md
```

### Step 3: Setup Local Database (SQLite)

Update `.env` to use SQLite:
```
DATABASE_URL=sqlite:///db.sqlite3
```

### Step 4: Run Migrations

```bash
python manage.py migrate
python manage.py createsuperuser
```

### Step 5: Create Sample Data (Optional)

```bash
python manage.py shell
```

```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
site.domain = 'localhost:8000'
site.name = 'SkillMap Nepal'
site.save()
exit()
```

### Step 6: Run Development Server

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2 (Optional): Redis
# If you have Redis installed
redis-server

# Terminal 3 (Optional): Celery
# Only if you want async tasks
celery -A skillmap worker --loglevel=info -P solo
```

### Step 7: Access Application

Open browser: http://localhost:8000

## Testing Without External APIs

### Mock Mode (No API Keys Required)

The app will use fallback roadmaps if Gemini API is not configured:

```python
# roadmap/tasks.py already has fallback logic
# It generates template-based roadmaps if API fails
```

### What Works Without APIs:

✅ User registration/login
✅ Dashboard views
✅ Database operations
✅ Admin panel

❌ CV upload (needs Cloudinary)
❌ AI roadmap generation (needs Gemini)
❌ Job scraping (needs Playwright setup)

## Full Setup with APIs

### 1. Get Gemini API Key (FREE)

Visit: https://makersuite.google.com/app/apikey

Update `.env`:
```
GEMINI_API_KEY=AIzaSy...your-key
```

### 2. Get Cloudinary Account (FREE)

Visit: https://cloudinary.com/users/register/free

Update `.env`:
```
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### 3. Install Playwright (For Scraping)

```bash
pip install playwright
playwright install chromium
```

## Troubleshooting

### Error: "No module named X"
```bash
pip install -r requirements.txt
```

### Error: "Can't find spaCy model"
```bash
python -m spacy download en_core_web_md
```

### Error: "Redis connection refused"
- Skip Redis for now (Celery tasks won't run but web app works)
- Or install Redis: https://redis.io/download

### Port 8000 already in use
```bash
python manage.py runserver 8080
```

## Next Steps

Once running locally:
1. Create a user account
2. Explore the admin panel at /admin
3. Test the dashboard
4. Add API keys for full functionality
5. Or proceed to Docker deployment

## Production Deployment

For production, use Docker:
```bash
docker-compose up --build
```

See DEPLOYMENT.md for details.
