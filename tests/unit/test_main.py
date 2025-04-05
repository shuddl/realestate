"""
Unit tests for the main module.

Tests for argument parsing and ZIP code loading functions in the main module.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from src.real_estate_deal_finder.main import parse_arguments, load_zip_codes


class TestParseArguments:
    """Tests for the parse_arguments function."""
    
    def test_parse_zipcodes_argument(self):
        """Test parsing --zipcodes argument."""
        with patch('sys.argv', ['main.py', '--zipcodes', '90210,10001']):
            args = parse_arguments()
            assert args.zipcodes == '90210,10001'
            assert args.zipfile is None
    
    def test_parse_zipfile_argument(self):
        """Test parsing --zipfile argument."""
        with patch('sys.argv', ['main.py', '--zipfile', 'path/to/file.txt']):
            args = parse_arguments()
            assert args.zipfile == 'path/to/file.txt'
            assert args.zipcodes is None
    
    def test_missing_required_argument(self):
        """Test that error is raised when neither argument is provided."""
        with patch('sys.argv', ['main.py']):
            with pytest.raises(SystemExit):
                parse_arguments()


class TestLoadZipCodes:
    """Tests for the load_zip_codes function."""
    
    def test_load_from_zipcodes_string(self):
        """Test loading ZIP codes from --zipcodes argument."""
        mock_args = MagicMock()
        mock_args.zipcodes = '90210,10001, 20500'
        mock_args.zipfile = None
        
        zip_codes = load_zip_codes(mock_args)
        
        assert zip_codes == ['90210', '10001', '20500']
    
    def test_load_from_zipfile(self):
        """Test loading ZIP codes from --zipfile argument."""
        # Create a temporary file with ZIP codes
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write('90210\n10001\n# Comment line\n20500\n')
            temp_path = temp_file.name
        
        try:
            mock_args = MagicMock()
            mock_args.zipcodes = None
            mock_args.zipfile = temp_path
            
            zip_codes = load_zip_codes(mock_args)
            
            assert zip_codes == ['90210', '10001', '20500']
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)
    
    def test_load_from_zipfile_not_found(self):
        """Test error handling when ZIP code file is not found."""
        mock_args = MagicMock()
        mock_args.zipcodes = None
        mock_args.zipfile = 'nonexistent_file.txt'
        
        zip_codes = load_zip_codes(mock_args)
        
        assert zip_codes == []
    
    def test_validate_zip_codes(self):
        """Test validation of ZIP codes."""
        mock_args = MagicMock()
        mock_args.zipcodes = '90210,invalid,12,123456,10001'
        mock_args.zipfile = None
        
        zip_codes = load_zip_codes(mock_args)
        
        # Only valid 5-digit ZIP codes should be included
        assert zip_codes == ['90210', '10001']
        assert 'invalid' not in zip_codes
        assert '12' not in zip_codes
        assert '123456' not in zip_codes