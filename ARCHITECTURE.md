# SkillMap Nepal - Architecture Documentation

## System Overview

SkillMap Nepal is a Django-based web application that uses AI and machine learning to help job seekers identify skill gaps and get personalized learning recommendations.

## Technology Stack

### Backend
- **Framework**: Django 4.2+
- **Language**: Python 3.11
- **Database**: PostgreSQL 16 with pgvector extension
- **Task Queue**: Celery with Redis broker
- **API**: Django REST Framework

### Machine Learning & NLP
- **NLP**: spaCy (en_core_web_md)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2, 384-dim)
- **Vector Search**: pgvector (cosine similarity)
- **AI**: Anthropic Claude API (claude-sonnet-4-20250514)

### Web Scraping
- **Tool**: Playwright (async)
- **Targets**: Merojob.com, Kumarijob.com

### Storage & Deployment
- **File Storage**: Cloudinary
- **Web Server**: Gunicorn + Nginx
- **Containerization**: Docker + Docker Compose

### Frontend
- **Templates**: Django Templates
- **Styling**: Tailwind CSS (CDN)
- **Charts**: Chart.js
- **AJAX**: Vanilla JavaScript

## Data Flow

### 1. CV Upload Flow
```
User uploads CV (PDF/DOCX)
    ↓
Cloudinary stores file
    ↓
CVUpload record created (status: pending)
    ↓
parse_cv_task.delay() queued
    ↓
Celery worker picks up task
    ↓
Extract text (pdfplumber/python-docx)
    ↓
Extract skills (spaCy NER + pattern matching)
    ↓
Normalize skills (SKILL_MAPPINGS dict)
    ↓
Vectorize skills (sentence-transformers)
    ↓
Store in ExtractedSkill table with vectors
    ↓
CVUpload status → done
    ↓
Trigger analyze_skill_gap_task.delay()
```

### 2. Job Scraping Flow
```
Celery beat triggers scrape_all_sources (every 24h)
    ↓
scrape_merojob_task + scrape_kumarijob_task queued
    ↓
Playwright launches headless browser
    ↓
Navigate to job listings
    ↓
Extract job details (title, company, location)
    ↓
Visit job detail page
    ↓
Extract skills from description
    ↓
Normalize and vectorize skills
    ↓
Store in JobPosting + JobSkill tables
    ↓
Deduplicate by source_url
    ↓
Update ScrapeJob record
```

### 3. Skill Gap Analysis Flow
```
analyze_skill_gap_task triggered after CV parsing
    ↓
Load user skills (ExtractedSkill records)
    ↓
Load active job postings (JobPosting.is_active=True)
    ↓
For each job skill:
    - Check if user has it
    - If not, compute cosine similarity to closest user skill
    - Track demand frequency
    ↓
Aggregate gap items
    ↓
Calculate readiness score:
    readiness = (matched_skills / total_required) * 100
    ↓
Store in SkillGapReport + GapItem tables
    ↓
Trigger generate_roadmap_task.delay()
```

### 4. Roadmap Generation Flow
```
generate_roadmap_task triggered after analysis
    ↓
Load user's current skills
    ↓
Load top 10 gap items (priority ranked)
    ↓
Construct prompt for Claude API
    ↓
Call Claude with system + user prompts
    ↓
Claude returns JSON roadmap:
    - Week-by-week learning plan
    - Skills per week
    - Resources (title, URL, platform)
    ↓
Parse JSON response
    ↓
Store in Roadmap + RoadmapItem + Resource tables
    ↓
User notified via dashboard
```

## Vector Similarity Search

### Why pgvector?
- Native PostgreSQL extension
- Fast cosine similarity search
- Integrates seamlessly with Django ORM
- Scales to millions of vectors

### How it Works
1. **Encoding**: sentence-transformers converts text → 384-dim vector
2. **Storage**: Stored as `VectorField(dimensions=384)` in PostgreSQL
3. **Search**: pgvector performs cosine similarity:
   ```python
   similarity = vector1 <=> vector2  # cosine distance operator
   ```

### Example Query
```python
from pgvector.django import CosineDistance

# Find similar skills
similar_skills = JobSkill.objects.annotate(
    distance=CosineDistance('skill_vector', user_skill_vector)
).order_by('distance')[:10]
```

## Celery Task Architecture

### Task Types

1. **parse_cv_task**
   - **Trigger**: After CV upload
   - **Retry**: 3 attempts, 60s delay
   - **Duration**: 30-60 seconds
   - **Chain**: Triggers analyze_skill_gap_task

2. **analyze_skill_gap_task**
   - **Trigger**: After CV parsing
   - **Retry**: 3 attempts, 60s delay
   - **Duration**: 10-30 seconds
   - **Chain**: Triggers generate_roadmap_task

3. **generate_roadmap_task**
   - **Trigger**: After analysis
   - **Retry**: 3 attempts, 120s delay
   - **Duration**: 10-20 seconds
   - **Chain**: End of pipeline

4. **scrape_merojob_task / scrape_kumarijob_task**
   - **Trigger**: Celery beat (24h) or manual
   - **Retry**: 3 attempts, 300s delay
   - **Duration**: 2-5 minutes
   - **Chain**: None

### Task Status Tracking
- All tasks update status in database models
- Status choices: pending → processing/running → done/ready or failed
- Error messages stored for debugging

## Database Schema

### Core Tables

```sql
-- User authentication
users (UUID PK)

-- CV processing
cv_uploads (UUID PK, user FK)
extracted_skills (UUID PK, cv_upload FK, skill_vector vector(384))

-- Job market data
job_postings (UUID PK, source, is_active)
job_skills (UUID PK, job_posting FK, skill_vector vector(384))
scrape_jobs (UUID PK, source, status)

-- Analysis results
skill_gap_reports (UUID PK, user FK, cv_upload FK)
gap_items (UUID PK, report FK, priority_rank)

-- AI-generated roadmaps
roadmaps (UUID PK, report FK OneToOne)
roadmap_items (UUID PK, roadmap FK, week_number)
resources (UUID PK, roadmap_item FK)
```

### Indexes
- `skill_vector` columns (pgvector IVFFlat for large datasets)
- `normalized_name` (B-tree)
- `source_url` (unique constraint + B-tree)
- `is_active` (B-tree)
- Foreign keys (automatic)

## API Endpoints (Future)

Currently using Django views, but serializers ready for REST API:

```
GET  /api/reports/           - List user's reports
GET  /api/reports/{id}/      - Report detail
POST /api/cv/upload/         - Upload CV
GET  /api/roadmap/{id}/      - Roadmap detail
GET  /api/status/{cv_id}/    - Check processing status
```

## Security Considerations

1. **Authentication**: django-allauth with email
2. **Authorization**: User can only access their own data
3. **File Upload**: Validation (extension, size), virus scan recommended
4. **API Keys**: Environment variables, never in code
5. **SQL Injection**: Django ORM prevents
6. **XSS**: Django templates auto-escape
7. **CSRF**: Enabled by default
8. **HTTPS**: Required in production (Nginx SSL)

## Scalability

### Current Limits
- ~1000 CVs/day (with current setup)
- ~10,000 active job postings
- ~100 concurrent users

### Scaling Strategies

1. **Horizontal Scaling**
   - Multiple Celery workers
   - Read replicas for PostgreSQL
   - Redis Cluster

2. **Optimization**
   - pgvector IVFFlat index for >100k vectors
   - Celery task result expiration
   - CDN for static files
   - Database connection pooling

3. **Caching**
   - Redis cache for frequent queries
   - Template fragment caching
   - API response caching

## Monitoring & Logging

### Logging Levels
- **INFO**: Task starts/completions
- **WARNING**: Retries, non-critical errors
- **ERROR**: Task failures, API errors

### Metrics to Track
- Task completion times
- Task failure rates
- API response times
- CV parsing accuracy
- Scraper success rates

### Tools (Recommended)
- Sentry for error tracking
- Celery Flower for task monitoring
- Prometheus + Grafana for metrics
- ELK stack for log aggregation

## Deployment Architecture

```
Internet
    ↓
Nginx (Port 80/443)
    ↓
Gunicorn (Port 8000) ← Django App
    ↓                     ↓
PostgreSQL            Redis
(pgvector)            (Celery broker)
    ↑                     ↑
    └─────────────────────┘
         Celery Worker
         (Background tasks)
```

## Future Enhancements

1. **Real-time Updates**: WebSockets for live status
2. **Caching Layer**: Redis for query results
3. **CDN**: CloudFront for static assets
4. **Elasticsearch**: Full-text search for jobs
5. **GraphQL**: Alternative to REST API
6. **Microservices**: Separate scraper service
7. **ML Pipeline**: Airflow for data orchestration
