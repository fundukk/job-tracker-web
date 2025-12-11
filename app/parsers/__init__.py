#!/usr/bin/env python3
"""
Job parser modules.
Provides a unified interface for parsing job postings from different platforms.
"""
import logging
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Import individual parsers
from app.parsers import linkedin, handshake, generic

# Parser registry for routing URLs to appropriate parsers
PARSERS = {
    'linkedin.com': linkedin,
    'handshake.com': handshake,
    'joinhandshake.com': handshake,
}


def validate_job_url(url: str) -> tuple[bool, str]:
    """
    Validate that a URL is well-formed and potentially scrapable.
    
    Args:
        url: The job URL to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"
    
    url = url.strip()
    
    try:
        parsed = urlparse(url)
        
        if not parsed.scheme:
            return False, "URL must include http:// or https://"
        
        if parsed.scheme not in ('http', 'https'):
            return False, "URL must use http or https protocol"
        
        if not parsed.netloc:
            return False, "URL must include a domain name"
        
        return True, ""
    
    except Exception as e:
        logger.warning(f"URL validation error: {str(e)}")
        return False, f"Invalid URL format: {str(e)}"


def fetch_job_html(url: str, timeout: int = 10) -> str:
    """
    Fetch HTML content from a job URL.
    
    Args:
        url: Job posting URL
        timeout: Request timeout in seconds
        
    Returns:
        str: HTML content
        
    Raises:
        requests.RequestException: If the request fails
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                     'AppleWebKit/537.36 (KHTML, like Gecko) '
                     'Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        logger.info(f"Fetching job HTML from: {url}")
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        logger.info(f"Successfully fetched {len(response.text)} bytes")
        return response.text
    
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout fetching {url}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {str(e)}")
        raise


def detect_parser(url: str):
    """
    Detect which parser to use based on the URL.
    
    Args:
        url: Job posting URL
        
    Returns:
        module: Parser module (linkedin, handshake, or generic)
    """
    url_lower = url.lower()
    
    for domain, parser in PARSERS.items():
        if domain in url_lower:
            logger.info(f"Detected parser: {parser.__name__}")
            return parser
    
    logger.info("No specific parser detected, using generic parser")
    return generic


def parse_handshake_text_wrapper(text: str, job_url: str) -> dict:
    """
    Parse Handshake job from copied text (not HTML).
    This is a wrapper around the text-based Handshake parser.
    
    Args:
        text: Copied text from Handshake job page
        job_url: URL of the job posting
        
    Returns:
        dict: Standardized job data
    """
    try:
        logger.info(f"Parsing Handshake text for URL: {job_url}")
        job_data = handshake.parse_text(text, job_url)
        
        # Convert to expected format for the web app
        return {
            "position": job_data.get("title", ""),
            "company": job_data.get("company", ""),
            "location": job_data.get("location", ""),
            "salary": job_data.get("salary", ""),
            "job_type": job_data.get("job_type", ""),
            "remote": job_data.get("remote", ""),
            "link": job_url,
            "source": "Handshake",
            "status": "Applied",
            "notes": job_data.get("notes", ""),
        }
    
    except Exception as e:
        logger.error(f"Failed to parse Handshake text: {str(e)}", exc_info=True)
        raise


def process_job_url(job_url: str) -> dict:
    """
    Main entry point: fetch HTML, parse, and return job data.
    
    Args:
        job_url: URL of the job posting
        
    Returns:
        dict: Parsed job data with standardized fields
        
    Raises:
        requests.RequestException: If fetching fails
        Exception: If parsing fails
    """
    try:
        # Fetch HTML
        html = fetch_job_html(job_url)
        
        # Detect appropriate parser
        parser = detect_parser(job_url)
        
        # Parse with detected parser
        logger.info(f"Parsing job with {parser.__name__}")
        job_data = parser.parse(html, job_url)
        
        # Convert to expected format for the web app
        return {
            "position": job_data.get("title", ""),
            "company": job_data.get("company", ""),
            "location": job_data.get("location", ""),
            "salary": job_data.get("salary", ""),
            "job_type": job_data.get("job_type", ""),
            "remote": job_data.get("remote", ""),
            "link": job_url,
            "source": job_data.get("platform", "Unknown"),
            "status": "Applied",
            "notes": job_data.get("notes", ""),
        }
    
    except Exception as e:
        logger.error(f"Failed to process job URL {job_url}: {str(e)}", exc_info=True)
        raise


__all__ = [
    'validate_job_url',
    'fetch_job_html',
    'process_job_url',
    'parse_handshake_text_wrapper',
    'linkedin',
    'handshake',
    'generic',
]
