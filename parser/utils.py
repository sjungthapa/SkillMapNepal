"""CV parsing utilities — keyword-based skill extraction (no spaCy required)"""
import os
import re
import tempfile
import requests
import pdfplumber
from docx import Document
import logging

logger = logging.getLogger(__name__)

# Skill normalization dictionary
SKILL_MAPPINGS = {
    'reactjs': 'React.js', 'react': 'React.js', 'react.js': 'React.js',
    'vuejs': 'Vue.js', 'vue': 'Vue.js', 'vue.js': 'Vue.js',
    'nodejs': 'Node.js', 'node': 'Node.js', 'node.js': 'Node.js',
    'nextjs': 'Next.js', 'next.js': 'Next.js',
    'nuxtjs': 'Nuxt.js', 'nuxt': 'Nuxt.js',
    'postgres': 'PostgreSQL', 'postgresql': 'PostgreSQL',
    'mongo': 'MongoDB', 'mongodb': 'MongoDB',
    'js': 'JavaScript', 'javascript': 'JavaScript',
    'ts': 'TypeScript', 'typescript': 'TypeScript',
    'py': 'Python', 'python': 'Python',
    'django': 'Django', 'flask': 'Flask', 'fastapi': 'FastAPI',
    'angular': 'Angular', 'angularjs': 'Angular',
    'java': 'Java',
    'spring': 'Spring Boot', 'springboot': 'Spring Boot',
    'c++': 'C++', 'cpp': 'C++',
    'c#': 'C#', 'csharp': 'C#',
    'dotnet': '.NET', '.net': '.NET',
    'aws': 'AWS', 'amazon web services': 'AWS',
    'azure': 'Azure',
    'gcp': 'Google Cloud', 'google cloud platform': 'Google Cloud',
    'docker': 'Docker',
    'kubernetes': 'Kubernetes', 'k8s': 'Kubernetes',
    'git': 'Git', 'github': 'GitHub', 'gitlab': 'GitLab',
    'mysql': 'MySQL', 'mariadb': 'MariaDB',
    'redis': 'Redis', 'elasticsearch': 'Elasticsearch',
    'html': 'HTML', 'html5': 'HTML',
    'css': 'CSS', 'css3': 'CSS',
    'sass': 'SASS', 'scss': 'SCSS',
    'tailwind': 'Tailwind CSS', 'tailwindcss': 'Tailwind CSS',
    'bootstrap': 'Bootstrap',
    'rest': 'REST API', 'restful': 'REST API', 'rest api': 'REST API',
    'graphql': 'GraphQL',
    'sql': 'SQL', 'nosql': 'NoSQL',
    'jenkins': 'Jenkins', 'ci/cd': 'CI/CD',
    'terraform': 'Terraform', 'ansible': 'Ansible',
    'linux': 'Linux', 'ubuntu': 'Linux', 'centos': 'Linux',
    'bash': 'Bash', 'shell': 'Shell Scripting',
    'agile': 'Agile', 'scrum': 'Scrum',
    'jira': 'JIRA', 'confluence': 'Confluence',
    'figma': 'Figma', 'postman': 'Postman',
    'redux': 'Redux', 'jwt': 'JWT', 'oauth': 'OAuth',
    'webpack': 'Webpack', 'vite': 'Vite',
    'express': 'Express', 'expressjs': 'Express',
    'nestjs': 'NestJS', 'nest': 'NestJS',
    'kotlin': 'Kotlin', 'swift': 'Swift',
    'flutter': 'Flutter', 'dart': 'Dart',
    'php': 'PHP', 'laravel': 'Laravel',
    'rust': 'Rust', 'go': 'Go', 'golang': 'Go',
    'ruby': 'Ruby', 'rails': 'Ruby on Rails',
    'celery': 'Celery', 'rabbitmq': 'RabbitMQ', 'kafka': 'Kafka',
    'nginx': 'Nginx', 'apache': 'Apache',
    'cloudinary': 'Cloudinary', 'stripe': 'Stripe',
    'firebase': 'Firebase', 'supabase': 'Supabase',
    'pandas': 'Pandas', 'numpy': 'NumPy',
    'tensorflow': 'TensorFlow', 'pytorch': 'PyTorch',
    'scikit-learn': 'scikit-learn', 'sklearn': 'scikit-learn',
    'microservices': 'Microservices', 'tdd': 'TDD',
    'github actions': 'GitHub Actions',
    'vs code': 'VS Code', 'vscode': 'VS Code',
    'shadcn': 'Shadcn UI', 'shadcn ui': 'Shadcn UI',
    'pgvector': 'pgvector', 'spacy': 'spaCy',
    'sentence-transformers': 'sentence-transformers',
    'groq': 'Groq API', 'langchain': 'LangChain',
    'power bi': 'Power BI', 'tableau': 'Tableau',
}

# All keywords to search for (lowercase)
TECH_KEYWORDS = set(SKILL_MAPPINGS.keys())


def normalize_skill(skill_name):
    """Normalize skill name using mapping dictionary."""
    skill_lower = skill_name.lower().strip()
    return SKILL_MAPPINGS.get(skill_lower, skill_name.title())


def extract_skills_from_text(text):
    """
    Extract tech skills from text using keyword matching only.
    No spaCy or ML models needed — fast and memory efficient.
    """
    if not text:
        return []

    text_lower = text.lower()
    found = {}

    for keyword in TECH_KEYWORDS:
        # Word boundary check to avoid partial matches
        pattern = r'(?<![a-zA-Z0-9\-])' + re.escape(keyword) + r'(?![a-zA-Z0-9\-])'
        if re.search(pattern, text_lower):
            display = SKILL_MAPPINGS.get(keyword, keyword.title())
            found[display] = True

    return list(found.keys())


def vectorize_skills(skills):
    """
    Convert skills to vectors using sentence-transformers.
    Model is loaded lazily — only when CV is uploaded.
    """
    from sentence_transformers import SentenceTransformer

    # Lazy load — only loads once per process
    global _encoder
    if '_encoder' not in globals() or _encoder is None:
        logger.info("Loading sentence-transformers model...")
        _encoder = SentenceTransformer('all-MiniLM-L6-v2')

    skill_data = []
    for skill in skills:
        normalized = normalize_skill(skill)
        vector = _encoder.encode(normalized)
        skill_data.append({
            'skill_name': skill,
            'normalized_name': normalized,
            'skill_vector': vector.tolist(),
            'confidence_score': 1.0
        })

    return skill_data


_encoder = None


def download_file(url):
    """Download file from Cloudinary using authenticated signed URL."""
    import cloudinary
    import cloudinary.utils
    from django.conf import settings

    cloudinary.config(
        cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
        api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
        api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
    )

    # Extract public_id from URL
    if '/upload/' in url:
        after_upload = url.split('/upload/')[1]
        if after_upload.startswith('v') and '/' in after_upload:
            parts = after_upload.split('/', 1)
            if parts[0][1:].isdigit():
                after_upload = parts[1]
        public_id = after_upload
    else:
        public_id = url

    signed_url, _ = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type='raw',
        sign_url=True,
        type='upload',
        secure=True,
        api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
        api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
    )

    response = requests.get(signed_url, timeout=30)
    response.raise_for_status()

    suffix = '.pdf' if url.lower().endswith('.pdf') else '.docx'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(response.content)
        return tmp.name


def extract_text_from_pdf(file_path):
    """Extract text from PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def extract_text_from_docx(file_path):
    """Extract text from DOCX using python-docx."""
    doc = Document(file_path)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])


def extract_text_from_cv(file_url):
    """Extract text from CV file (PDF or DOCX) downloaded from Cloudinary."""
    temp_file = download_file(file_url)
    try:
        if temp_file.endswith('.pdf'):
            return extract_text_from_pdf(temp_file)
        elif temp_file.endswith('.docx'):
            return extract_text_from_docx(temp_file)
        else:
            raise ValueError("Unsupported file format")
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def parse_cv(file_url, is_local=False):
    """
    Main CV parsing pipeline.
    Args:
        file_url: Cloudinary URL or local file path
        is_local: If True, read directly from local path (skip Cloudinary download)
    Returns: dict with extracted skills and raw text
    """
    logger.info(f"Starting CV parsing for: {file_url}")

    # Extract text
    if is_local:
        if file_url.endswith('.pdf'):
            text = extract_text_from_pdf(file_url)
        elif file_url.endswith('.docx'):
            text = extract_text_from_docx(file_url)
        else:
            raise ValueError("Unsupported file format")
    else:
        text = extract_text_from_cv(file_url)

    logger.info(f"Extracted {len(text)} characters from CV")

    # Extract skills using keyword matching
    skills = extract_skills_from_text(text)
    logger.info(f"Found {len(skills)} skills")

    # Vectorize skills
    skill_data = vectorize_skills(skills)
    logger.info(f"Vectorized {len(skill_data)} skills")

    return {
        'skills': skill_data,
        'raw_text': text[:1000],
    }