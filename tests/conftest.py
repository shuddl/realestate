"""
Pytest configuration file for Real Estate Deal Finder tests.

This file contains fixtures and configuration settings for the test suite.
"""

import os
import pytest
from unittest.mock import patch

# Set test environment variables
os.environ['ZILLOW_API_KEY'] = 'test_zillow_key'
os.environ['ZILLOW_RAPIDAPI_HOST'] = 'test.rapidapi.com'
os.environ['RENTCAST_API_KEY'] = 'test_rentcast_key'
os.environ['RENTCAST_CACHE_FILE_PATH'] = 'tests/test_data/test_cache.json'
os.environ['LOG_LEVEL'] = 'DEBUG'


@pytest.fixture
def mock_zillow_response():
    """Sample Zillow API response for testing."""
    return {
        "results": [
            {
                "zpid": "123456",
                "address": "123 Main St, Beverly Hills, CA 90210",
                "bedrooms": 3,
                "bathrooms": 2,
                "price": 1200000,
                "livingArea": 2000,
                "homeType": "SINGLE_FAMILY",
                "yearBuilt": 1990,
                "detailUrl": "https://www.zillow.com/homes/123456"
            },
            {
                "zpid": "654321",
                "address": "456 Oak Ave, Beverly Hills, CA 90210",
                "bedrooms": 4,
                "bathrooms": 3,
                "price": 1500000,
                "livingArea": 2500,
                "homeType": "MULTI_FAMILY",
                "yearBuilt": 1985,
                "detailUrl": "https://www.zillow.com/homes/654321"
            }
        ]
    }


@pytest.fixture
def mock_rentcast_response():
    """Sample RentCast API response for testing."""
    return {
        "rent": 4000.0
    }


@pytest.fixture
def sample_property_data():
    """Sample property data for testing financial calculations."""
    return {
        "address": "123 Main St, Beverly Hills, CA 90210",
        "price": 1200000,
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 2000,
        "year_built": 1990,
        "property_type": "Single Family",
        "zillow_url": "https://www.zillow.com/homes/123456",
        "estimated_rent": 4000,
        "estimated_mortgage": 5000,
        "monthly_expenses": 1000,
        "estimated_monthly_cash_flow": -2000,
        "estimated_annual_cash_flow": -24000,
        "estimated_coc_return": -10.0,
        "zip_code": "90210"
    }


@pytest.fixture
def sample_filtered_results():
    """List of properties that pass the filtering criteria."""
    return [
        {
            "address": "123 Main St, Beverly Hills, CA 90210",
            "price": 1200000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 2000,
            "year_built": 1990,
            "property_type": "Single Family",
            "zillow_url": "https://www.zillow.com/homes/123456",
            "estimated_rent": 7000,
            "estimated_mortgage": 5000,
            "monthly_expenses": 1000,
            "estimated_monthly_cash_flow": 1000,
            "estimated_annual_cash_flow": 12000,
            "estimated_coc_return": 10.0,
            "zip_code": "90210"
        },
        {
            "address": "456 Oak Ave, Beverly Hills, CA 90210",
            "price": 1500000,
            "bedrooms": 4,
            "bathrooms": 3,
            "sqft": 2500,
            "year_built": 1985,
            "property_type": "Multifamily",
            "zillow_url": "https://www.zillow.com/homes/654321",
            "estimated_rent": 8000,
            "estimated_mortgage": 6000,
            "monthly_expenses": 1200,
            "estimated_monthly_cash_flow": 800,
            "estimated_annual_cash_flow": 9600,
            "estimated_coc_return": 8.0,
            "zip_code": "90210"
        }
    ]