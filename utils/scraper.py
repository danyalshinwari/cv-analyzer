import requests
from bs4 import BeautifulSoup
import re

def scrape_job_description(url: str) -> str:
    """
    Extracts job description text from common job board URLs.
    Supports LinkedIn, Indeed (basic), and general HTML pages.
    """
    if not url.startswith(('http://', 'https://')):
        return "Error: Invalid URL format."

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Job Board Specific Selectors
        content = ""
        
        if "linkedin.com" in url:
            # LinkedIn specific selectors for descriptions
            jd_div = soup.find('div', class_='description__text') or \
                     soup.find('div', class_='show-more-less-html__markup') or \
                     soup.find('section', class_='description')
            if jd_div:
                content = jd_div.get_text(separator='\n')
        
        elif "indeed.com" in url:
            jd_div = soup.find('div', id='jobDescriptionText')
            if jd_div:
                content = jd_div.get_text(separator='\n')

        # Fallback for generic job boards
        if not content:
            # Look for common ID or class names related to job descriptions
            common_selectors = ['job-description', 'description', 'job-details', 'job_description']
            for sel in common_selectors:
                found = soup.find(id=re.compile(sel, re.I)) or soup.find(class_=re.compile(sel, re.I))
                if found:
                    content = found.get_text(separator='\n')
                    break
        
        # Final fallback: text of the body with basic cleanup
        if not content:
            content = soup.body.get_text(separator='\n') if soup.body else soup.get_text(separator='\n')

        # Cleanup whitespace
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        return '\n'.join(lines)

    except Exception as e:
        return f"Error scraping URL: {e}"
