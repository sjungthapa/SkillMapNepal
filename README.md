# SkillMap Nepal 🗺️

An AI-powered job skill gap analyzer that helps Nepali tech job seekers identify missing skills and get personalized learning roadmaps.

**✨ Powered by Groq API (Llama 3.3 70B) — completely FREE!**

## 🎯 Overview

SkillMap Nepal analyzes your CV against real job market demands from Merojob.com and provides:

- Detailed skill gap analysis
- Market readiness score (0-100%)
- AI-generated personalized learning roadmap (powered by **Groq API — FREE!** 🎉)
- Week-by-week learning plan with curated free resources

## 🏗️ Architecture

### Technology Stack

- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL 16 with pgvector extension
- **Task Queue**: Celery + Redis
- **Web Scraping**: Merojob API (api.merojob.com)
- **CV Parsing**: pdfplumber + python-docx + spaCy
- **NLP/ML**: sentence-transformers (all-MiniLM-L6-v2, 384 dimensions)
- **AI**: Groq API (Llama 3.3 70B) — FREE tier
- **Storage**: Cloudinary (CV files)
- **Frontend**: Django Templates + Tailwind CSS + Chart.js
- **Deployment**: Docker + Gunicorn + Nginx

### System Flow

```
1. User uploads CV (PDF/DOCX)
2. Celery task: Parse CV → Extract skills → Vectorize with sentence-transformers
3. Celery task: Analyze skill gaps using pgvector cosine similarity
4. Celery task: Generate roadmap using Groq API (Llama 3.3 70B)
5. User views dashboard with charts and personalized roadmap
```

### Django Apps

#### `users/`
- Custom User model with UUID primary key
- Email-based authentication via django-allauth
- Profile management

#### `parser/`
- CV upload handling (PDF/DOCX)
- Text extraction with pdfplumber + python-docx
- Tech skill extraction using keyword matching
- Vectorization using sentence-transformers

#### `scraper/`
- Merojob API integration (api.merojob.com)
- IT & Telecommunication job scraping with pagination
- Skill extraction from job descriptions
- Runs via Celery beat every 24 hours
- Deduplication by source_url

#### `analysis/`
- pgvector cosine similarity computation
- Skill gap identification
- Readiness score calculation (0-100%)
- Job matching algorithm

#### `roadmap/`
- Groq API integration (Llama 3.3 70B)
- JSON-structured roadmap generation
- Free resource curation
- Week-by-week learning plans

#### `dashboard/`
- Dashboard views with Chart.js visualizations
- AJAX status polling with loading UI
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
- `generated_by`: str (e.g. llama-3.3-70b-versatile)
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
git clone https://github.com/sjungthapa/SkillMapNepal.git
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
GROQ_API_KEY=your-groq-api-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

Get a free Groq API key at: https://console.groq.com

3. **Build and run with Docker**
```bash
docker-compose up --build
```

Services will be available at:
- Web: http://localhost
- Admin: http://localhost/admin

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

3. **Setup PostgreSQL with pgvector**
```sql
CREATE DATABASE skillmap_db;
CREATE USER skillmap_user WITH PASSWORD 'skillmap_pass';
ALTER ROLE skillmap_user SET client_encoding TO 'utf8';
ALTER ROLE skillmap_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE skillmap_user SET timezone TO 'Asia/Kathmandu';
GRANT ALL PRIVILEGES ON DATABASE skillmap_db TO skillmap_user;

\c skillmap_db
CREATE EXTENSION vector;
```

4. **Run migrations**
```bash
python manage.py migrate
```

5. **Create superuser**
```bash
python manage.py createsuperuser
```

6. **Collect static files**
```bash
python manage.py collectstatic
```

7. **Run development servers**

Terminal 1 - Django:
```bash
python manage.py runserver
```

Terminal 2 - Celery Worker (optional, set CELERY_TASK_ALWAYS_EAGER=True to skip):
```bash
celery -A skillmap worker --loglevel=info
```

Terminal 3 - Celery Beat (optional):
```bash
celery -A skillmap beat --loglevel=info
```

## 📋 Management Commands

### Manually trigger job scraping
```bash
python manage.py scrape_jobs
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

### Retry Logic
- All tasks have max 3 retries
- Exponential backoff: 60s, 120s, 240s
- Status tracked in database

## 🎨 Frontend Features

### Dashboard
- Readiness score display
- Bar chart for top missing skills
- Report history

### CV Upload
- PDF and DOCX support (max 10MB)
- Real-time status page with progress steps
- Auto-redirect to report when ready

### Report View
- Interactive Chart.js bar chart
- Current skills display
- Priority skills to learn
- Matched jobs with percentage

### Roadmap View
- Week-by-week learning timeline
- Free resource links per skill

## 🔒 Security

- CSRF protection enabled
- File upload validation (type + size)
- SQL injection prevention (Django ORM)
- XSS protection (Django templates)
- Secrets in environment variables
- Authentication required for all features

## 🧪 Testing

```bash
python manage.py test
```

## 📝 Admin Panel

Access at `/admin/` to:
- View scrape job logs
- Monitor CV parse status
- Check report generation status
- Manage users and data

## 🐛 Troubleshooting

### PostgreSQL Connection Error
```bash
docker-compose ps
docker-compose logs db
```

### Celery Tasks Not Running
```bash
docker-compose logs worker
docker-compose logs redis
```

### CV Parsing Failed
- Check Cloudinary credentials in `.env`
- Verify file is PDF or DOCX
- Check spaCy model: `python -m spacy download en_core_web_md`

### Scraping Failed
- Run `python manage.py scrape_jobs` manually
- Check network connectivity to api.merojob.com

### Groq API Error
- Verify `GROQ_API_KEY` in `.env`
- Get a free key at https://console.groq.com
- Check daily rate limit (14,400 requests/day on free tier)

## 📦 Docker Services

- `db`: PostgreSQL 16 with pgvector
- `redis`: Redis 7 Alpine
- `web`: Django + Gunicorn
- `worker`: Celery worker + beat
- `nginx`: Reverse proxy

## 🔮 Future Enhancements

- [ ] GitHub Actions CI/CD pipeline
- [ ] Comprehensive test suite
- [ ] Real-time WebSocket updates
- [ ] Email notifications
- [ ] PDF report export
- [ ] More job sites (Kumarijob, Jobs Nepal)
- [ ] Multi-field support (Finance, Design, Marketing)
- [ ] LinkedIn integration
- [ ] Mobile app

## 📄 License

MIT License - see LICENSE file

## 👥 Contributors

Built for Nepali tech job seekers 🇳🇵

## 🙏 Acknowledgments

- Merojob.com for job market data
- spaCy for NLP
- **Groq API (Llama 3.3 70B) for free AI-powered roadmap generation** 🎉
- sentence-transformers for skill embeddings
- pgvector for vector similarity search