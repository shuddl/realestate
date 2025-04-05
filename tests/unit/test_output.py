"""
Unit tests for the output module.

Tests for the save_results_to_csv function in the output module.
"""

import os
import csv
import pytest
from unittest.mock import patch
from src.real_estate_deal_finder.output import save_results_to_csv


class TestSaveResultsToCsv:
    """Tests for the save_results_to_csv function."""
    
    def setup_method(self):
        """Set up test environment."""
        # Set test output directory
        os.environ['OUTPUT_DIRECTORY'] = 'tests/test_data/output'
        os.environ['OUTPUT_FILENAME_PREFIX'] = 'test_results'
        
        # Ensure test output directory exists
        os.makedirs('tests/test_data/output', exist_ok=True)
    
    def teardown_method(self):
        """Clean up after test."""
        # Remove test output directory
        import shutil
        if os.path.exists('tests/test_data/output'):
            shutil.rmtree('tests/test_data/output')
    
    def test_save_results_empty_list(self):
        """Test saving empty results."""
        result = save_results_to_csv([])
        assert result is None
    
    @patch('src.real_estate_deal_finder.output.datetime')
    def test_save_results_success(self, mock_datetime, sample_filtered_results):
        """Test successfully saving results to CSV."""
        # Mock datetime to get a fixed filename
        mock_datetime.datetime.now.return_value.strftime.return_value = "20250101_120000"
        
        # Save results
        output_path = save_results_to_csv(sample_filtered_results)
        
        # Verify output path
        expected_path = 'tests/test_data/output/test_results_20250101_120000.csv'
        assert output_path == expected_path
        
        # Verify file exists
        assert os.path.exists(expected_path)
        
        # Verify file contents
        with open(expected_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Verify correct number of rows
            assert len(rows) == 2
            
            # Verify column headers
            assert 'Address' in reader.fieldnames
            assert 'Price' in reader.fieldnames
            assert 'Beds' in reader.fieldnames
            assert 'Estimated Rent' in reader.fieldnames
            assert 'Zillow Link' in reader.fieldnames
            
            # Verify data in first row
            assert rows[0]['Address'] == "123 Main St, Beverly Hills, CA 90210"
            assert rows[0]['Price'] == "$1,200,000.00"
            assert rows[0]['Beds'] == "3"
            assert rows[0]['Estimated CoC Return'] == "10.00%"
    
    def test_save_results_directory_error(self, sample_filtered_results):
        """Test handling directory creation errors."""
        # Set output directory to an invalid path
        os.environ['OUTPUT_DIRECTORY'] = '/invalid/directory/path'
        
        # Try to save results (should fail)
        with patch('src.real_estate_deal_finder.output.os.makedirs') as mock_makedirs:
            mock_makedirs.side_effect = OSError("Permission denied")
            result = save_results_to_csv(sample_filtered_results)
            
            # Verify result is None
            assert result is None
    
    def test_save_results_file_error(self, sample_filtered_results):
        """Test handling file writing errors."""
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = IOError("Permission denied")
            result = save_results_to_csv(sample_filtered_results)
            
            # Verify result is None
            assert result is None