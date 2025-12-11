#!/usr/bin/env python3
"""
Unit tests for LinkedIn job parser.
"""
import pytest
from app.parsers import linkedin


class TestLinkedInParser:
    """Test suite for LinkedIn parser."""
    
    def test_parse_basic_job(self):
        """Test parsing a basic LinkedIn job posting."""
        html = """
        <html>
            <head>
                <meta property="og:title" content="Software Engineer - TechCorp | LinkedIn" />
            </head>
            <body>
                <h1>Software Engineer</h1>
                <p>San Francisco, CA</p>
                <p>$120,000 - $150,000/year</p>
                <p>Full-time, Remote</p>
            </body>
        </html>
        """
        
        result = linkedin.parse(html, "https://www.linkedin.com/jobs/view/123456")
        
        assert result['platform'] == 'LinkedIn'
        assert result['title'] == 'Software Engineer'
        assert result['company'] == 'TechCorp'
        assert 'San Francisco' in result['location']
        assert result['remote'] == 'Remote'
    
    def test_parse_with_salary(self):
        """Test salary extraction from LinkedIn job."""
        html = """
        <html>
            <body>
                <h1>Data Scientist</h1>
                <p>The salary range is $100k - $140k per year</p>
            </body>
        </html>
        """
        
        result = linkedin.parse(html, "https://www.linkedin.com/jobs/view/789012")
        
        assert '$' in result['salary']
        assert 'year' in result['salary'].lower() or 'yr' in result['salary'].lower()
    
    def test_parse_job_type_detection(self):
        """Test job type detection (internship, full-time, etc.)."""
        html_internship = """
        <html>
            <body>
                <h1>Engineering Intern</h1>
                <p>This is an internship position for summer 2025.</p>
            </body>
        </html>
        """
        
        result = linkedin.parse(html_internship, "https://www.linkedin.com/jobs/view/111111")
        assert result['job_type'] == 'Internship'
        
        html_fulltime = """
        <html>
            <body>
                <h1>Senior Developer</h1>
                <p>This is a full-time position with benefits.</p>
            </body>
        </html>
        """
        
        result = linkedin.parse(html_fulltime, "https://www.linkedin.com/jobs/view/222222")
        assert result['job_type'] == 'Full-time'
    
    def test_parse_remote_detection(self):
        """Test remote/hybrid/on-site detection."""
        test_cases = [
            ("This is a remote position", "Remote"),
            ("We offer hybrid work arrangements", "Hybrid"),
            ("This role is on-site at our office", "On-site"),
        ]
        
        for text, expected in test_cases:
            html = f"""
            <html>
                <body>
                    <h1>Test Job</h1>
                    <p>{text}</p>
                </body>
            </html>
            """
            result = linkedin.parse(html, "https://www.linkedin.com/jobs/view/test")
            assert result['remote'] == expected, f"Failed for: {text}"
    
    def test_parse_handles_missing_data(self):
        """Test that parser handles missing/incomplete data gracefully."""
        minimal_html = "<html><body><h1>Job Title</h1></body></html>"
        
        result = linkedin.parse(minimal_html, "https://www.linkedin.com/jobs/view/test")
        
        # Should still return a valid dict with all required keys
        assert 'title' in result
        assert 'company' in result
        assert 'location' in result
        assert 'platform' in result
        assert result['platform'] == 'LinkedIn'
    
    def test_parse_handles_malformed_html(self):
        """Test that parser handles malformed HTML without crashing."""
        bad_html = "<html><body><p>Broken HTML"
        
        result = linkedin.parse(bad_html, "https://www.linkedin.com/jobs/view/test")
        
        # Should not raise exception, should return dict
        assert isinstance(result, dict)
        assert 'notes' in result
