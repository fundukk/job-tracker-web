#!/usr/bin/env python3
"""
Unit tests for Handshake job parser.
"""
import pytest
from app.parsers import handshake


class TestHandshakeParser:
    """Test suite for Handshake parser."""
    
    def test_parse_text_basic(self):
        """Test parsing basic Handshake copied text."""
        text = """
        TechCorp logo
        Software Engineering Intern
        TechCorp
        New York, NY
        Internship
        Remote
        $30/hr
        """
        
        result = handshake.parse_text(text, "https://handshake.com/jobs/123456")
        
        assert result['platform'] == 'Handshake'
        assert 'Software' in result['title']
        assert result['company'] == 'TechCorp'
        assert 'New York' in result['location']
        assert result['job_type'] == 'Internship'
        assert result['remote'] == 'Remote'
    
    def test_parse_text_with_labeled_fields(self):
        """Test parsing with explicitly labeled fields."""
        text = """
        Position
        Data Analyst
        Company
        DataCo
        Location
        Austin, TX
        Salary
        $70,000/year
        JobType
        Full-time
        """
        
        result = handshake.parse_text(text, "https://handshake.com/jobs/789012")
        
        assert result['title'] == 'Data Analyst'
        assert result['company'] == 'DataCo'
        assert result['location'] == 'Austin, TX'
        assert '$70,000' in result['salary']
        assert result['job_type'] == 'Full-time'
    
    def test_parse_text_salary_detection(self):
        """Test salary detection from various formats."""
        test_cases = [
            ("The pay is $25/hr for this role", "$25/hr"),
            ("Salary: $80,000 per year", "$80,000 per year"),
            ("Compensation: $100k - $120k/yr", "$100k - $120k/yr"),
        ]
        
        for text, expected_contains in test_cases:
            result = handshake.parse_text(text, "https://handshake.com/jobs/test")
            assert expected_contains.split()[0] in result['salary'], \
                f"Failed for: {text}, got: {result['salary']}"
    
    def test_parse_text_location_pattern(self):
        """Test location extraction from City, ST pattern."""
        text = """
        Great opportunity in Seattle, WA!
        Full-time Software Developer position.
        """
        
        result = handshake.parse_text(text, "https://handshake.com/jobs/test")
        
        assert result['location'] == 'Seattle, WA'
    
    def test_parse_text_job_type_detection(self):
        """Test job type detection from keywords."""
        test_cases = [
            ("This is an internship for students", "Internship"),
            ("Full-time position available", "Full-time"),
            ("Part-time work opportunity", "Part-time"),
            ("Contract role for 6 months", "Contract"),
        ]
        
        for text, expected in test_cases:
            result = handshake.parse_text(text, "https://handshake.com/jobs/test")
            assert result['job_type'] == expected, f"Failed for: {text}"
    
    def test_parse_text_filters_noise(self):
        """Test that noise patterns are filtered out."""
        text = """
        Skip to main content
        Menu
        123 profile views
        TechCorp logo
        Software Engineer
        TechCorp
        Posted 2 days ago
        Apply by March 1
        """
        
        result = handshake.parse_text(text, "https://handshake.com/jobs/test")
        
        # Should extract meaningful data and ignore noise
        assert result['title'] == 'Software Engineer'
        assert result['company'] == 'TechCorp'
        assert 'Skip' not in result['title']
        assert 'profile views' not in result['company']
    
    def test_parse_html_basic(self):
        """Test HTML parsing fallback."""
        html = """
        <html>
            <head>
                <meta property="og:title" content="Marketing Intern" />
                <meta property="og:site_name" content="MarketCo" />
            </head>
            <body>
                <p>Boston, MA</p>
                <p>$22/hour</p>
                <p>This is a remote internship position.</p>
            </body>
        </html>
        """
        
        result = handshake.parse(html, "https://handshake.com/jobs/test")
        
        assert result['title'] == 'Marketing Intern'
        assert result['company'] == 'MarketCo'
        assert result['remote'] == 'Remote'
    
    def test_parse_handles_empty_text(self):
        """Test that parser handles empty text gracefully."""
        result = handshake.parse_text("", "https://handshake.com/jobs/test")
        
        # Should return valid dict with empty fields
        assert isinstance(result, dict)
        assert result['platform'] == 'Handshake'
        assert 'title' in result
        assert 'company' in result
