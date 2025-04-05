"""
Integration tests for the Streamlit app.

Tests for the app.py functionality using the Streamlit test library.
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


# Note: True Streamlit testing would require the streamlit.testing library,
# but we can test the core functions the app uses

def test_parse_zip_codes():
    """Test the parse_zip_codes function in the app."""
    # Import here to avoid importing streamlit in non-streamlit contexts
    from app import parse_zip_codes
    
    # Test with comma-separated input
    result = parse_zip_codes("90210,10001, 20500")
    assert result == ["90210", "10001", "20500"]
    
    # Test with newline-separated input
    result = parse_zip_codes("90210\n10001\n20500")
    assert result == ["90210", "10001", "20500"]
    
    # Test with mixed separators
    result = parse_zip_codes("90210,10001\n20500")
    assert result == ["90210", "10001", "20500"]
    
    # Test with invalid ZIP codes
    result = parse_zip_codes("90210,invalid,123456,10001")
    assert result == ["90210", "10001"]
    
    # Test with comments
    result = parse_zip_codes("90210\n# Comment line\n10001")
    assert result == ["90210", "10001"]
    
    # Test with empty input
    result = parse_zip_codes("")
    assert result == []


def test_format_currency():
    """Test the format_currency function in the app."""
    # Import here to avoid importing streamlit in non-streamlit contexts
    from app import format_currency
    
    # Test with various inputs
    assert format_currency(1000) == "$1,000.00"
    assert format_currency(1000.5) == "$1,000.50"
    assert format_currency(0) == "$0.00"
    assert format_currency(None) == "N/A"
    assert format_currency(pd.NA) == "N/A"


def test_format_percentage():
    """Test the format_percentage function in the app."""
    # Import here to avoid importing streamlit in non-streamlit contexts
    from app import format_percentage
    
    # Test with various inputs
    assert format_percentage(10) == "10.00%"
    assert format_percentage(10.5) == "10.50%"
    assert format_percentage(0) == "0.00%"
    assert format_percentage(None) == "N/A"
    assert format_percentage(pd.NA) == "N/A"


@patch('app.RealEstateOrchestrator')
def test_streamlit_core_flow(mock_orchestrator_class):
    """Test the core workflow of the Streamlit app."""
    # Import here to avoid importing streamlit directly
    import app
    
    # We can't directly test Streamlit UI components, but we can test the
    # helper functions and the core workflow that would be triggered
    
    # Setup mock orchestrator
    mock_orchestrator = MagicMock()
    mock_orchestrator.process_zip_codes.return_value = [
        {
            "address": "123 Main St, Beverly Hills, CA 90210",
            "price": 1200000,
            "bedrooms": 3,
            "bathrooms": 2,
            "property_type": "Single Family",
            "estimated_rent": 7000,
            "estimated_mortgage": 5000,
            "monthly_expenses": 1000,
            "estimated_monthly_cash_flow": 1000,
            "estimated_coc_return": 10.0
        }
    ]
    mock_orchestrator_class.return_value = mock_orchestrator
    
    # Test that the app's workflow functions correctly by patching streamlit
    # Since we can't directly test streamlit.button(), we'll test the
    # functionality that would be called when the button is clicked
    
    # In a real test of a Streamlit app, we would use the streamlit.testing library
    # to interact with the app's UI components directly
    
    # For now, let's just verify that our helper functions are working
    zips = app.parse_zip_codes("90210,10001")
    assert zips == ["90210", "10001"]
    
    # And that our dataframe conversion would work
    with patch('app.pd.DataFrame') as mock_df:
        mock_df.return_value = pd.DataFrame({
            "Address": ["123 Main St"],
            "Price": [1200000],
            "CoC Return %": [10.0]
        })
        
        # The app would process these results
        results = mock_orchestrator.process_zip_codes.return_value
        # And format them for display
        for col in ["Price", "Estimated Rent"]:
            if col in mock_df.return_value.columns:
                mock_df.return_value[col] = mock_df.return_value[col].apply(app.format_currency)
                
        for col in ["CoC Return %"]:
            if col in mock_df.return_value.columns:
                mock_df.return_value[col] = mock_df.return_value[col].apply(app.format_percentage)
        
        # The result would be a formatted dataframe for display