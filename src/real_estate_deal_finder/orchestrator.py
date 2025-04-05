"""
Orchestrator module for the Real Estate Deal Finder application.

This module contains the RealEstateOrchestrator class which coordinates
the workflow between API clients, financial calculations, and filtering
to find suitable rental properties based on specified criteria.
"""

import logging
from typing import List, Dict, Any, Optional

from src.real_estate_deal_finder import config
from src.real_estate_deal_finder.api_clients import ZillowApiClient, RentCastApiClient
from src.real_estate_deal_finder.calculations import (
    calculate_monthly_mortgage,
    calculate_cash_flow,
    calculate_coc_return
)


class RealEstateOrchestrator:
    """
    Coordinates the end-to-end process of finding rental properties that meet
    investment criteria.
    
    This class orchestrates:
    1. Fetching property listings from Zillow API
    2. Getting rent estimates from RentCast API
    3. Calculating financial metrics (mortgage, cash flow, CoC return)
    4. Filtering properties based on investment criteria
    """
    
    def __init__(self) -> None:
        """
        Initialize the Real Estate Orchestrator.
        
        Retrieves configuration settings and initializes API clients.
        """
        # Initialize API clients
        self.zillow_client = ZillowApiClient()
        self.rentcast_client = RentCastApiClient()
        
        # Retrieve filter criteria
        self.min_coc_return = config.MIN_CASH_ON_CASH_RETURN
        self.min_cash_flow = config.MIN_CASH_FLOW
        
        # Retrieve financial assumptions
        self.down_payment_percent = config.DEFAULT_DOWN_PAYMENT_PERCENT / 100.0  # Convert to decimal
        self.interest_rate_decimal = config.DEFAULT_INTEREST_RATE / 100.0  # Convert to decimal
        self.loan_term_years = config.DEFAULT_LOAN_TERM_YEARS
        
        # Calculate monthly expenses based on configuration
        # This is a simplification - a real implementation would calculate this per property
        self.monthly_expenses = 0.0  # Placeholder for property-specific calculation
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
    
    def calculate_monthly_expenses(self, property_price: float) -> float:
        """
        Calculate total monthly expenses for a property.
        
        Args:
            property_price: The purchase price of the property
            
        Returns:
            Total monthly expenses as a float
        """
        # Calculate annual property tax
        annual_property_tax = property_price * (config.DEFAULT_ANNUAL_PROPERTY_TAX_PERCENT / 100.0)
        monthly_property_tax = annual_property_tax / 12.0
        
        # Calculate annual insurance
        annual_insurance = property_price * (config.DEFAULT_ANNUAL_INSURANCE_PERCENT / 100.0)
        monthly_insurance = annual_insurance / 12.0
        
        # HOA fees (fixed amount per month)
        monthly_hoa = config.DEFAULT_MONTHLY_HOA
        
        # These would typically be calculated based on the actual rent,
        # but we need to estimate them before we have the rent figure
        # For now, we'll use a placeholder calculation
        estimated_rent = property_price * 0.008  # Rough estimate: 0.8% of property value as monthly rent
        
        # Property management (percentage of rent)
        monthly_property_management = estimated_rent * (config.DEFAULT_MONTHLY_PROPERTY_MANAGEMENT_PERCENT / 100.0)
        
        # Maintenance (percentage of rent)
        monthly_maintenance = estimated_rent * (config.DEFAULT_MONTHLY_MAINTENANCE_PERCENT / 100.0)
        
        # Vacancy (percentage of rent)
        monthly_vacancy = estimated_rent * (config.DEFAULT_MONTHLY_VACANCY_PERCENT / 100.0)
        
        # Sum all monthly expenses
        total_monthly_expenses = (
            monthly_property_tax +
            monthly_insurance +
            monthly_hoa +
            monthly_property_management +
            monthly_maintenance +
            monthly_vacancy
        )
        
        return total_monthly_expenses
    
    def process_zip_codes(self, zip_codes: List[str]) -> List[Dict[str, Any]]:
        """
        Process a list of ZIP codes to find properties meeting investment criteria.
        
        Args:
            zip_codes: List of ZIP codes to search
            
        Returns:
            List of dictionaries containing details of properties that meet the criteria
        """
        all_processed_properties: List[Dict[str, Any]] = []
        
        # Iterate through each ZIP code
        for zip_code in zip_codes:
            self.logger.info(f"Processing ZIP code: {zip_code}")
            
            # Get listings from Zillow
            listings = self.zillow_client.get_listings_by_zip(zip_code)
            self.logger.info(f"Found {len(listings)} listings in {zip_code}")
            
            # Process each listing
            for listing in listings:
                # Extract core property data
                home_type = listing.get('home_type', '').lower()
                address = listing.get('address')
                
                # Extract and validate price
                price = listing.get('price')
                if price is None:
                    self.logger.warning(f"Skipping property at {address}: Missing price")
                    continue
                
                try:
                    price = float(price)
                    if price <= 0:
                        self.logger.warning(f"Skipping property at {address}: Invalid price {price}")
                        continue
                except (ValueError, TypeError):
                    self.logger.warning(f"Skipping property at {address}: Price is not a valid number")
                    continue
                
                # Extract and validate bedrooms
                bedrooms = listing.get('bedrooms')
                if bedrooms is None:
                    self.logger.warning(f"Skipping property at {address}: Missing bedrooms")
                    continue
                
                try:
                    bedrooms = int(bedrooms)
                    if bedrooms <= 0:
                        self.logger.warning(f"Skipping property at {address}: Invalid bedrooms {bedrooms}")
                        continue
                except (ValueError, TypeError):
                    self.logger.warning(f"Skipping property at {address}: Bedrooms is not a valid number")
                    continue
                
                # Filter property type
                if home_type not in ("singlefamily", "multifamily"):
                    self.logger.debug(f"Skipping property at {address}: Unsupported type {home_type}")
                    continue
                
                property_type = "Single Family" if home_type == "singlefamily" else "Multifamily"
                
                # Additional property data
                bathrooms = listing.get('bathrooms')
                sqft = listing.get('sqft')
                year_built = listing.get('year_built')
                zillow_url = listing.get('zillow_url')
                
                # Get rent estimate from RentCast
                rent_estimate = self.rentcast_client.get_rent_estimate(zip_code, bedrooms)
                
                if rent_estimate is None:
                    self.logger.warning(f"Skipping property at {address}: Could not get rent estimate")
                    continue
                
                # Calculate monthly expenses
                monthly_expenses = self.calculate_monthly_expenses(price)
                
                # Calculate mortgage payment
                monthly_mortgage = calculate_monthly_mortgage(
                    price,
                    self.down_payment_percent,
                    self.interest_rate_decimal,
                    self.loan_term_years
                )
                
                if monthly_mortgage is None:
                    self.logger.warning(f"Skipping property at {address}: Could not calculate mortgage payment")
                    continue
                
                # Calculate cash flow
                monthly_cash_flow = calculate_cash_flow(
                    rent_estimate,
                    monthly_mortgage,
                    monthly_expenses
                )
                
                if monthly_cash_flow is None:
                    self.logger.warning(f"Skipping property at {address}: Could not calculate cash flow")
                    continue
                
                # Calculate annual cash flow and cash-on-cash return
                annual_cash_flow = monthly_cash_flow * 12.0
                
                coc_return = calculate_coc_return(
                    price,
                    self.down_payment_percent,
                    annual_cash_flow
                )
                
                if coc_return is None:
                    self.logger.warning(f"Skipping property at {address}: Could not calculate CoC return")
                    continue
                
                # Create property data dictionary
                property_data = {
                    'address': address,
                    'price': price,
                    'bedrooms': bedrooms,
                    'bathrooms': bathrooms,
                    'sqft': sqft,
                    'year_built': year_built,
                    'property_type': property_type,
                    'zillow_url': zillow_url,
                    'estimated_rent': rent_estimate,
                    'estimated_mortgage': monthly_mortgage,
                    'monthly_expenses': monthly_expenses,
                    'estimated_monthly_cash_flow': monthly_cash_flow,
                    'estimated_annual_cash_flow': annual_cash_flow,
                    'estimated_coc_return': coc_return,
                    'zip_code': zip_code
                }
                
                all_processed_properties.append(property_data)
            
            self.logger.info(f"Finished processing listings for ZIP code: {zip_code}")
        
        # Filter properties based on criteria
        self.logger.info(f"Processed {len(all_processed_properties)} total properties across all ZIP codes. Now filtering...")
        
        filtered_properties = []
        for prop in all_processed_properties:
            coc = prop.get('estimated_coc_return')
            cf = prop.get('estimated_monthly_cash_flow')
            
            passes_coc = coc is not None and coc >= self.min_coc_return
            passes_cf = cf is not None and cf >= self.min_cash_flow
            
            if passes_coc and passes_cf:
                filtered_properties.append(prop)
        
        self.logger.info(f"Found {len(filtered_properties)} properties meeting the criteria.")
        return filtered_properties