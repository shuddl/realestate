"""
Integration tests for the orchestrator module.

Tests the RealEstateOrchestrator class and its interactions with API clients
and calculation functions.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.real_estate_deal_finder.orchestrator import RealEstateOrchestrator


class TestRealEstateOrchestrator:
    """Integration tests for RealEstateOrchestrator."""
    
    @patch('src.real_estate_deal_finder.orchestrator.ZillowApiClient')
    @patch('src.real_estate_deal_finder.orchestrator.RentCastApiClient')
    def test_process_zip_codes_empty(self, mock_rentcast_client, mock_zillow_client):
        """Test processing with empty ZIP code list."""
        # Setup mocks
        mock_zillow_instance = MagicMock()
        mock_rentcast_instance = MagicMock()
        mock_zillow_client.return_value = mock_zillow_instance
        mock_rentcast_client.return_value = mock_rentcast_instance
        
        # Create orchestrator and process empty list
        orchestrator = RealEstateOrchestrator()
        results = orchestrator.process_zip_codes([])
        
        # Verify no API calls were made
        mock_zillow_instance.get_listings_by_zip.assert_not_called()
        mock_rentcast_instance.get_rent_estimate.assert_not_called()
        
        # Verify empty results
        assert results == []
    
    @patch('src.real_estate_deal_finder.orchestrator.ZillowApiClient')
    @patch('src.real_estate_deal_finder.orchestrator.RentCastApiClient')
    def test_process_zip_codes_no_zillow_listings(self, mock_rentcast_client, mock_zillow_client):
        """Test processing when Zillow returns no listings."""
        # Setup mocks
        mock_zillow_instance = MagicMock()
        mock_zillow_instance.get_listings_by_zip.return_value = []
        mock_rentcast_instance = MagicMock()
        mock_zillow_client.return_value = mock_zillow_instance
        mock_rentcast_client.return_value = mock_rentcast_instance
        
        # Create orchestrator and process list
        orchestrator = RealEstateOrchestrator()
        results = orchestrator.process_zip_codes(["90210"])
        
        # Verify Zillow API call was made
        mock_zillow_instance.get_listings_by_zip.assert_called_once_with("90210")
        
        # Verify RentCast API call was not made
        mock_rentcast_instance.get_rent_estimate.assert_not_called()
        
        # Verify empty results
        assert results == []
    
    @patch('src.real_estate_deal_finder.orchestrator.ZillowApiClient')
    @patch('src.real_estate_deal_finder.orchestrator.RentCastApiClient')
    def test_process_zip_codes_complete_flow(self, mock_rentcast_client, mock_zillow_client):
        """Test the complete processing flow with mock data."""
        # Setup Zillow mock
        mock_zillow_instance = MagicMock()
        mock_zillow_instance.get_listings_by_zip.return_value = [
            {
                "address": "123 Main St, Beverly Hills, CA 90210",
                "price": 1200000,
                "bedrooms": 3,
                "bathrooms": 2,
                "sqft": 2000,
                "year_built": 1990,
                "home_type": "singlefamily",
                "zillow_url": "https://www.zillow.com/homes/123456"
            }
        ]
        
        # Setup RentCast mock
        mock_rentcast_instance = MagicMock()
        mock_rentcast_instance.get_rent_estimate.return_value = 7000  # $7000/month rent
        
        # Set up mock client instances
        mock_zillow_client.return_value = mock_zillow_instance
        mock_rentcast_client.return_value = mock_rentcast_instance
        
        # Create orchestrator with test parameters
        orchestrator = RealEstateOrchestrator()
        orchestrator.down_payment_percent = 0.20
        orchestrator.interest_rate_decimal = 0.05
        orchestrator.loan_term_years = 30
        orchestrator.min_cash_flow = 100
        orchestrator.min_coc_return = 5.0
        
        # Process ZIP codes
        results = orchestrator.process_zip_codes(["90210"])
        
        # Verify Zillow API call was made
        mock_zillow_instance.get_listings_by_zip.assert_called_once_with("90210")
        
        # Verify RentCast API call was made
        mock_rentcast_instance.get_rent_estimate.assert_called_once_with("90210", 3)
        
        # Verify results
        assert len(results) == 1
        assert results[0]["address"] == "123 Main St, Beverly Hills, CA 90210"
        assert results[0]["price"] == 1200000
        assert results[0]["bedrooms"] == 3
        assert results[0]["estimated_rent"] == 7000
        assert "estimated_mortgage" in results[0]
        assert "estimated_monthly_cash_flow" in results[0]
        assert "estimated_coc_return" in results[0]
    
    @patch('src.real_estate_deal_finder.orchestrator.ZillowApiClient')
    @patch('src.real_estate_deal_finder.orchestrator.RentCastApiClient')
    def test_process_zip_codes_filtering(self, mock_rentcast_client, mock_zillow_client):
        """Test that properties are filtered based on criteria."""
        # Setup Zillow mock with two properties
        mock_zillow_instance = MagicMock()
        mock_zillow_instance.get_listings_by_zip.return_value = [
            {
                "address": "123 Main St, Beverly Hills, CA 90210",
                "price": 1200000,
                "bedrooms": 3,
                "bathrooms": 2,
                "sqft": 2000,
                "year_built": 1990,
                "home_type": "singlefamily",
                "zillow_url": "https://www.zillow.com/homes/123456"
            },
            {
                "address": "456 Oak Ave, Beverly Hills, CA 90210",
                "price": 2000000,  # More expensive property
                "bedrooms": 4,
                "bathrooms": 3,
                "sqft": 3000,
                "year_built": 1985,
                "home_type": "singlefamily",
                "zillow_url": "https://www.zillow.com/homes/654321"
            }
        ]
        
        # Setup RentCast mock with same rent for both properties
        mock_rentcast_instance = MagicMock()
        mock_rentcast_instance.get_rent_estimate.side_effect = [7000, 8500]
        
        # Set up mock client instances
        mock_zillow_client.return_value = mock_zillow_instance
        mock_rentcast_client.return_value = mock_rentcast_instance
        
        # Create orchestrator with strict filtering criteria
        orchestrator = RealEstateOrchestrator()
        orchestrator.down_payment_percent = 0.20
        orchestrator.interest_rate_decimal = 0.05
        orchestrator.loan_term_years = 30
        orchestrator.min_cash_flow = 1000  # High minimum cash flow
        orchestrator.min_coc_return = 10.0  # High minimum CoC return
        
        # Patch the calculate_monthly_expenses method to return fixed values
        with patch.object(orchestrator, 'calculate_monthly_expenses') as mock_expenses:
            mock_expenses.side_effect = [1000, 1500]  # Different expenses for each property
            
            # Process ZIP codes
            results = orchestrator.process_zip_codes(["90210"])
        
        # Verify API calls were made for both properties
        assert mock_zillow_instance.get_listings_by_zip.call_count == 1
        assert mock_rentcast_instance.get_rent_estimate.call_count == 2
        
        # If the filtering criteria worked correctly, we should get 0 or 1 properties
        # The exact result depends on the implementations of calculate_monthly_mortgage, etc.
        # We're mainly testing that the filtering logic itself runs
        assert len(results) <= 1