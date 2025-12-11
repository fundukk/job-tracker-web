#!/usr/bin/env python3
"""
Handshake job parser.
Extracts job information from Handshake job postings.
Supports both HTML parsing and text-based parsing.
"""
import logging
import re
from bs4 import BeautifulSoup
from datetime import date

logger = logging.getLogger(__name__)

# Salary time markers pattern
TIME_MARKERS_PATTERN = r"(?:/yr|/year|per year|yr|/mo|/month|per month|month|mo|/hr|/hour|per hour|hr)\b"


def parse(html: str, job_url: str) -> dict:
    """
    Parse Handshake job posting HTML.
    
    Args:
        html: Raw HTML content of the job page
        job_url: URL of the job posting
        
    Returns:
        Standardized job_data dict with all fields
    """
    # Initialize result with empty defaults
    job_data = {
        "date_added": date.today().isoformat(),
        "platform": "Handshake",
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
                job_data["title"] = og_title.get("content").strip()
                logger.debug(f"Extracted title: {job_data['title']}")
            else:
                # Fallback to h1
                h1 = soup.find("h1")
                if h1:
                    job_data["title"] = h1.get_text(strip=True)
                    logger.debug(f"Extracted title from h1: {job_data['title']}")
        except Exception as e:
            logger.warning(f"Failed to extract title: {str(e)}")
        
        # Extract company from og:site_name or specific divs
        try:
            company_meta = soup.find("meta", property="og:site_name")
            if company_meta and company_meta.get("content"):
                job_data["company"] = company_meta.get("content").strip()
                logger.debug(f"Extracted company: {job_data['company']}")
        except Exception as e:
            logger.warning(f"Failed to extract company: {str(e)}")
        
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
            salary_pattern = rf'\$\s*[\d,]+(?:\.\d+)?(?:\s*k)?(?:\s*[-–]\s*\$?\s*[\d,]+(?:\.\d+)?(?:\s*k)?)?(?:\s*{TIME_MARKERS_PATTERN})?'
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
        logger.error(f"Handshake HTML parser error for {job_url}: {error_msg}", exc_info=True)
        job_data["notes"] = error_msg
    
    logger.info(f"Parsed Handshake job: {job_data['title']} at {job_data['company']}")
    return job_data


def parse_text(text: str, job_url: str) -> dict:
    """
    Parse copied text from Handshake job page (alternative to HTML parsing).
    This is used when the user copies and pastes text from a Handshake job.
    
    Args:
        text: Copied text from Handshake job page
        job_url: URL of the job posting
        
    Returns:
        Standardized job_data dict with all fields
    """
    logger.info(f"Parsing Handshake text for URL: {job_url}")
    
    position = ""
    company = ""
    location = ""
    salary = ""
    job_type = ""
    remote_hint = ""
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text_lower = text.lower()
    
    # Noise patterns to skip
    noise_patterns = [
        r'^\d+\s+profile\s+views?$',
        r'^skip to',
        r'^menu$',
        r'^navigation$',
        r'^home$',
        r'^jobs$',
        r'^sign in$',
        r'^log in$',
        r'^search$',
        r'^get the app$',
        r'^save$',
        r'^share$',
        r'^apply$',
        r'^follow$',
        r'in the past \d+ days?$',
        r'^posted',
        r'^apply by',
        r'^={3,}$',
    ]
    
    def is_noise(line: str) -> bool:
        """Check if a line is noise/navigation."""
        if not line or len(line.strip()) == 0:
            return True
        line_lower = line.lower().strip()
        if line_lower.isdigit():
            return True
        return any(re.match(pattern, line_lower, re.IGNORECASE) for pattern in noise_patterns)
    
    # Look for "Company logo" pattern to extract company name
    logo_line_idx = -1
    for i, line in enumerate(lines):
        if "logo" in line.lower():
            logo_line_idx = i
            logo_match = re.match(r'^(.+?)\s+logo\s*$', line, re.IGNORECASE)
            if logo_match and not company:
                potential_company = logo_match.group(1).strip()
                if not is_noise(potential_company) and len(potential_company) > 2:
                    company = potential_company
                    logger.debug(f"Extracted company from logo line: {company}")
            break
    
    # If we found a logo line, position is usually the SECOND meaningful line after logo
    if logo_line_idx >= 0 and not position:
        start_idx = logo_line_idx + 1
        seen_first_text = False
        
        for i in range(start_idx, min(start_idx + 8, len(lines))):
            line = lines[i].strip()
            lower = line.lower()
            
            if re.match(r"^posted", lower) or re.search(r"\d+\s+days?\s+ago", lower) or "apply by" in lower:
                break
            
            if company and lower == company.lower():
                continue
            
            if is_noise(line) or len(line) <= 3 or line.isupper():
                continue
            
            if not seen_first_text:
                seen_first_text = True
                continue
            
            position = line
            logger.debug(f"Extracted position from text: {position}")
            break
    
    # Try to find labeled fields as fallback
    i = 0
    while i < len(lines) and (not position or not company):
        line_lower = lines[i].lower()
        
        if not position and line_lower == "position" and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if not is_noise(next_line):
                position = next_line
                logger.debug(f"Extracted position from labeled field: {position}")
                i += 2
                continue
        
        elif not company and line_lower == "company" and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if not is_noise(next_line):
                company = next_line
                logger.debug(f"Extracted company from labeled field: {company}")
                i += 2
                continue
        
        elif line_lower == "location" and i + 1 < len(lines):
            location = lines[i + 1].strip()
            logger.debug(f"Extracted location from labeled field: {location}")
            i += 2
            continue
        
        elif line_lower == "salary" and i + 1 < len(lines):
            salary = lines[i + 1].strip()
            logger.debug(f"Extracted salary from labeled field: {salary}")
            i += 2
            continue
        
        elif line_lower in ["jobtype", "job type", "employment type"] and i + 1 < len(lines):
            job_type = lines[i + 1].strip()
            logger.debug(f"Extracted job type from labeled field: {job_type}")
            i += 2
            continue
        
        elif line_lower == "remote" and i + 1 < len(lines):
            remote_hint = lines[i + 1].strip()
            logger.debug(f"Extracted remote hint from labeled field: {remote_hint}")
            i += 2
            continue
        
        i += 1
    
    # Fallback: if position or company still empty, find meaningful lines
    if not position or not company:
        label_words = {"position", "company", "location", "salary", "jobtype", "job type", "remote", "employment type"}
        skip_keywords = {"profile", "view", "follow"}
        meaningful_lines = []
        
        for line in lines:
            if (not is_noise(line) 
                and line.lower() not in label_words 
                and len(line) > 5
                and not any(kw in line.lower() for kw in skip_keywords)
                and not re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}$', line)):
                meaningful_lines.append(line)
        
        if not position and meaningful_lines:
            position = meaningful_lines[0]
            logger.debug(f"Extracted position from meaningful lines: {position}")
        
        if not company and len(meaningful_lines) > 1:
            company = meaningful_lines[1]
            logger.debug(f"Extracted company from meaningful lines: {company}")
    
    # Fallback: Location pattern matching
    if not location:
        loc_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})', text)
        if loc_match:
            location = loc_match.group(1)
            logger.debug(f"Extracted location from pattern: {location}")
    
    # Salary
    if not salary:
        salary_match = re.search(
            rf"\$\s*[\d,]+(?:\.\d+)?\s*(?:k|K)?(?:\s*[-–]\s*\$?\s*[\d,]+(?:\.\d+)?\s*(?:k|K)?)?\s*{TIME_MARKERS_PATTERN}",
            text,
            re.IGNORECASE,
        )
        if salary_match:
            salary = salary_match.group(0).strip()
            logger.debug(f"Extracted salary from pattern: {salary}")
    
    # Remote/Hybrid
    if not remote_hint:
        if "remote" in text_lower:
            remote_hint = "Remote"
        elif "hybrid" in text_lower:
            remote_hint = "Hybrid"
        logger.debug(f"Detected remote type: {remote_hint}")
    
    # Job type
    if not job_type:
        if any(word in text_lower for word in ["internship", "intern position"]):
            job_type = "Internship"
        elif "full-time" in text_lower or "full time" in text_lower:
            job_type = "Full-time"
        elif "part-time" in text_lower or "part time" in text_lower:
            job_type = "Part-time"
        elif "contract" in text_lower:
            job_type = "Contract"
        logger.debug(f"Detected job type: {job_type}")
    
    logger.info(f"Parsed Handshake text: {position} at {company}")
    
    return {
        "date_added": date.today().isoformat(),
        "platform": "Handshake",
        "company": company,
        "title": position,
        "location": location,
        "salary": salary,
        "job_type": job_type,
        "remote": remote_hint,
        "url": job_url,
        "status": "Not applied",
        "notes": "",
    }
