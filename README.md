# SkillMap Nepal 🗺️

An AI-powered job skill gap analyzer that helps Nepali tech job seekers identify missing skills and get personalized learning roadmaps.

**✨ Now using Google Gemini API - FREE tier available!**

## 🎯 Overview

SkillMap Nepal analyzes your CV against real job market demands from major Nepali job sites (Merojob.com, Kumarijob.com) and provides:
- Detailed skill gap analysis
- Market readiness score (0-100%)
- AI-generated personalized learning roadmap (powered by **Google Gemini - FREE!** 🎉)
- Week-by-week learning plan with curated resources

## 🏗️ Architecture

### Technology Stack
- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL 16 with pgvector extension
- **Task Queue**: Celery + Redis
- **Web Scraping**: Playwright (async)
- **CV Parsing**: pdfplumber + python-docx + spaCy
- **NLP/ML**: sentence-transformers (all-MiniLM-L6-v2, 384 dimensions)
- **AI**: Google Gemini API (gemini-2.0-flash) — FREE tier
- **Storage**: Cloudinary (CV files)
- **Frontend**: Django Templates + Tailwind CSS + Chart.js
- **Deployment**: Docker + Gunicorn + Nginx

### System Flow
```
1. User uploads CV (PDF/DOCX)
2. Celery task: Parse CV → Extract skills → Vectorize with sentence-transformers
3. Celery task: Analyze skill gaps using pgvector cosine similarity
4. Celery task: Generate roadmap using Google Gemini API
5. User views dashboard with charts and personalized roadmap
```

### Django Apps

#### `users/`
- Custom User model with UUID primary key
- Email-based authentication
- Profile management

#### `parser/`
- CV upload handling
- PDF/DOCX text extraction
- spaCy NER for skill extraction
- Skill normalization
- Vectorization using sentence-transformers

#### `scraper/`
- Playwright-based scrapers for Merojob and Kumarijob
- Job posting extraction
- Skill identification from job descriptions
- Runs via Celery beat (every 24 hours)
- Deduplication by source_url

#### `analysis/`
- pgvector cosine similarity computation
- Skill gap identification
- Readiness score calculation
- Job matching algorithm

#### `roadmap/`
- **Google Gemini API integration (FREE tier!)**
- JSON-structured roadmap generation
- Resource curation
- Week-by-week learning plans

#### `dashboard/`
- Dashboard views
- Chart.js visualizations
- AJAX status polling
- Report history

## 📊 Database Models

### USER (users.User)
- `id`: UUID PK
- `full_name`, `email`, `phone`
- `created_at`

### CV_UPLOAD (parser.CVUpload)
- `id`: UUID PK
- `user`: FK to User
- `file_url`: Cloudinary URL
- `original_filename`
- `parse_status`: pending/processing/done/failed
- `uploaded_at`, `parsed_at`

### EXTRACTED_SKILL (parser.ExtractedSkill)
- `id`: UUID PK
- `cv_upload`: FK
- `skill_name`, `normalized_name`
- `confidence_score`: float
- `skill_vector`: VectorField (384 dimensions)

### JOB_POSTING (scraper.JobPosting)
- `id`: UUID PK
- `title`, `company`, `source`
- `source_url`, `district`, `experience_level`, `salary_range`
- `scraped_at`, `is_active`

### JOB_SKILL (scraper.JobSkill)
- `id`: UUID PK
- `job_posting`: FK
- `skill_name`, `normalized_name`
- `is_required`: bool
- `skill_vector`: VectorField (384 dimensions)

### SCRAPE_JOB (scraper.ScrapeJob)
- `id`: UUID PK
- `source`, `status`
- `jobs_found`, `jobs_saved`
- `started_at`, `completed_at`

### SKILL_GAP_REPORT (analysis.SkillGapReport)
- `id`: UUID PK
- `user`: FK, `cv_upload`: FK
- `readiness_score`: float (0-100)
- `total_jobs_matched`: int
- `status`: pending/generating/ready/failed
- `generated_at`

### GAP_ITEM (analysis.GapItem)
- `id`: UUID PK
- `report`: FK
- `skill_name`
- `demand_frequency`: float
- `similarity_score`: float
- `priority_rank`: int

### ROADMAP (roadmap.Roadmap)
- `id`: UUID PK
- `report`: OneToOne FK
- `generated_by`: str
- `created_at`

### ROADMAP_ITEM (roadmap.RoadmapItem)
- `id`: UUID PK
- `roadmap`: FK, `gap_item`: FK
- `skill_name`, `week_number`, `description`

### RESOURCE (roadmap.Resource)
- `id`: UUID PK
- `roadmap_item`: FK
- `title`, `url`, `platform`, `resource_type`

## 🚀 Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 16 with pgvector
- Redis

### Environment Setup

1. **Clone and setup**
```bash
git clone <repository>
cd SkillMapNepal
cp .env.example .env
```

2. **Configure environment variables in `.env`**
```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://skillmap_user:skillmap_pass@db:5432/skillmap_db
REDIS_URL=redis://redis:6379/0
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
GEMINI_API_KEY=your-gemini-api-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

3. **Build and run with Docker**
```bash
docker-compose up --build
```

Services will be available at:
- Web: http://localhost
- Admin: http://localhost/admin
- API: http://localhost/api (if configured)

### Local Development (without Docker)

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Install spaCy model**
```bash
python -m spacy download en_core_web_md
```

3. **Install Playwright browsers**
```bash
playwright install chromium
playwright install-deps chromium
```

4. **Setup PostgreSQL with pgvector**
```sql
CREATE DATABASE skillmap_db;
CREATE USER skillmap_user WITH PASSWORD 'skillmap_pass';
ALTER ROLE skillmap_user SET client_encoding TO 'utf8';
ALTER ROLE skillmap_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE skillmap_user SET timezone TO 'Asia/Kathmandu';
GRANT ALL PRIVILEGES ON DATABASE skillmap_db TO skillmap_user;

-- Connect to skillmap_db
\c skillmap_db
CREATE EXTENSION vector;
```

5. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Collect static files**
```bash
python manage.py collectstatic
```

8. **Run development servers**

Terminal 1 - Django:
```bash
python manage.py runserver
```

Terminal 2 - Celery Worker:
```bash
celery -A skillmap worker --loglevel=info
```

Terminal 3 - Celery Beat:
```bash
celery -A skillmap beat --loglevel=info
```

Terminal 4 - Redis (if not using Docker):
```bash
redis-server
```

## 📋 Management Commands

### Seed skill normalization mappings
```bash
python manage.py seed_skills
```

### Manually trigger job scraping
```bash
# Scrape all sources
python manage.py scrape_jobs

# Scrape specific source
python manage.py scrape_jobs --source merojob
python manage.py scrape_jobs --source kumarijob
```

## 🔄 Celery Tasks

### Task Chain Flow
```
1. parse_cv_task (parser.tasks)
   ↓
2. analyze_skill_gap_task (analysis.tasks)
   ↓
3. generate_roadmap_task (roadmap.tasks)
```

### Scheduled Tasks (Celery Beat)
- `scrape_all_sources`: Runs every 24 hours
- Scrapes Merojob and Kumarijob for latest tech jobs

### Retry Logic
- All tasks have max 3 retries
- Exponential backoff: 60s, 120s, 240s
- Status tracking in database

## 🎨 Frontend Features

### Dashboard
- Readiness score gauge (Chart.js)
- Radar chart for skill coverage
- Bar chart for top missing skills
- Report history table

### CV Upload
- Drag & drop support
- File validation (PDF, DOCX, max 10MB)
- Upload history with status

### Report View
- Interactive charts
- Skill comparison
- Gap prioritization
- Roadmap link

### Roadmap View
- Week-by-week timeline
- Resource cards with links
- Progress tracking

## 🔒 Security

- CSRF protection enabled
- File upload validation
- SQL injection prevention (Django ORM)
- XSS protection (Django templates)
- Secrets in environment variables
- User authentication required for all features

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test parser
python manage.py test scraper
python manage.py test analysis
python manage.py test roadmap
```

## 📝 Admin Panel

Access Django admin at `/admin/` to:
- View scrape job logs
- Monitor CV parse status
- Check report generation status
- Manage users and data

## 🐛 Troubleshooting

### PostgreSQL Connection Error
```bash
# Check PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs db
```

### Celery Tasks Not Running
```bash
# Check Celery worker logs
docker-compose logs worker

# Check Redis connection
docker-compose logs redis
```

### CV Parsing Failed
- Check Cloudinary credentials
- Verify file format (PDF/DOCX only)
- Check spaCy model installation
- View parser task logs in admin

### Scraping Failed
- Check Playwright installation
- Verify network connectivity
- Check scraper task logs in admin
- Sites may have changed structure

### Gemini API Error
- Verify GEMINI_API_KEY in .env
- Check API quota (free tier limit)
- Review roadmap task logs
- Ensure genai.configure() is inside function (not module level)

## 📦 Docker Services

- `db`: PostgreSQL 16 with pgvector
- `redis`: Redis 7 Alpine
- `web`: Django + Gunicorn
- `worker`: Celery worker + beat
- `nginx`: Reverse proxy

## 🔮 Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Email notifications
- [ ] PDF report export
- [ ] More job sites (Jobs Nepal, etc.)
- [ ] Skill endorsements
- [ ] LinkedIn integration
- [ ] Mobile app
- [ ] Recommendation engine

## 📄 License

MIT License - see LICENSE file

## 👥 Contributors

Built for Nepali tech job seekers 🇳🇵

## 🙏 Acknowledgments

- Merojob.com and Kumarijob.com for job data
- spaCy for NLP
- **Google Gemini for free AI-powered roadmap generation** 🎉
- sentence-transformers for embeddings
- pgvector for vector similarity search
