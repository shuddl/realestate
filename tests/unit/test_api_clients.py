"""
Unit tests for the API clients.

Tests for ZillowApiClient and RentCastApiClient classes in the api_clients module.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.real_estate_deal_finder.api_clients import ZillowApiClient, RentCastApiClient, APIError


class TestZillowApiClient:
    """Tests for the ZillowApiClient class."""
    
    @patch('src.real_estate_deal_finder.api_clients.requests.request')
    def test_make_request_success(self, mock_request):
        """Test making a successful API request."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": "test_data"}
        mock_request.return_value = mock_response
        
        # Create client and make request
        client = ZillowApiClient()
        result = client._make_request("GET", "test_endpoint", {"param": "value"})
        
        # Verify request was made correctly
        mock_request.assert_called_once_with(
            method="GET",
            url="https://zillow-com1.p.rapidapi.com/test_endpoint",
            headers={
                "X-RapidAPI-Key": "test_zillow_key",
                "X-RapidAPI-Host": "test.rapidapi.com"
            },
            params={"param": "value"},
            timeout=15
        )
        
        # Verify result
        assert result == {"success": True, "data": "test_data"}
    
    @patch('src.real_estate_deal_finder.api_clients.requests.request')
    def test_make_request_http_error(self, mock_request):
        """Test handling HTTP error responses."""
        # Setup mock response with error
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_request.return_value = mock_response
        
        # Create client and test exception is raised
        client = ZillowApiClient()
        with pytest.raises(APIError) as exc_info:
            client._make_request("GET", "test_endpoint")
        
        # Verify error message
        assert "404" in str(exc_info.value)
        assert "Not Found" in str(exc_info.value)
    
    @patch('src.real_estate_deal_finder.api_clients.requests.request')
    def test_make_request_network_error(self, mock_request):
        """Test handling network errors."""
        # Setup mock to raise exception
        mock_request.side_effect = Exception("Connection error")
        
        # Create client and test exception is raised
        client = ZillowApiClient()
        with pytest.raises(APIError) as exc_info:
            client._make_request("GET", "test_endpoint")
        
        # Verify error message
        assert "Connection error" in str(exc_info.value)
    
    @patch('src.real_estate_deal_finder.api_clients.ZillowApiClient._make_request')
    def test_get_listings_by_zip(self, mock_make_request, mock_zillow_response):
        """Test fetching listings by ZIP code."""
        # Setup mock to return sample response
        mock_make_request.return_value = mock_zillow_response
        
        # Create client and get listings
        client = ZillowApiClient()
        listings = client.get_listings_by_zip("90210")
        
        # Verify request was made
        mock_make_request.assert_called_once()
        
        # Verify processed listings
        assert len(listings) == 2
        assert listings[0]["address"] == "123 Main St, Beverly Hills, CA 90210"
        assert listings[1]["price"] == 1500000


class TestRentCastApiClient:
    """Tests for the RentCastApiClient class."""
    
    def setup_method(self):
        """Set up test environment."""
        # Ensure test cache directory exists
        os.makedirs(os.path.dirname("tests/test_data/test_cache.json"), exist_ok=True)
        
        # Remove test cache file if it exists
        if os.path.exists("tests/test_data/test_cache.json"):
            os.remove("tests/test_data/test_cache.json")
    
    def teardown_method(self):
        """Clean up after test."""
        # Remove test cache file
        if os.path.exists("tests/test_data/test_cache.json"):
            os.remove("tests/test_data/test_cache.json")
    
    @patch('src.real_estate_deal_finder.api_clients.requests.request')
    def test_make_request_success(self, mock_request):
        """Test making a successful API request."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": "test_data"}
        mock_request.return_value = mock_response
        
        # Create client and make request
        client = RentCastApiClient()
        result = client._make_request("GET", "test_endpoint", {"param": "value"})
        
        # Verify request was made correctly
        mock_request.assert_called_once_with(
            method="GET",
            url="https://api.rentcast.io/v1/test_endpoint",
            headers={
                "X-Api-Key": "test_rentcast_key",
                "Content-Type": "application/json"
            },
            params={"param": "value"},
            timeout=15
        )
        
        # Verify result
        assert result == {"success": True, "data": "test_data"}
    
    @patch('src.real_estate_deal_finder.api_clients.RentCastApiClient._make_request')
    def test_get_rent_estimate_api_call(self, mock_make_request, mock_rentcast_response):
        """Test fetching rent estimate when not in cache."""
        # Setup mock to return sample response
        mock_make_request.return_value = mock_rentcast_response
        
        # Create client and get rent estimate
        client = RentCastApiClient()
        rent = client.get_rent_estimate("90210", 3)
        
        # Verify request was made
        mock_make_request.assert_called_once_with(
            "GET", 
            "avm/rent/zipcode", 
            {'zipCode': '90210', 'propertyType': 'SFH', 'bedrooms': 3}
        )
        
        # Verify result
        assert rent == 4000.0
        
        # Verify cache was updated
        assert os.path.exists("tests/test_data/test_cache.json")
        with open("tests/test_data/test_cache.json", "r") as f:
            cache_data = json.load(f)
            assert "90210_3" in cache_data
            assert cache_data["90210_3"]["data"] == 4000.0
    
    def test_get_rent_estimate_from_cache(self):
        """Test fetching rent estimate from cache."""
        # Create a cache file with test data
        cache_data = {
            "90210_3": {
                "timestamp": 9999999999,  # Far future timestamp to ensure cache validity
                "data": 3500.0
            }
        }
        
        with open("tests/test_data/test_cache.json", "w") as f:
            json.dump(cache_data, f)
        
        # Create client and get rent estimate (should use cache)
        client = RentCastApiClient()
        rent = client.get_rent_estimate("90210", 3)
        
        # Verify result from cache
        assert rent == 3500.0
    
    @patch('src.real_estate_deal_finder.api_clients.RentCastApiClient._make_request')
    def test_get_rent_estimate_api_error(self, mock_make_request):
        """Test handling API errors when fetching rent estimate."""
        # Setup mock to raise exception
        mock_make_request.side_effect = APIError("API error")
        
        # Create client and get rent estimate (should return None)
        client = RentCastApiClient()
        rent = client.get_rent_estimate("90210", 3)
        
        # Verify result
        assert rent is None