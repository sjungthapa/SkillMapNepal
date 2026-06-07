"""
Celery tasks for scraping Nepali job sites.
Uses Merojob's real API: https://api.merojob.com/api/v1/jobs/
"""
import logging
import requests
import re
from celery import shared_task
from django.utils import timezone
from sentence_transformers import SentenceTransformer

from .models import JobPosting, JobSkill, ScrapeJob

logger = logging.getLogger(__name__)

MEROJOB_API = "https://api.merojob.com/api/v1/jobs/"
MEROJOB_BASE = "https://merojob.com"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://merojob.com/',
    'Origin': 'https://merojob.com',
}

# Tech keywords to extract from job descriptions
TECH_KEYWORDS = {
    'python', 'javascript', 'typescript', 'java', 'c#', 'c++', 'php',
    'dart', 'kotlin', 'swift', 'rust', 'go', 'ruby',
    'react', 'react.js', 'vue', 'vue.js', 'angular', 'next.js',
    'nuxt', 'svelte', 'tailwind', 'bootstrap', 'html', 'css',
    'sass', 'scss', 'redux', 'jquery',
    'node.js', 'express', 'django', 'flask', 'fastapi',
    'spring', 'laravel', 'nestjs', 'graphql', 'rest api',
    'postgresql', 'mysql', 'mongodb', 'redis', 'sqlite',
    'elasticsearch', 'firebase', 'dynamodb',
    'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'linux',
    'nginx', 'ci/cd', 'jenkins', 'github actions', 'terraform',
    'git', 'github', 'gitlab', 'jira', 'figma', 'postman',
    'tensorflow', 'pytorch', 'pandas', 'numpy',
    'celery', 'kafka', 'rabbitmq',
    'microservices', 'agile', 'scrum', 'tdd', 'jwt',
    'cloudinary', 'stripe', 'sql', 'nosql', 'power bi',
}

SKILL_DISPLAY = {
    'react': 'React.js', 'react.js': 'React.js',
    'vue': 'Vue.js', 'vue.js': 'Vue.js',
    'node.js': 'Node.js', 'next.js': 'Next.js',
    'postgresql': 'PostgreSQL', 'mongodb': 'MongoDB',
    'javascript': 'JavaScript', 'typescript': 'TypeScript',
    'python': 'Python', 'django': 'Django', 'flask': 'Flask',
    'fastapi': 'FastAPI', 'docker': 'Docker',
    'kubernetes': 'Kubernetes', 'aws': 'AWS',
    'azure': 'Azure', 'gcp': 'Google Cloud',
    'git': 'Git', 'github': 'GitHub', 'gitlab': 'GitLab',
    'css': 'CSS', 'html': 'HTML', 'sass': 'SASS',
    'tailwind': 'Tailwind CSS', 'bootstrap': 'Bootstrap',
    'redis': 'Redis', 'linux': 'Linux', 'nginx': 'Nginx',
    'ci/cd': 'CI/CD', 'rest api': 'REST API',
    'graphql': 'GraphQL', 'sql': 'SQL', 'nosql': 'NoSQL',
    'agile': 'Agile', 'scrum': 'Scrum', 'jira': 'JIRA',
    'figma': 'Figma', 'postman': 'Postman',
    'celery': 'Celery', 'redux': 'Redux', 'jwt': 'JWT',
    'cloudinary': 'Cloudinary', 'express': 'Express',
    'nestjs': 'NestJS', 'java': 'Java', 'kotlin': 'Kotlin',
    'swift': 'Swift', 'php': 'PHP', 'laravel': 'Laravel',
    'c#': 'C#', 'c++': 'C++', 'rust': 'Rust', 'go': 'Go',
    'ruby': 'Ruby', 'jquery': 'jQuery',
    'github actions': 'GitHub Actions',
    'power bi': 'Power BI', 'tensorflow': 'TensorFlow',
    'pytorch': 'PyTorch', 'pandas': 'Pandas',
    'numpy': 'NumPy', 'kafka': 'Kafka',
    'microservices': 'Microservices', 'stripe': 'Stripe',
    'terraform': 'Terraform', 'jenkins': 'Jenkins',
    'elasticsearch': 'Elasticsearch', 'firebase': 'Firebase',
    'mysql': 'MySQL', 'sqlite': 'SQLite',
}


def extract_skills_from_text(text):
    """Extract tech skills from text using keyword matching."""
    if not text:
        return []
    text_lower = text.lower()
    found = {}
    for keyword in TECH_KEYWORDS:
        pattern = r'(?<![a-zA-Z0-9\-])' + re.escape(keyword) + r'(?![a-zA-Z0-9\-])'
        if re.search(pattern, text_lower):
            display = SKILL_DISPLAY.get(keyword, keyword.title())
            found[display] = True
    return list(found.keys())


def extract_skills_from_job(job_data):
    """
    Extract skills from both the structured skills field and
    description/specification text for maximum coverage.
    """
    skills = set()

    # 1. From structured skills field (already extracted by Merojob)
    for skill in job_data.get('skills', []):
        normalized = extract_skills_from_text(skill)
        skills.update(normalized)
        # Also add common ones directly if they match known tech
        skill_lower = skill.lower().strip()
        if skill_lower in SKILL_DISPLAY:
            skills.add(SKILL_DISPLAY[skill_lower])

    # 2. From title
    skills.update(extract_skills_from_text(job_data.get('title', '')))

    # 3. From description HTML (strip tags first)
    description = job_data.get('description', '') or ''
    description = re.sub(r'<[^>]+>', ' ', description)
    skills.update(extract_skills_from_text(description))

    # 4. From specification HTML
    specification = job_data.get('specification', '') or ''
    specification = re.sub(r'<[^>]+>', ' ', specification)
    skills.update(extract_skills_from_text(specification))

    # 5. From job summary
    skills.update(extract_skills_from_text(job_data.get('job_summary', '') or ''))

    return list(skills)


def fetch_merojob_it_jobs():
    """
    Fetch all IT & Telecommunication jobs from Merojob API.
    Handles pagination automatically.
    """
    all_jobs = []
    url = f"{MEROJOB_API}?categories=IT+%26+Telecommunication&page_size=20"

    page = 1
    while url and page <= 10:  # Max 10 pages = 200 jobs
        try:
            logger.info(f"Fetching Merojob page {page}: {url}")
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            data = response.json()

            results = data.get('results', [])
            all_jobs.extend(results)
            logger.info(f"Page {page}: got {len(results)} jobs (total: {len(all_jobs)})")

            url = data.get('next')  # Next page URL from API
            page += 1

        except Exception as e:
            logger.error(f"Error fetching Merojob page {page}: {e}")
            break

    return all_jobs


def save_merojob_jobs(raw_jobs, encoder):
    """Save Merojob jobs to database."""
    saved = 0
    skipped = 0

    for job_data in raw_jobs:
        try:
            slug = job_data.get('absolute_url', '').strip('/')
            source_url = f"{MEROJOB_BASE}/{slug}/" if slug else ''

            # Skip if already exists
            if source_url and JobPosting.objects.filter(source_url=source_url).exists():
                skipped += 1
                continue

            # Extract company info
            client = job_data.get('client', {}) or {}
            company = client.get('org_name') or client.get('client_name') or 'Unknown'

            # Extract location
            locations = job_data.get('job_locations', [])
            district = ''
            if locations:
                district = locations[0].get('address', '') or ''

            # Extract salary
            salary_data = job_data.get('offered_salary') or {}
            salary = ''
            if salary_data:
                currency = salary_data.get('currency', '')
                min_sal = salary_data.get('minimum', '')
                max_sal = salary_data.get('maximum', '')
                unit = salary_data.get('unit', '')
                if min_sal and max_sal:
                    salary = f"{currency} {min_sal:,.0f} - {max_sal:,.0f} {unit}"

            # Create job posting
            posting = JobPosting.objects.create(
                title=job_data.get('title', 'Unknown'),
                company=company,
                source='merojob',
                source_url=source_url,
                experience_level=job_data.get('experience_required', ''),
                salary_range=salary,
                district=district[:100] if district else '',
                is_active=True,
                scraped_at=timezone.now(),
            )

            # Extract and save skills
            skills = extract_skills_from_job(job_data)

            if not skills:
                # If no tech skills found, skip saving this job
                # (non-tech jobs like Finance Manager)
                posting.delete()
                skipped += 1
                continue

            for skill_name in skills:
                try:
                    vector = encoder.encode(skill_name).tolist()
                    JobSkill.objects.create(
                        job_posting=posting,
                        skill_name=skill_name,
                        normalized_name=skill_name,
                        is_required=True,
                        skill_vector=vector,
                    )
                except Exception as e:
                    logger.warning(f"Failed to save skill {skill_name}: {e}")

            saved += 1
            logger.info(f"Saved: {posting.title} @ {company} | {len(skills)} skills")

        except Exception as e:
            logger.warning(f"Failed to save job: {e}")
            continue

    return saved, skipped


# ── Celery Tasks ──────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def scrape_merojob_task(self):
    scrape_job = ScrapeJob.objects.create(
        source='merojob', status='running', started_at=timezone.now()
    )
    try:
        logger.info("Loading sentence-transformers encoder...")
        encoder = SentenceTransformer('all-MiniLM-L6-v2')

        logger.info("Fetching IT jobs from Merojob API...")
        raw_jobs = fetch_merojob_it_jobs()
        logger.info(f"Fetched {len(raw_jobs)} raw jobs")

        saved, skipped = save_merojob_jobs(raw_jobs, encoder)

        scrape_job.status = 'done'
        scrape_job.jobs_found = len(raw_jobs)
        scrape_job.jobs_saved = saved
        scrape_job.completed_at = timezone.now()
        scrape_job.save()

        logger.info(f"Merojob scrape done: {saved} saved, {skipped} skipped")
        return {'source': 'merojob', 'jobs_found': len(raw_jobs), 'jobs_saved': saved}

    except Exception as exc:
        scrape_job.status = 'failed'
        scrape_job.completed_at = timezone.now()
        scrape_job.save()
        logger.error(f"Merojob scrape failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def scrape_kumarijob_task(self):
    """Placeholder — Kumarijob scraper to be implemented."""
    logger.info("Kumarijob scraper not yet implemented")
    return {'source': 'kumarijob', 'jobs_saved': 0}


@shared_task
def scrape_all_sources():
    """Run all scrapers — called by Celery beat every 24 hours."""
    scrape_merojob_task.delay()
    scrape_kumarijob_task.delay()
    return {'status': 'scrapers queued'}