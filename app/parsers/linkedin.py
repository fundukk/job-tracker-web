#!/usr/bin/env python3
"""
LinkedIn job parser.
Extracts job information from LinkedIn job postings.
"""
import logging
import re
from bs4 import BeautifulSoup
from datetime import date

logger = logging.getLogger(__name__)


def parse(html: str, job_url: str) -> dict:
    """
    Parse LinkedIn job posting HTML.
    
    Args:
        html: Raw HTML content of the job page
        job_url: URL of the job posting
        
    Returns:
        Standardized job_data dict with all fields:
        - title: Job title
        - company: Company name
        - location: Job location (City, State format)
        - salary: Salary range if available
        - job_type: Full-time, Part-time, Internship, etc.
        - remote: Remote, Hybrid, or On-site
        - platform: "LinkedIn"
        - url: Original job URL
        - status: "Not applied"
        - notes: Any parsing errors or additional notes
    """
    # Initialize result with empty defaults
    job_data = {
        "date_added": date.today().isoformat(),
        "platform": "LinkedIn",
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
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract title from og:title meta tag
        try:
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title_text = og_title.get("content").strip()
                # LinkedIn format is usually "Title - Company | LinkedIn"
                if " - " in title_text:
                    parts = title_text.split(" - ", 1)
                    job_data["title"] = parts[0].strip()
                    if " | " in parts[1]:
                        job_data["company"] = parts[1].split(" | ")[0].strip()
                    else:
                        job_data["company"] = parts[1].strip()
                else:
                    job_data["title"] = title_text.split(" | ")[0].strip()
                
                logger.debug(f"Extracted title: {job_data['title']}, company: {job_data['company']}")
        
        except Exception as e:
            logger.warning(f"Failed to extract from og:title: {str(e)}")
        
        # Fallback to h1 for title if not found
        if not job_data["title"]:
            try:
                h1 = soup.find("h1")
                if h1:
                    job_data["title"] = h1.get_text(strip=True)
                    logger.debug(f"Extracted title from h1: {job_data['title']}")
            except Exception as e:
                logger.warning(f"Failed to extract from h1: {str(e)}")
        
        # Extract body text for additional parsing
        body_text = soup.get_text(" ", strip=True)
        body_lower = body_text.lower()
        
        # Extract location (City, State format)
        try:
            loc_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})', body_text)
            if loc_match:
                job_data["location"] = loc_match.group(1)
                logger.debug(f"Extracted location: {job_data['location']}")
        except Exception as e:
            logger.warning(f"Failed to extract location: {str(e)}")
        
        # Extract salary
        try:
            salary_pattern = r'\$\s*[\d,]+(?:\.\d+)?(?:\s*k)?(?:\s*[-–]\s*\$?\s*[\d,]+(?:\.\d+)?(?:\s*k)?)?(?:\s*(?:/hr|/hour|per hour|/yr|/year|per year))?'
            salary_match = re.search(salary_pattern, body_text, re.IGNORECASE)
            if salary_match:
                job_data["salary"] = salary_match.group(0).strip()
                logger.debug(f"Extracted salary: {job_data['salary']}")
        except Exception as e:
            logger.warning(f"Failed to extract salary: {str(e)}")
        
        # Detect remote/hybrid/on-site
        try:
            if "remote" in body_lower:
                job_data["remote"] = "Remote"
            elif "hybrid" in body_lower:
                job_data["remote"] = "Hybrid"
            else:
                job_data["remote"] = "On-site"
            logger.debug(f"Detected remote type: {job_data['remote']}")
        except Exception as e:
            logger.warning(f"Failed to detect remote type: {str(e)}")
        
        # Detect job type
        try:
            if any(word in body_lower for word in ["internship", "intern position"]):
                job_data["job_type"] = "Internship"
            elif "full-time" in body_lower or "full time" in body_lower:
                job_data["job_type"] = "Full-time"
            elif "part-time" in body_lower or "part time" in body_lower:
                job_data["job_type"] = "Part-time"
            elif "contract" in body_lower:
                job_data["job_type"] = "Contract"
            logger.debug(f"Detected job type: {job_data['job_type']}")
        except Exception as e:
            logger.warning(f"Failed to detect job type: {str(e)}")
    
    except Exception as e:
        # On error, return partial data with notes about the error
        error_msg = f"Parsing error: {str(e)}"
        logger.error(f"LinkedIn parser error for {job_url}: {error_msg}", exc_info=True)
        job_data["notes"] = error_msg
    
    logger.info(f"Parsed LinkedIn job: {job_data['title']} at {job_data['company']}")
    return job_data
