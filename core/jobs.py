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


def parse_handshake_text_wrapper(text: str, job_url: str) -> dict:
    """
    Wrapper for parse_handshake_text from CLI.
    Returns standardized job_data dict for web app.
    """
    import sys
    from pathlib import Path
    
    # Add parent directory to path to import job_tracker
    parent_dir = Path(__file__).resolve().parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    from job_tracker import parse_handshake_text
    
    position, company, location, salary, job_type, remote_hint = parse_handshake_text(text)
    
    return {
        "position": position,
        "company": company,
        "location": location,
        "salary": salary,
        "job_type": job_type,
        "remote": remote_hint,
        "link": job_url,
        "source": "Handshake",
        "status": "Applied",
        "notes": "",
    }


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


def normalize_linkedin_url(url: str) -> str:
    """
    Normalize LinkedIn URLs.
    Turn URLs like .../jobs/collections/recommended/?currentJobId=XXXX
    into .../jobs/view/XXXX/
    """
    url = url.strip()
    if "linkedin" not in url.lower():
        return url
    
    if "/jobs/view/" in url:
        return url
    
    if "currentJobId=" in url:
        try:
            part = url.split("currentJobId=", 1)[1]
            job_id = "".join(c for c in part if c.isdigit())
            if job_id:
                return f"https://www.linkedin.com/jobs/view/{job_id}/"
        except Exception:
            pass
    
    return url


def validate_job_url(url: str) -> tuple[bool, str]:
    """
    Validate job URL.
    Returns (is_valid, error_message).
    """
    url = url.strip()
    if not url:
        return False, "Job URL is required."
    if not url.startswith(("http://", "https://")):
        return False, "URL must start with http:// or https://"
    return True, ""


def parse_linkedin_job(html: str, job_url: str) -> dict:
    """Parse LinkedIn job page - migrated from CLI script."""
    # Normalize URL first
    job_url = normalize_linkedin_url(job_url)
    
    soup = BeautifulSoup(html, "html.parser")
    
    position = ""
    company = ""
    location = ""
    salary = ""
    job_type = ""
    remote = ""
    
    # Try to get title from og:title meta tag first
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title_text = og_title.get("content").strip()
    else:
        h1 = soup.find("h1")
        title_text = h1.get_text(strip=True) if h1 else ""

    if title_text:
        # Remove trailing "| LinkedIn" if present
        for sep in [" | LinkedIn", " |"]:
            if sep in title_text:
                title_text = title_text.split(sep, 1)[0].strip()
                break

        # Pattern 1: "Company hiring Position in City, ST"
        lower_title = title_text.lower()
        if " hiring " in lower_title:
            try:
                idx_hiring = lower_title.index(" hiring ")
                company = title_text[:idx_hiring].strip()
                rest = title_text[idx_hiring + len(" hiring "):]
                
                # Look for location after "in"
                if " in " in rest.lower():
                    idx_in = rest.lower().index(" in ")
                    position = rest[:idx_in].strip()
                    location = rest[idx_in + 4:].strip()
                else:
                    position = rest.strip()
            except Exception:
                pass
        
        # Pattern 2: "Position – Company – City, ST" (fallback if pattern 1 didn't work)
        if not company or not position:
            separators = ["–", "-"]
            for sep in separators:
                if sep in title_text and title_text.count(sep) >= 1:
                    parts = [p.strip() for p in title_text.split(sep)]
                    if len(parts) >= 1 and not position:
                        position = parts[0]
                    if len(parts) >= 2 and not company:
                        company = parts[1]
                    if len(parts) >= 3 and not location:
                        location = parts[2]
                    break

    # Gather visible text for analysis
    body = soup.get_text(" ", strip=True)
    
    # Salary extraction - look for patterns with time markers
    time_markers = r"(?:/yr|/year|per year|yr|/mo|/month|per month|month|mo|/hr|/hour|per hour|hr)\b"
    
    # 1) $-based patterns with time markers
    salary_match = re.search(
        rf"\$\s*[\d,]+(?:\.\d+)?\s*(?:k|K)?(?:\s*[-–]\s*\$?\s*[\d,]+(?:\.\d+)?\s*(?:k|K)?)?\s*{time_markers}",
        body,
        re.IGNORECASE,
    )
    
    if salary_match:
        salary = salary_match.group(0).strip()
    else:
        # 2) k-style without $ but with time marker
        k_match = re.search(
            rf"[\d,]+(?:\s*[-–]\s*[\d,]+)?\s*[kK]\s*{time_markers}",
            body,
            re.IGNORECASE,
        )
        if k_match:
            salary = k_match.group(0).strip()
    
    # Remote detection
    body_lower = body.lower()
    if "remote" in body_lower:
        remote = "Remote"
    elif "hybrid" in body_lower:
        remote = "Hybrid"
    else:
        remote = "On-site"
    
    # Job type detection
    if any(word in body_lower for word in ["internship", "intern position", "intern -"]):
        job_type = "Internship"
    else:
        for t in ["Full-time", "Part-time", "Contract", "Temporary"]:
            if t.lower() in body_lower:
                job_type = t
                break
    
    return {
        "position": position,
        "company": company,
        "location": location,
        "salary": salary,
        "job_type": job_type,
        "remote": remote,
        "link": job_url,
        "source": "LinkedIn",
        "status": "Applied",
        "notes": "",
    }


def parse_generic_job(html: str, job_url: str) -> dict:
    """Parse generic job page - migrated from CLI script."""
    soup = BeautifulSoup(html, "html.parser")
    
    position = ""
    company = ""
    location = ""
    
    # Try to get position from h1
    h1 = soup.find("h1")
    if h1:
        position = h1.get_text(strip=True)
    
    # Extract company from domain
    try:
        company = job_url.split("//", 1)[-1].split("/", 1)[0]
        # Clean up domain
        company = company.replace("www.", "").split(".")[0].title()
    except Exception:
        pass
    
    # Try to find location
    body = soup.get_text(" ", strip=True)
    loc_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})', body)
    if loc_match:
        location = loc_match.group(1)
    
    # Detect remote/hybrid
    body_lower = body.lower()
    remote = ""
    if "remote" in body_lower:
        remote = "Remote"
    elif "hybrid" in body_lower:
        remote = "Hybrid"
    else:
        remote = "On-site"
    
    # Detect job type
    job_type = ""
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
        "salary": "",
        "job_type": job_type,
        "remote": remote,
        "link": job_url,
        "source": infer_source(job_url),
        "status": "Applied",
        "notes": "",
    }


def parse_handshake_job(html: str, job_url: str) -> dict:
    """Parse Handshake job page - migrated from CLI script."""
    soup = BeautifulSoup(html, "html.parser")
    
    position = ""
    company = ""
    location = ""
    salary = ""
    job_type = ""
    remote = ""
    
    # Get title from og:title or h1
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        position = og_title.get("content").strip()
    else:
        h1 = soup.find("h1")
        if h1:
            position = h1.get_text(strip=True)
    
    # Try to find company name
    company_meta = soup.find("meta", property="og:site_name")
    if company_meta and company_meta.get("content"):
        company = company_meta.get("content").strip()
    
    # Get body text for analysis
    body = soup.get_text(" ", strip=True)
    
    # Look for location
    loc_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})', body)
    if loc_match:
        location = loc_match.group(1)
    
    # Check for remote/hybrid
    body_lower = body.lower()
    if "remote" in body_lower:
        remote = "Remote"
    elif "hybrid" in body_lower:
        remote = "Hybrid"
    else:
        remote = "On-site"
    
    # Check for job type
    if any(word in body_lower for word in ["internship", "intern position"]):
        job_type = "Internship"
    elif "full-time" in body_lower or "full time" in body_lower:
        job_type = "Full-time"
    elif "part-time" in body_lower or "part time" in body_lower:
        job_type = "Part-time"
    elif "contract" in body_lower:
        job_type = "Contract"
    
    # Look for salary
    time_markers = r"(?:/yr|/year|per year|yr|/mo|/month|per month|month|mo|/hr|/hour|per hour|hr)\b"
    salary_match = re.search(
        rf"\$\s*[\d,]+(?:\.\d+)?\s*(?:k|K)?(?:\s*[-–]\s*\$?\s*[\d,]+(?:\.\d+)?\s*(?:k|K)?)?\s*{time_markers}",
        body,
        re.IGNORECASE,
    )
    if salary_match:
        salary = salary_match.group(0).strip()
    
    return {
        "position": position,
        "company": company,
        "location": location,
        "salary": salary,
        "job_type": job_type,
        "remote": remote,
        "link": job_url,
        "source": "Handshake",
        "status": "Applied",
        "notes": "",
    }


def parse_job_html(html: str, job_url: str) -> dict:
    """
    Parse job info using BeautifulSoup. Routes to appropriate parser.
    """
    url_lower = job_url.lower()
    
    # Route to appropriate parser based on URL
    if "linkedin.com" in url_lower:
        return parse_linkedin_job(html, job_url)
    elif "handshake.com" in url_lower or "joinhandshake.com" in url_lower:
        return parse_handshake_job(html, job_url)
    else:
        return parse_generic_job(html, job_url)


def process_job_url(job_url: str) -> dict:
    """Fetch → parse → return dict."""
    html = fetch_job_html(job_url)
    job_data = parse_job_html(html, job_url)
    return job_data
