#!/usr/bin/env python3
"""Job scraping and parsing logic."""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

# ============================================================================
# FEATURE FLAG: Toggle between old and new parser system
# ============================================================================
# Set to True to use the new modular parser system (core/parsers/)
# Set to False to use the legacy placeholder parser (safe fallback)
USE_NEW_PARSER = False

# Only import new parsers if flag is enabled
if USE_NEW_PARSER:
    from core.parsers import linkedin, handshake, generic


def fetch_job_html(job_url: str) -> str:
    """Fetch HTML via requests."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    response = requests.get(job_url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.text


def infer_source(url: str) -> str:
    """Infer job source from URL."""
    url_lower = url.lower()
    if "linkedin.com" in url_lower:
        return "LinkedIn"
    if "indeed.com" in url_lower:
        return "Indeed"
    if "glassdoor" in url_lower:
        return "Glassdoor"
    if "handshake.com" in url_lower or "joinhandshake.com" in url_lower:
        return "Handshake"
    return "Company / Other"


def parse_job_html(html: str, job_url: str) -> dict:
    """
    Parse job info using BeautifulSoup. Return a dict.
    
    Routes to appropriate parser based on USE_NEW_PARSER flag:
    - If True: Uses modular parsers (linkedin, handshake, generic)
    - If False: Uses legacy placeholder parser (current implementation)
    """
    # ========================================================================
    # NEW PARSER SYSTEM (Modular)
    # ========================================================================
    if USE_NEW_PARSER:
        domain = urlparse(job_url).netloc.lower()
        
        # Route to appropriate parser based on domain
        if "linkedin.com" in domain:
            return linkedin.parse(html, job_url)
        elif "joinhandshake.com" in domain or "handshake.com" in domain:
            return handshake.parse(html, job_url)
        else:
            return generic.parse(html, job_url)
    
    # ========================================================================
    # LEGACY PARSER (Placeholder)
    # ========================================================================
    soup = BeautifulSoup(html, "html.parser")
    
    # Placeholder parsing logic - extract basic info
    position = ""
    company = ""
    location = ""
    salary = ""
    job_type = ""
    remote = ""
    
    # Try to get title from og:title meta tag
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        position = og_title.get("content").strip()
    else:
        # Fallback to h1
        h1 = soup.find("h1")
        if h1:
            position = h1.get_text(strip=True)
    
    # Try to extract company from page
    body_text = soup.get_text(" ", strip=True)
    
    # Look for location pattern (City, State)
    loc_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})', body_text)
    if loc_match:
        location = loc_match.group(1)
    
    # Detect remote/hybrid
    body_lower = body_text.lower()
    if "remote" in body_lower:
        remote = "Remote"
    elif "hybrid" in body_lower:
        remote = "Hybrid"
    else:
        remote = "On-site"
    
    # Detect job type
    if any(word in body_lower for word in ["internship", "intern position"]):
        job_type = "Internship"
    elif "full-time" in body_lower or "full time" in body_lower:
        job_type = "Full-time"
    elif "part-time" in body_lower or "part time" in body_lower:
        job_type = "Part-time"
    elif "contract" in body_lower:
        job_type = "Contract"
    
    return {
        "position": position,
        "company": company,
        "location": location,
        "salary": salary,
        "job_type": job_type,
        "remote": remote,
        "link": job_url,
        "source": infer_source(job_url),
        "status": "Applied",
        "notes": "",
    }


def process_job_url(job_url: str) -> dict:
    """Fetch → parse → return dict."""
    html = fetch_job_html(job_url)
    job_data = parse_job_html(html, job_url)
    return job_data
