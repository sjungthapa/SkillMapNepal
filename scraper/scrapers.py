"""Web scrapers for job sites using Playwright"""
import asyncio
from playwright.async_api import async_playwright
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


async def scrape_merojob():
    """Scrape tech jobs from Merojob.com"""
    jobs = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to IT & Telecom category
            url = "https://merojob.com/category/it-telecom/"
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for job listings to load
            await page.wait_for_selector('.card', timeout=10000)
            
            # Extract job listings
            job_cards = await page.query_selector_all('.card')
            
            for card in job_cards[:50]:  # Limit to 50 jobs per run
                try:
                    title_elem = await card.query_selector('h2.title a')
                    company_elem = await card.query_selector('.company-name')
                    location_elem = await card.query_selector('.location')
                    
                    if title_elem:
                        title = await title_elem.inner_text()
                        href = await title_elem.get_attribute('href')
                        job_url = urljoin(url, href) if href else ''
                        
                        company = await company_elem.inner_text() if company_elem else 'Unknown'
                        location = await location_elem.inner_text() if location_elem else 'Nepal'
                        
                        # Visit job details page to extract skills
                        skills = await extract_skills_from_job_page(page, job_url)
                        
                        jobs.append({
                            'title': title.strip(),
                            'company': company.strip(),
                            'source': 'merojob',
                            'source_url': job_url,
                            'district': location.strip(),
                            'skills': skills
                        })
                        
                        # Small delay to avoid overwhelming the server
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logger.warning(f"Error extracting job card: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Merojob: {e}")
            
        finally:
            await browser.close()
    
    logger.info(f"Scraped {len(jobs)} jobs from Merojob")
    return jobs


async def scrape_kumarijob():
    """Scrape tech jobs from Kumarijob.com"""
    jobs = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to IT jobs section
            url = "https://kumarijob.com/jobs/it-telecommunication"
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for job listings
            await page.wait_for_selector('.job-item', timeout=10000)
            
            # Extract job listings
            job_items = await page.query_selector_all('.job-item')
            
            for item in job_items[:50]:  # Limit to 50 jobs
                try:
                    title_elem = await item.query_selector('.job-title a')
                    company_elem = await item.query_selector('.company-name')
                    location_elem = await item.query_selector('.location')
                    
                    if title_elem:
                        title = await title_elem.inner_text()
                        href = await title_elem.get_attribute('href')
                        job_url = urljoin(url, href) if href else ''
                        
                        company = await company_elem.inner_text() if company_elem else 'Unknown'
                        location = await location_elem.inner_text() if location_elem else 'Nepal'
                        
                        # Visit job details page
                        skills = await extract_skills_from_job_page(page, job_url)
                        
                        jobs.append({
                            'title': title.strip(),
                            'company': company.strip(),
                            'source': 'kumarijob',
                            'source_url': job_url,
                            'district': location.strip(),
                            'skills': skills
                        })
                        
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logger.warning(f"Error extracting job item: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Kumarijob: {e}")
            
        finally:
            await browser.close()
    
    logger.info(f"Scraped {len(jobs)} jobs from Kumarijob")
    return jobs


async def extract_skills_from_job_page(page, job_url):
    """Extract skills from job details page"""
    skills = []
    
    if not job_url:
        return skills
    
    try:
        await page.goto(job_url, wait_until="networkidle", timeout=15000)
        
        # Extract all text from job description
        content = await page.inner_text('body')
        
        # Common tech skills to look for
        tech_skills = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue',
            'Node.js', 'Django', 'Flask', 'Spring Boot', 'FastAPI',
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
            'Git', 'GitHub', 'GitLab', 'JIRA', 'Agile', 'Scrum',
            'HTML', 'CSS', 'SASS', 'Tailwind', 'Bootstrap',
            'REST API', 'GraphQL', 'Microservices', 'CI/CD',
            'Linux', 'Bash', 'Terraform', 'Ansible', 'Jenkins',
            'Machine Learning', 'AI', 'Data Science', 'TensorFlow', 'PyTorch',
            '.NET', 'C#', 'C++', 'Go', 'Rust', 'PHP', 'Ruby', 'Laravel',
        ]
        
        # Check which skills are mentioned
        content_lower = content.lower()
        for skill in tech_skills:
            if skill.lower() in content_lower:
                skills.append(skill)
        
    except Exception as e:
        logger.warning(f"Error extracting skills from {job_url}: {e}")
    
    return skills


def scrape_merojob_sync():
    """Synchronous wrapper for scrape_merojob"""
    return asyncio.run(scrape_merojob())


def scrape_kumarijob_sync():
    """Synchronous wrapper for scrape_kumarijob"""
    return asyncio.run(scrape_kumarijob())
