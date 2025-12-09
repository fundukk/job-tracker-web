"""
Generic job parser.

Fallback parser for job postings from unknown or unsupported platforms.
Uses basic heuristics to extract common job information.
"""
from bs4 import BeautifulSoup
from datetime import date
import re


def parse(html: str, job_url: str) -> dict:
    """
    Parse generic job posting HTML using basic heuristics.
    
    Args:
        html: Raw HTML content of the job page
        job_url: URL of the job posting
        
    Returns:
        Standardized job_data dict with all fields
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Infer platform from URL
    domain = job_url.lower()
    if "indeed.com" in domain:
        platform = "Indeed"
    elif "glassdoor" in domain:
        platform = "Glassdoor"
    else:
        platform = "Other"
    
    # Initialize result with empty defaults
    job_data = {
        "date_added": date.today().isoformat(),
        "platform": platform,
        "company": "",
        "title": "",
        "location": "",
        "salary": "",
        "job_type": "",
        "remote": "",
        "url": job_url,
        "status": "Not applied",
        "notes": "",
    }
    
    try:
        # Try to extract title from og:title meta tag
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            job_data["title"] = og_title.get("content").strip()
        else:
            # Fallback to h1
            h1 = soup.find("h1")
            if h1:
                job_data["title"] = h1.get_text(strip=True)
        
        # Try to extract company from domain or page content
        if not job_data["company"]:
            # Extract from URL domain as last resort
            from urllib.parse import urlparse
            parsed = urlparse(job_url)
            domain_parts = parsed.netloc.split('.')
            if len(domain_parts) >= 2:
                job_data["company"] = domain_parts[-2].capitalize()
        
        # Extract body text for additional parsing
        body_text = soup.get_text(" ", strip=True)
        body_lower = body_text.lower()
        
        # Extract location (City, State format)
        loc_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})', body_text)
        if loc_match:
            job_data["location"] = loc_match.group(1)
        
        # Extract salary
        salary_pattern = r'\$\s*[\d,]+(?:\.\d+)?(?:\s*k)?(?:\s*[-–]\s*\$?\s*[\d,]+(?:\.\d+)?(?:\s*k)?)?(?:\s*(?:/hr|/hour|per hour|/yr|/year|per year))?'
        salary_match = re.search(salary_pattern, body_text, re.IGNORECASE)
        if salary_match:
            job_data["salary"] = salary_match.group(0).strip()
        
        # Detect remote/hybrid/on-site
        if "remote" in body_lower:
            job_data["remote"] = "Remote"
        elif "hybrid" in body_lower:
            job_data["remote"] = "Hybrid"
        else:
            job_data["remote"] = "On-site"
        
        # Detect job type
        if any(word in body_lower for word in ["internship", "intern position"]):
            job_data["job_type"] = "Internship"
        elif "full-time" in body_lower or "full time" in body_lower:
            job_data["job_type"] = "Full-time"
        elif "part-time" in body_lower or "part time" in body_lower:
            job_data["job_type"] = "Part-time"
        elif "contract" in body_lower:
            job_data["job_type"] = "Contract"
    
    except Exception as e:
        # On error, return partial data with notes about the error
        job_data["notes"] = f"Parsing error: {str(e)}"
    
    return job_data
