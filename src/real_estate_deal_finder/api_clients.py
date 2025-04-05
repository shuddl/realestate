"""
API client implementations for the Real Estate Deal Finder application.

This module contains classes for interacting with external APIs such as Zillow and RentCast.
"""

import json
import logging
import os
import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

import requests

from src.real_estate_deal_finder import config


class APIError(Exception):
    """Exception raised for API-related errors."""
    pass


class ZillowApiClient:
    """
    Client for interacting with the Zillow API via RapidAPI.
    
    This class handles authentication, request building, error handling,
    and response parsing for the Zillow API endpoints.
    """
    
    def __init__(self) -> None:
        """
        Initialize the Zillow API client.
        
        Retrieves API key and host from configuration and sets up logger.
        """
        self.api_key = config.ZILLOW_API_KEY
        self.rapidapi_host = config.ZILLOW_RAPIDAPI_HOST
        self.base_url = f"https://{self.rapidapi_host}"
        self.logger = logging.getLogger(__name__)
        
        if not self.api_key:
            self.logger.error("Zillow API key is not set in configuration")
        
        if not self.rapidapi_host:
            self.logger.error("Zillow RapidAPI host is not set in configuration")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None, 
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the Zillow API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters for the request
            headers: Additional headers to include
            
        Returns:
            Dict containing the parsed JSON response
            
        Raises:
            APIError: If the request fails or returns an error response
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Prepare default headers
        default_headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.rapidapi_host
        }
        
        # Merge with any custom headers
        if headers:
            default_headers.update(headers)
        
        self.logger.debug(f"Making {method} request to {url}")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=default_headers,
                params=params,
                timeout=15  # 15 seconds timeout
            )
            
            # Check for HTTP errors
            if response.status_code >= 400:
                error_message = f"API request failed with status {response.status_code}: {response.text}"
                self.logger.error(error_message)
                raise APIError(error_message)
            
            # Parse JSON response
            try:
                response_data = response.json()
                return response_data
            except json.JSONDecodeError as e:
                error_message = f"Failed to parse API response as JSON: {e}"
                self.logger.error(error_message)
                self.logger.debug(f"Response content: {response.text[:500]}...")
                raise APIError(error_message)
                
        except requests.exceptions.RequestException as e:
            error_message = f"Request to Zillow API failed: {e}"
            self.logger.error(error_message)
            raise APIError(error_message)
    
    def get_listings_by_zip(self, zip_code: str) -> List[Dict[str, Any]]:
        """
        Fetch property listings for a specific ZIP code.
        
        Args:
            zip_code: The ZIP code to search for listings
            
        Returns:
            List of dictionaries containing property listing details
        """
        self.logger.info(f"Fetching Zillow listings for ZIP code: {zip_code}")
        
        # Define the endpoint for listings by ZIP code
        # Note: This is a placeholder and may need adjustment based on the actual RapidAPI endpoint
        endpoint = "propertyExtendedSearch"
        
        # Define query parameters
        params = {
            "location": zip_code,
            "home_type": "Houses",  # Focusing on houses
            "sort": "price_high_to_low"  # Sort from highest to lowest price
        }
        
        try:
            # Make the API request
            response_data = self._make_request("GET", endpoint, params=params)
            
            # Parse the listings from the response
            # Note: The actual response structure may differ; this is an educated guess
            try:
                # Try to extract listings from the expected location in the response
                # This assumes the listings are in a 'results' key
                raw_listings = response_data.get("results", [])
                
                if not raw_listings:
                    self.logger.warning(f"No listings found for ZIP code {zip_code}")
                    return []
                
                # Process the listings to extract relevant fields
                processed_listings = []
                for listing in raw_listings:
                    # Extract the fields we're interested in
                    processed_listing = {
                        "address": listing.get("address"),
                        "price": listing.get("price"),
                        "bedrooms": listing.get("bedrooms"),
                        "bathrooms": listing.get("bathrooms"),
                        "sqft": listing.get("livingArea"),
                        "home_type": listing.get("homeType", "Unknown"),
                        "year_built": listing.get("yearBuilt"),
                        "zillow_url": listing.get("detailUrl"),
                        "zpid": listing.get("zpid"),  # Zillow Property ID
                        "images": listing.get("imgSrc")
                    }
                    
                    # Filter out listings that don't have essential data
                    if all(processed_listing.get(key) is not None for key in ["address", "price", "bedrooms"]):
                        processed_listings.append(processed_listing)
                    else:
                        self.logger.debug(f"Skipping listing due to missing essential data: {listing.get('zpid')}")
                
                self.logger.info(f"Successfully parsed {len(processed_listings)} listings for ZIP code {zip_code}")
                return processed_listings
                
            except (KeyError, TypeError) as e:
                self.logger.error(f"Failed to parse listings from response: {e}")
                self.logger.debug(f"Response structure: {list(response_data.keys())}")
                return []
                
        except APIError as e:
            self.logger.error(f"Error fetching listings for ZIP code {zip_code}: {e}")
            return []


class RentCastApiClient:
    """
    Client for interacting with the RentCast API.
    
    This class handles authentication, request building, error handling,
    response parsing, and caching for the RentCast API endpoints.
    """
    
    def __init__(self) -> None:
        """
        Initialize the RentCast API client.
        
        Retrieves API key and cache settings from configuration and sets up logging and cache.
        """
        self.api_key = config.RENTCAST_API_KEY
        self.cache_file_path = config.RENTCAST_CACHE_FILE_PATH
        self.cache_duration_seconds = config.RENTCAST_CACHE_DURATION_SECONDS
        self.base_url = "https://api.rentcast.io/v1"
        self.logger = logging.getLogger(__name__)
        
        # Initialize cache storage
        self.cache_data: Dict[str, Any] = {}
        
        # Make sure the cache directory exists
        os.makedirs(os.path.dirname(self.cache_file_path), exist_ok=True)
        
        # Load the cache
        self._load_cache()
        
        if not self.api_key:
            self.logger.error("RentCast API key is not set in configuration")
    
    def _load_cache(self) -> None:
        """
        Load cached data from the cache file.
        
        If the file doesn't exist or has invalid JSON, an empty cache is used.
        """
        try:
            if os.path.exists(self.cache_file_path):
                with open(self.cache_file_path, 'r') as f:
                    self.cache_data = json.load(f)
                self.logger.debug(f"Loaded cache from {self.cache_file_path} with {len(self.cache_data)} entries")
            else:
                self.logger.info(f"Cache file {self.cache_file_path} does not exist. Starting with empty cache.")
        except FileNotFoundError:
            self.logger.info(f"Cache file {self.cache_file_path} not found. Starting with empty cache.")
        except json.JSONDecodeError as e:
            # If the cache file is corrupted, back it up and start with an empty cache
            backup_path = f"{self.cache_file_path}.bak.{int(datetime.datetime.now().timestamp())}"
            try:
                os.rename(self.cache_file_path, backup_path)
                self.logger.error(f"Cache file had invalid JSON: {e}. Backed up to {backup_path} and starting with empty cache.")
            except OSError:
                self.logger.error(f"Cache file had invalid JSON: {e}. Could not create backup. Starting with empty cache.")
            self.cache_data = {}
        except Exception as e:
            self.logger.error(f"Error loading cache: {e}. Starting with empty cache.")
            self.cache_data = {}
    
    def _save_cache(self) -> None:
        """
        Save the current cache data to the cache file.
        
        Creates the cache directory if it doesn't exist.
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.cache_file_path), exist_ok=True)
            
            # Write the cache data to the file
            with open(self.cache_file_path, 'w') as f:
                json.dump(self.cache_data, f, indent=4)
            
            self.logger.debug(f"Saved {len(self.cache_data)} entries to cache file {self.cache_file_path}")
        except IOError as e:
            self.logger.error(f"Error saving cache to {self.cache_file_path}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error saving cache: {e}")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if a cache entry is valid (exists and not expired).
        
        Args:
            cache_key: The key to check in the cache
            
        Returns:
            True if the entry exists and is not expired, False otherwise
        """
        if cache_key not in self.cache_data:
            return False
        
        cache_entry = self.cache_data[cache_key]
        
        # Check if the entry has the expected structure
        if not isinstance(cache_entry, dict) or 'timestamp' not in cache_entry or 'data' not in cache_entry:
            self.logger.warning(f"Cache entry for {cache_key} has invalid structure")
            return False
        
        # Check if the entry has expired
        timestamp = cache_entry['timestamp']
        current_time = datetime.datetime.now().timestamp()
        age = current_time - timestamp
        
        if age >= self.cache_duration_seconds:
            self.logger.debug(f"Cache entry for {cache_key} has expired (age: {age:.1f}s, max: {self.cache_duration_seconds}s)")
            return False
        
        return True
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the RentCast API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters for the request
            
        Returns:
            Dict containing the parsed JSON response
            
        Raises:
            APIError: If the request fails or returns an error response
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Prepare headers
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        self.logger.debug(f"Making {method} request to {url}")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                timeout=15  # 15 seconds timeout
            )
            
            # Check for HTTP errors
            if response.status_code >= 400:
                error_message = f"RentCast API request failed with status {response.status_code}: {response.text}"
                self.logger.error(error_message)
                raise APIError(error_message)
            
            # Parse JSON response
            try:
                response_data = response.json()
                return response_data
            except json.JSONDecodeError as e:
                error_message = f"Failed to parse RentCast API response as JSON: {e}"
                self.logger.error(error_message)
                self.logger.debug(f"Response content: {response.text[:500]}...")
                raise APIError(error_message)
                
        except requests.exceptions.RequestException as e:
            error_message = f"Request to RentCast API failed: {e}"
            self.logger.error(error_message)
            raise APIError(error_message)
    
    def get_rent_estimate(self, zip_code: str, bedrooms: int) -> Optional[float]:
        """
        Get the average rent estimate for a property in a specific ZIP code with the given number of bedrooms.
        
        Args:
            zip_code: The ZIP code to get the rent estimate for
            bedrooms: The number of bedrooms in the property
            
        Returns:
            The average rent estimate as a float, or None if the estimate couldn't be retrieved
        """
        self.logger.info(f"Getting rent estimate for ZIP code {zip_code} with {bedrooms} bedrooms")
        
        # Create a unique cache key
        cache_key = f"{zip_code}_{bedrooms}"
        
        # Check if we have a valid cached value
        if self._is_cache_valid(cache_key):
            cached_estimate = self.cache_data[cache_key]['data']
            self.logger.info(f"Using cached rent estimate for {zip_code} with {bedrooms} bedrooms: ${cached_estimate:.2f}")
            return cached_estimate
        
        # If not in cache or expired, fetch from API
        try:
            # Define the RentCast endpoint for rent estimates by ZIP code
            endpoint = "avm/rent/zipcode"
            
            # Define query parameters
            params = {
                'zipCode': zip_code,
                'propertyType': 'SFH',  # Single Family Home (may need adjustment based on RentCast documentation)
                'bedrooms': bedrooms
            }
            
            # Make the API request
            response_data = self._make_request("GET", endpoint, params=params)
            
            # Parse the response to get the rent estimate
            try:
                # Try to extract the rent estimate from the expected location in the response
                # This is an assumption - adjust based on actual RentCast API response structure
                rent_estimate = response_data.get('rent')
                
                if rent_estimate is None:
                    self.logger.warning(f"No rent estimate found in response for ZIP {zip_code} with {bedrooms} bedrooms")
                    return None
                
                # Convert to float (may already be a number in the JSON)
                rent_estimate_float = float(rent_estimate)
                
                # Cache the result
                self.cache_data[cache_key] = {
                    'timestamp': datetime.datetime.now().timestamp(),
                    'data': rent_estimate_float
                }
                self._save_cache()
                
                self.logger.info(f"Fetched and cached rent estimate for {zip_code} with {bedrooms} bedrooms: ${rent_estimate_float:.2f}")
                return rent_estimate_float
                
            except (KeyError, TypeError, ValueError) as e:
                self.logger.error(f"Failed to parse rent estimate from response: {e}")
                self.logger.debug(f"Response keys: {list(response_data.keys())}")
                return None
                
        except APIError as e:
            self.logger.error(f"Error fetching rent estimate for ZIP {zip_code} with {bedrooms} bedrooms: {e}")
            return None