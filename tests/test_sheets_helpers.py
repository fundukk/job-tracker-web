#!/usr/bin/env python3
"""
Unit tests for Google Sheets helper functions.
"""
import pytest
from datetime import date
from unittest.mock import Mock, MagicMock, patch
from app.sheets import (
    extract_spreadsheet_id,
    COLUMNS
)


class TestSheetsHelpers:
    """Test suite for sheets helper functions."""
    
    def test_extract_spreadsheet_id_from_url(self):
        """Test extracting spreadsheet ID from full URL."""
        url = "https://docs.google.com/spreadsheets/d/1ABC123XYZ/edit#gid=0"
        result = extract_spreadsheet_id(url)
        
        assert result == "1ABC123XYZ"
    
    def test_extract_spreadsheet_id_from_plain_id(self):
        """Test that plain IDs pass through unchanged."""
        plain_id = "1ABC123XYZ"
        result = extract_spreadsheet_id(plain_id)
        
        assert result == "1ABC123XYZ"
    
    def test_extract_spreadsheet_id_strips_whitespace(self):
        """Test that whitespace is stripped."""
        url = "  https://docs.google.com/spreadsheets/d/1ABC123/edit  "
        result = extract_spreadsheet_id(url)
        
        assert result == "1ABC123"
    
    def test_columns_definition(self):
        """Test that COLUMNS constant has expected structure."""
        assert isinstance(COLUMNS, list)
        assert len(COLUMNS) == 11
        assert "DateApplied" in COLUMNS
        assert "Company" in COLUMNS
        assert "Position" in COLUMNS
        assert "Link" in COLUMNS
    
    @patch('app.sheets.get_gspread_client')
    def test_get_worksheet_creates_headers(self, mock_get_client):
        """Test that get_worksheet creates header row if missing."""
        from app.sheets import get_worksheet
        
        # Mock the gspread client and worksheet
        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        
        mock_get_client.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_worksheet.row_values.return_value = []  # No headers
        
        # Call function
        credentials_dict = {
            'token': 'fake',
            'client_id': 'fake',
            'client_secret': 'fake',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'scopes': ['https://www.googleapis.com/auth/spreadsheets']
        }
        result = get_worksheet("test_sheet_id", credentials_dict)
        
        # Verify header row was inserted
        mock_worksheet.insert_row.assert_called_once_with(COLUMNS, 1)
    
    @patch('app.sheets.get_gspread_client')
    def test_append_job_row(self, mock_get_client):
        """Test appending a job row to the sheet."""
        from app.sheets import append_job_row
        
        mock_worksheet = Mock()
        
        job_data = {
            'company': 'TestCorp',
            'location': 'New York, NY',
            'position': 'Engineer',
            'link': 'https://example.com/job',
            'salary': '$100k/year',
            'job_type': 'Full-time',
            'remote': 'Remote',
            'status': 'Applied',
            'source': 'LinkedIn',
            'notes': 'Test note'
        }
        
        append_job_row(mock_worksheet, job_data)
        
        # Verify insert_row was called with correct data
        mock_worksheet.insert_row.assert_called_once()
        call_args = mock_worksheet.insert_row.call_args
        
        # Check that row was inserted at position 2 (after header)
        assert call_args[0][1] == 2
        
        # Check that data includes today's date
        row_data = call_args[0][0]
        assert row_data[0] == date.today().isoformat()
        assert row_data[1] == 'TestCorp'
        assert row_data[3] == 'Engineer'
    
    @patch('app.sheets.get_gspread_client')
    def test_find_job_by_link_found(self, mock_get_client):
        """Test finding a job by link when it exists."""
        from app.sheets import find_job_by_link
        
        mock_worksheet = Mock()
        mock_worksheet.get_all_values.return_value = [
            ['Date', 'Company', 'Location', 'Position', 'Link'],  # Header row
            ['2024-01-01', 'Corp1', 'NYC', 'Job1', 'https://example.com/job1'],
            ['2024-01-02', 'Corp2', 'LA', 'Job2', 'https://example.com/job2'],
        ]
        
        result = find_job_by_link(mock_worksheet, 'https://example.com/job2')
        
        # Should return row 3 (header=1, first job=2, second job=3)
        assert result == 3
    
    @patch('app.sheets.get_gspread_client')
    def test_find_job_by_link_not_found(self, mock_get_client):
        """Test finding a job by link when it doesn't exist."""
        from app.sheets import find_job_by_link
        
        mock_worksheet = Mock()
        mock_worksheet.get_all_values.return_value = [
            ['Date', 'Company', 'Location', 'Position', 'Link'],  # Header row
            ['2024-01-01', 'Corp1', 'NYC', 'Job1', 'https://example.com/job1'],
        ]
        
        result = find_job_by_link(mock_worksheet, 'https://example.com/nonexistent')
        
        # Should return 0 when not found
        assert result == 0
    
    def test_find_job_by_link_empty_link(self):
        """Test that empty link returns 0."""
        from app.sheets import find_job_by_link
        
        mock_worksheet = Mock()
        result = find_job_by_link(mock_worksheet, '')
        
        assert result == 0
