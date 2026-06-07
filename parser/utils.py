"""CV parsing utilities"""
import os
import tempfile
import requests
import pdfplumber
from docx import Document
import spacy
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

# Load models globally
nlp = None
encoder = None

# Skill normalization dictionary
SKILL_MAPPINGS = {
    'reactjs': 'React.js',
    'react': 'React.js',
    'vuejs': 'Vue.js',
    'vue': 'Vue.js',
    'nodejs': 'Node.js',
    'node': 'Node.js',
    'postgres': 'PostgreSQL',
    'postgresql': 'PostgreSQL',
    'mongo': 'MongoDB',
    'mongodb': 'MongoDB',
    'js': 'JavaScript',
    'javascript': 'JavaScript',
    'ts': 'TypeScript',
    'typescript': 'TypeScript',
    'py': 'Python',
    'python': 'Python',
    'django': 'Django',
    'flask': 'Flask',
    'fastapi': 'FastAPI',
    'angular': 'Angular',
    'angularjs': 'Angular',
    'java': 'Java',
    'spring': 'Spring Boot',
    'springboot': 'Spring Boot',
    'c++': 'C++',
    'cpp': 'C++',
    'c#': 'C#',
    'csharp': 'C#',
    'dotnet': '.NET',
    '.net': '.NET',
    'aws': 'AWS',
    'amazon web services': 'AWS',
    'azure': 'Azure',
    'gcp': 'Google Cloud',
    'google cloud platform': 'Google Cloud',
    'docker': 'Docker',
    'kubernetes': 'Kubernetes',
    'k8s': 'Kubernetes',
    'git': 'Git',
    'github': 'GitHub',
    'gitlab': 'GitLab',
    'mysql': 'MySQL',
    'mariadb': 'MariaDB',
    'redis': 'Redis',
    'elasticsearch': 'Elasticsearch',
    'html': 'HTML',
    'css': 'CSS',
    'sass': 'SASS',
    'scss': 'SCSS',
    'tailwind': 'Tailwind CSS',
    'bootstrap': 'Bootstrap',
    'rest': 'REST API',
    'restful': 'REST API',
    'graphql': 'GraphQL',
    'api': 'API Development',
    'sql': 'SQL',
    'nosql': 'NoSQL',
    'jenkins': 'Jenkins',
    'ci/cd': 'CI/CD',
    'terraform': 'Terraform',
    'ansible': 'Ansible',
    'linux': 'Linux',
    'ubuntu': 'Linux',
    'centos': 'Linux',
    'bash': 'Bash',
    'shell': 'Shell Scripting',
    'agile': 'Agile',
    'scrum': 'Scrum',
    'jira': 'JIRA',
    'confluence': 'Confluence',
}


def load_models():
    """Load spaCy and sentence-transformers models"""
    global nlp, encoder
    if nlp is None:
        logger.info("Loading spaCy model...")
        nlp = spacy.load('en_core_web_md')
    if encoder is None:
        logger.info("Loading sentence-transformers model...")
        encoder = SentenceTransformer('all-MiniLM-L6-v2')
    return nlp, encoder


def normalize_skill(skill_name):
    """Normalize skill name using mapping dictionary"""
    skill_lower = skill_name.lower().strip()
    return SKILL_MAPPINGS.get(skill_lower, skill_name.title())


def download_file(url):
    """Download file from Cloudinary using authenticated signed URL."""
    import cloudinary
    import cloudinary.utils
    from django.conf import settings

    # Configure cloudinary
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
        api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
        api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
    )

    # Extract public_id from URL
    # URL format: https://res.cloudinary.com/<cloud>/raw/upload/v1234/skillmap/cvs/file.pdf
    if '/upload/' in url:
        after_upload = url.split('/upload/')[1]
        # Remove version prefix like v1780558622/
        if after_upload.startswith('v') and '/' in after_upload:
            parts = after_upload.split('/', 1)
            if parts[0][1:].isdigit():
                after_upload = parts[1]
        public_id = after_upload
    else:
        public_id = url

    # Generate signed URL for authenticated download
    signed_url, _ = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type='raw',
        sign_url=True,
        type='upload',
        api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
        api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
    )

    response = requests.get(signed_url, timeout=30)
    response.raise_for_status()

    # Save to a temp file and return the path
    suffix = '.pdf' if url.endswith('.pdf') else '.docx'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(response.content)
        return tmp.name


def extract_text_from_pdf(file_path):
    """Extract text from PDF using pdfplumber"""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def extract_text_from_docx(file_path):
    """Extract text from DOCX using python-docx"""
    doc = Document(file_path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text


def extract_text_from_cv(file_url):
    """Extract text from CV file (PDF or DOCX)"""
    temp_file = download_file(file_url)

    try:
        if temp_file.endswith('.pdf'):
            text = extract_text_from_pdf(temp_file)
        elif temp_file.endswith('.docx'):
            text = extract_text_from_docx(temp_file)
        else:
            raise ValueError("Unsupported file format")

        return text
    finally:
        # Cleanup temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def extract_skills_from_text(text):
    """Extract skills from text using keyword matching only."""
    
    TECH_KEYWORDS = {
        # Languages
        'python', 'javascript', 'typescript', 'java', 'c#', 'c++', 'php',
        'dart', 'kotlin', 'swift', 'rust', 'go', 'scala', 'ruby',
        # Frontend
        'react', 'react.js', 'reactjs', 'vue', 'vue.js', 'angular',
        'next.js', 'nextjs', 'nuxt', 'svelte', 'tailwind', 'bootstrap',
        'html', 'css', 'sass', 'scss', 'redux', 'shadcn',
        # Backend
        'node.js', 'nodejs', 'express', 'django', 'flask', 'fastapi',
        'spring', 'laravel', 'nestjs', 'graphql', 'rest api',
        # Databases
        'postgresql', 'mysql', 'mongodb', 'redis', 'sqlite', 'elasticsearch',
        'firebase', 'supabase', 'dynamodb', 'cassandra',
        # DevOps / Cloud
        'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'linux',
        'nginx', 'ci/cd', 'jenkins', 'github actions', 'terraform',
        'ansible', 'heroku', 'vercel', 'netlify',
        # Tools
        'git', 'github', 'gitlab', 'jira', 'figma', 'postman',
        'vs code', 'webpack', 'vite',
        # AI / ML
        'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
        'celery', 'spacy', 'sentence-transformers', 'pgvector',
        'langchain', 'openai', 'groq',
        # Concepts
        'rest', 'microservices', 'agile', 'scrum', 'tdd',
        'jwt', 'oauth', 'graphql', 'websocket', 'sql', 'nosql',
        'cloudinary', 'stripe',
    }

    SKILL_DISPLAY = {
        'react': 'React.js', 'reactjs': 'React.js', 'react.js': 'React.js',
        'vue': 'Vue.js', 'vue.js': 'Vue.js',
        'node.js': 'Node.js', 'nodejs': 'Node.js',
        'next.js': 'Next.js', 'nextjs': 'Next.js',
        'postgresql': 'PostgreSQL', 'mongodb': 'MongoDB',
        'javascript': 'JavaScript', 'typescript': 'TypeScript',
        'python': 'Python', 'django': 'Django', 'flask': 'Flask',
        'fastapi': 'FastAPI', 'docker': 'Docker', 'kubernetes': 'Kubernetes',
        'aws': 'AWS', 'azure': 'Azure', 'gcp': 'Google Cloud',
        'git': 'Git', 'github': 'GitHub', 'gitlab': 'GitLab',
        'css': 'CSS', 'html': 'HTML', 'sass': 'SASS', 'scss': 'SCSS',
        'tailwind': 'Tailwind CSS', 'bootstrap': 'Bootstrap',
        'redis': 'Redis', 'linux': 'Linux', 'nginx': 'Nginx',
        'ci/cd': 'CI/CD', 'rest api': 'REST API', 'rest': 'REST API',
        'graphql': 'GraphQL', 'sql': 'SQL', 'nosql': 'NoSQL',
        'agile': 'Agile', 'scrum': 'Scrum', 'jira': 'JIRA',
        'figma': 'Figma', 'postman': 'Postman', 'celery': 'Celery',
        'redux': 'Redux', 'jwt': 'JWT', 'cloudinary': 'Cloudinary',
        'express': 'Express', 'nestjs': 'NestJS', 'java': 'Java',
        'kotlin': 'Kotlin', 'swift': 'Swift', 'php': 'PHP',
        'laravel': 'Laravel', 'c#': 'C#', 'c++': 'C++',
        'flutter': 'Flutter', 'dart': 'Dart', 'rust': 'Rust',
        'go': 'Go', 'scala': 'Scala', 'ruby': 'Ruby',
        'shadcn': 'Shadcn UI', 'pgvector': 'pgvector',
        'spacy': 'spaCy', 'groq': 'Groq API',
        'sentence-transformers': 'sentence-transformers',
        'github actions': 'GitHub Actions',
        'vs code': 'VS Code', 'webpack': 'Webpack', 'vite': 'Vite',
        'microservices': 'Microservices', 'websocket': 'WebSocket',
        'oauth': 'OAuth', 'tdd': 'TDD', 'stripe': 'Stripe',
        'terraform': 'Terraform', 'ansible': 'Ansible',
        'jenkins': 'Jenkins', 'vercel': 'Vercel', 'netlify': 'Netlify',
        'elasticsearch': 'Elasticsearch', 'firebase': 'Firebase',
        'pandas': 'Pandas', 'numpy': 'NumPy',
        'tensorflow': 'TensorFlow', 'pytorch': 'PyTorch',
        'scikit-learn': 'scikit-learn', 'langchain': 'LangChain',
    }

    text_lower = text.lower()
    found = {}

    for keyword in TECH_KEYWORDS:
        # Word boundary check to avoid partial matches
        import re
        pattern = r'(?<![a-zA-Z0-9\-])' + re.escape(keyword) + r'(?![a-zA-Z0-9\-])'
        if re.search(pattern, text_lower):
            display = SKILL_DISPLAY.get(keyword, keyword.title())
            found[display] = True

    return list(found.keys())


def vectorize_skills(skills):
    """Convert skills to vectors using sentence-transformers"""
    _, encoder_model = load_models()

    skill_data = []
    for skill in skills:
        normalized = normalize_skill(skill)
        vector = encoder_model.encode(normalized)

        skill_data.append({
            'skill_name': skill,
            'normalized_name': normalized,
            'skill_vector': vector.tolist(),
            'confidence_score': 1.0
        })

    return skill_data


def parse_cv(file_url, is_local=False):
    """
    Main CV parsing pipeline.
    Args:
        file_url: Cloudinary URL or local file path
        is_local: If True, treat file_url as a local file path (skip download)
    Returns: dict with extracted data
    """
    logger.info(f"Starting CV parsing for: {file_url}")

    # Extract text
    if is_local:
        # File is already on disk — parse directly
        if file_url.endswith('.pdf'):
            text = extract_text_from_pdf(file_url)
        elif file_url.endswith('.docx'):
            text = extract_text_from_docx(file_url)
        else:
            raise ValueError("Unsupported file format")
    else:
        text = extract_text_from_cv(file_url)
    logger.info(f"Extracted {len(text)} characters from CV")

    # Extract skills
    skills = extract_skills_from_text(text)
    logger.info(f"Found {len(skills)} potential skills")

    # Vectorize skills
    skill_data = vectorize_skills(skills)
    logger.info(f"Vectorized {len(skill_data)} skills")

    return {
        'skills': skill_data,
        'raw_text': text[:1000],  # Store first 1000 chars for reference
    }