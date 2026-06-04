# SkillMap Nepal - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Docker (Recommended)

1. **Prerequisites**
   - Docker and Docker Compose installed
   - 4GB RAM available

2. **Setup**
```bash
# Clone repository
git clone <repository-url>
cd SkillMapNepal

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your favorite editor

# Build and start
docker-compose up --build
```

3. **Initialize Database**
```bash
# In a new terminal
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py setup_site
```

4. **Access Application**
   - Web: http://localhost
   - Admin: http://localhost/admin

### Option 2: Local Development

1. **Prerequisites**
   - Python 3.11+
   - PostgreSQL 16 with pgvector
   - Redis

2. **Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_md
playwright install chromium

# Setup database
createdb skillmap_db
psql skillmap_db -c "CREATE EXTENSION vector;"

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run migrations
python manage.py migrate
python manage.py createsuperuser
python manage.py setup_site
```

3. **Run Services** (4 terminals needed)
```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A skillmap worker --loglevel=info

# Terminal 3: Celery Beat
celery -A skillmap beat --loglevel=info

# Terminal 4: Redis (if not installed as service)
redis-server
```

## 🔑 Required API Keys

### Cloudinary (File Storage)
1. Sign up at https://cloudinary.com
2. Get your credentials from Dashboard
3. Add to `.env`:
```
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### Anthropic Claude API
1. Sign up at https://console.anthropic.com
2. Create an API key
3. Add to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

## 📝 First Steps

1. **Create Account**
   - Visit http://localhost
   - Click "Sign Up"
   - Fill registration form

2. **Upload CV**
   - Login to dashboard
   - Click "Upload CV"
   - Choose PDF or DOCX file
   - Wait for analysis (2-3 minutes)

3. **View Results**
   - Readiness score
   - Skill gaps
   - Learning roadmap

4. **Run Scraper** (Optional)
```bash
python manage.py scrape_jobs
```

## 🐛 Troubleshooting

### "psycopg2.OperationalError: could not connect to server"
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env

### "ModuleNotFoundError: No module named 'en_core_web_md'"
```bash
python -m spacy download en_core_web_md
```

### "Celery tasks not running"
- Check Redis is running: `redis-cli ping`
- Check Celery worker logs

### "Cloudinary upload failed"
- Verify Cloudinary credentials
- Check internet connection

## 📚 Next Steps

- Read full [README.md](README.md)
- Explore Django admin at `/admin`
- Check Celery task logs
- Customize skill mappings in `parser/utils.py`

## 🆘 Need Help?

- Check logs: `docker-compose logs -f`
- View Celery tasks: Django admin > Celery Results
- Debug mode: Set `DEBUG=True` in .env
