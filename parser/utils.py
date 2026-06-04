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
    """Download file from Cloudinary URL to temp file"""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    suffix = '.pdf' if 'pdf' in url.lower() else '.docx'
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(response.content)
    temp_file.close()
    
    return temp_file.name


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
    """Extract skills from text using spaCy NER and pattern matching"""
    nlp_model, _ = load_models()
    
    # Process text with spaCy
    doc = nlp_model(text)
    
    # Extract potential skills
    skills = set()
    
    # Known tech keywords that might not be caught by NER
    tech_keywords = [
        'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
        'node.js', 'django', 'flask', 'spring', 'fastapi', 'express',
        'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
        'git', 'github', 'gitlab', 'jira', 'agile', 'scrum',
        'html', 'css', 'sass', 'tailwind', 'bootstrap',
        'rest api', 'graphql', 'microservices', 'ci/cd',
        'linux', 'bash', 'terraform', 'ansible'
    ]
    
    # Check for tech keywords in text
    text_lower = text.lower()
    for keyword in tech_keywords:
        if keyword in text_lower:
            skills.add(keyword)
    
    # Extract noun chunks that might be skills
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.strip()
        if len(chunk_text) > 2 and len(chunk_text) < 30:
            # Filter out common non-skill words
            if chunk_text.lower() not in ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at']:
                skills.add(chunk_text)
    
    # Extract entities
    for ent in doc.ents:
        if ent.label_ in ['ORG', 'PRODUCT', 'LANGUAGE']:
            skills.add(ent.text)
    
    return list(skills)


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


def parse_cv(file_url):
    """
    Main CV parsing pipeline
    Returns: dict with extracted data
    """
    logger.info(f"Starting CV parsing for: {file_url}")
    
    # Extract text
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
