# SkillMap Nepal - Project Structure

## Directory Layout

```
SkillMapNepal/
├── skillmap/                   # Django project settings
│   ├── __init__.py
│   ├── settings.py            # Main settings with Celery, pgvector config
│   ├── celery.py              # Celery app configuration
│   ├── urls.py                # Root URL configuration
│   ├── wsgi.py                # WSGI application
│   └── asgi.py                # ASGI application
│
├── users/                      # User authentication app
│   ├── models.py              # Custom User model (UUID PK, email auth)
│   ├── admin.py               # User admin configuration
│   ├── management/
│   │   └── commands/
│   │       └── setup_site.py  # Django sites setup for allauth
│   └── __init__.py
│
├── parser/                     # CV parsing app
│   ├── models.py              # CVUpload, ExtractedSkill
│   ├── admin.py               # Admin for CV uploads
│   ├── utils.py               # PDF/DOCX parsing, spaCy NER, vectorization
│   ├── tasks.py               # parse_cv_task (Celery)
│   ├── tests.py               # Unit tests
│   ├── management/
│   │   └── commands/
│   │       └── seed_skills.py # Display skill normalization mappings
│   └── __init__.py
│
├── scraper/                    # Job scraping app
│   ├── models.py              # JobPosting, JobSkill, ScrapeJob
│   ├── admin.py               # Scrape job monitoring
│   ├── scrapers.py            # Playwright scrapers (Merojob, Kumarijob)
│   ├── tasks.py               # scrape_merojob_task, scrape_kumarijob_task
│   ├── management/
│   │   └── commands/
│   │       └── scrape_jobs.py # Manual scrape trigger
│   └── __init__.py
│
├── analysis/                   # Skill gap analysis app
│   ├── models.py              # SkillGapReport, GapItem
│   ├── admin.py               # Report admin
│   ├── tasks.py               # analyze_skill_gap_task (pgvector queries)
│   ├── tests.py               # Analysis tests
│   └── __init__.py
│
├── roadmap/                    # AI roadmap generation app
│   ├── models.py              # Roadmap, RoadmapItem, Resource
│   ├── admin.py               # Roadmap admin
│   ├── tasks.py               # generate_roadmap_task (Claude API)
│   └── __init__.py
│
├── dashboard/                  # Dashboard & views app
│   ├── views.py               # All user-facing views
│   ├── urls.py                # Dashboard URL routing
│   ├── serializers.py         # DRF serializers for API
│   └── __init__.py
│
├── templates/                  # Django templates
│   ├── base.html              # Base template with nav, Tailwind
│   ├── home.html              # Landing page
│   └── dashboard/
│       ├── home.html          # Dashboard main page
│       ├── upload_cv.html     # CV upload form
│       ├── report_detail.html # Skill gap report with Chart.js
│       ├── roadmap.html       # Learning roadmap view
│       └── profile.html       # User profile
│
├── static/                     # Static files
│   ├── css/                   # Custom CSS (if needed)
│   └── js/                    # Custom JavaScript
│
├── media/                      # User uploads (local dev only)
├── staticfiles/                # Collected static files
│
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Django app container
├── nginx.conf                  # Nginx configuration
│
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── setup.sh                   # Setup script for Docker
│
├── manage.py                  # Django management script
│
├── README.md                  # Main documentation
├── QUICKSTART.md              # Quick start guide
├── ARCHITECTURE.md            # Architecture documentation
└── PROJECT_STRUCTURE.md       # This file
```

## Key Files Explained

### Configuration Files

**settings.py**
- Custom User model configuration
- PostgreSQL with pgvector
- Celery configuration
- Django-allauth setup
- Cloudinary storage
- REST Framework settings

**celery.py**
- Celery app initialization
- Auto-discover tasks
- Beat schedule (daily scraping)

**docker-compose.yml**
- 4 services: db, redis, web, worker, nginx
- PostgreSQL with pgvector extension
- Celery worker + beat in one container

### Models (Database Schema)

**users.User**
- UUID primary key
- Email authentication
- Custom fields: full_name, phone

**parser.CVUpload**
- Tracks CV uploads
- Parse status: pending → processing → done/failed

**parser.ExtractedSkill**
- Skills from CV
- 384-dim vector for similarity search

**scraper.JobPosting**
- Job listings from Merojob/Kumarijob
- Source tracking, deduplication

**scraper.JobSkill**
- Skills required for jobs
- 384-dim vector for matching

**analysis.SkillGapReport**
- User's skill gap analysis
- Readiness score (0-100)

**analysis.GapItem**
- Individual missing skills
- Demand frequency, priority rank

**roadmap.Roadmap**
- AI-generated learning plan
- Links to report (OneToOne)

**roadmap.RoadmapItem**
- Week-by-week learning items
- Linked to gap items

**roadmap.Resource**
- Learning resources (videos, docs, courses)
- Platform categorization

### Celery Tasks

**parse_cv_task** (parser/tasks.py)
- Downloads CV from Cloudinary
- Extracts text (PDF/DOCX)
- Extracts skills with spaCy
- Normalizes and vectorizes
- Stores in database
- Triggers analysis

**analyze_skill_gap_task** (analysis/tasks.py)
- Loads user skills
- Loads job market skills
- Computes pgvector similarity
- Identifies gaps
- Calculates readiness score
- Triggers roadmap generation

**generate_roadmap_task** (roadmap/tasks.py)
- Constructs prompt for Claude
- Calls Anthropic API
- Parses JSON response
- Stores roadmap in database

**scrape_merojob_task** (scraper/tasks.py)
- Playwright scraper for Merojob
- Extracts job listings
- Identifies skills
- Stores in database

**scrape_kumarijob_task** (scraper/tasks.py)
- Playwright scraper for Kumarijob
- Same flow as Merojob

**scrape_all_sources** (scraper/tasks.py)
- Triggered by Celery beat (every 24h)
- Queues both scraper tasks

### Views & Templates

**dashboard/views.py**
- dashboard_home: Main dashboard
- upload_cv: CV upload form
- report_status: AJAX status check
- view_report: Detailed report with charts
- roadmap_view: Learning roadmap
- profile_view: User profile
- home: Landing page

**templates/**
- Tailwind CSS for styling
- Chart.js for visualizations
- AJAX for live updates

### Utilities

**parser/utils.py**
- SKILL_MAPPINGS: Normalization dictionary
- load_models(): spaCy + sentence-transformers
- normalize_skill(): Skill name normalization
- extract_text_from_pdf/docx(): Text extraction
- extract_skills_from_text(): spaCy NER
- vectorize_skills(): Generate embeddings
- parse_cv(): Main pipeline

**scraper/scrapers.py**
- scrape_merojob(): Async Playwright scraper
- scrape_kumarijob(): Async Playwright scraper
- extract_skills_from_job_page(): Skill extraction
- Synchronous wrappers for Celery

### Management Commands

**python manage.py seed_skills**
- Display skill normalization mappings
- Help understand normalization

**python manage.py scrape_jobs [--source merojob|kumarijob|all]**
- Manually trigger job scraping
- Useful for testing or immediate updates

**python manage.py setup_site**
- Configure Django sites for allauth
- Run once after migrations

## Data Flow Summary

```
User → Upload CV → Cloudinary → CVUpload DB
    ↓
parse_cv_task (Celery)
    ↓
ExtractedSkill DB (with vectors)
    ↓
analyze_skill_gap_task (Celery)
    ↓
SkillGapReport + GapItem DB
    ↓
generate_roadmap_task (Celery + Claude API)
    ↓
Roadmap + RoadmapItem + Resource DB
    ↓
User views Dashboard with Chart.js
```

## Technology Integration

### pgvector
- PostgreSQL extension for vector storage
- Cosine similarity search
- Used in: ExtractedSkill, JobSkill models

### sentence-transformers
- all-MiniLM-L6-v2 model
- 384-dimensional embeddings
- Fast CPU inference

### spaCy
- en_core_web_md model
- Named Entity Recognition
- Noun chunk extraction

### Playwright
- Headless browser automation
- Async/await syntax
- JavaScript rendering support

### Claude API
- claude-sonnet-4-20250514 model
- JSON output format
- Structured roadmap generation

### Celery + Redis
- Async task queue
- Beat scheduler for periodic tasks
- Result backend for status tracking

### Cloudinary
- CV file storage
- CDN delivery
- Automatic optimization

## Security Features

- UUID primary keys (prevents enumeration)
- Email-based authentication
- CSRF protection
- XSS prevention (Django templates)
- File upload validation
- Environment variable secrets
- User data isolation (FK checks)
- SQL injection prevention (ORM)

## Scalability Considerations

- Stateless application design
- Horizontal scaling ready
- Database connection pooling
- Celery worker scaling
- Redis cluster support
- CDN for static files
- pgvector indexing for large datasets

## Testing Strategy

- Unit tests for utilities (parser/utils.py)
- Model tests for all models
- Integration tests for task chains
- API tests for endpoints
- Mocking external services (Claude, Cloudinary)

## Next Steps for Development

1. Add more comprehensive tests
2. Implement WebSocket for real-time updates
3. Add email notifications
4. Create REST API endpoints
5. Build mobile app
6. Add more job sources
7. Implement caching layer
8. Add analytics dashboard
