"""
Configuration module for the Real Estate Deal Finder application.

This module loads environment variables from a .env file and provides
configuration settings for the application.
"""

import os
from typing import Optional, Dict, Any, cast
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
ZILLOW_API_KEY: str = os.getenv("ZILLOW_API_KEY", "")
ZILLOW_RAPIDAPI_HOST: str = os.getenv("ZILLOW_RAPIDAPI_HOST", "zillow-com1.p.rapidapi.com")
RENTCAST_API_KEY: str = os.getenv("RENTCAST_API_KEY", "")

# Application Settings
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Default Financial Parameters
DEFAULT_DOWN_PAYMENT_PERCENT: float = float(os.getenv("DEFAULT_DOWN_PAYMENT_PERCENT", "20"))
DEFAULT_INTEREST_RATE: float = float(os.getenv("DEFAULT_INTEREST_RATE", "7.5"))
DEFAULT_LOAN_TERM_YEARS: int = int(os.getenv("DEFAULT_LOAN_TERM_YEARS", "30"))
DEFAULT_ANNUAL_PROPERTY_TAX_PERCENT: float = float(os.getenv("DEFAULT_ANNUAL_PROPERTY_TAX_PERCENT", "1.2"))
DEFAULT_ANNUAL_INSURANCE_PERCENT: float = float(os.getenv("DEFAULT_ANNUAL_INSURANCE_PERCENT", "0.5"))
DEFAULT_MONTHLY_HOA: float = float(os.getenv("DEFAULT_MONTHLY_HOA", "0"))
DEFAULT_MONTHLY_PROPERTY_MANAGEMENT_PERCENT: float = float(os.getenv("DEFAULT_MONTHLY_PROPERTY_MANAGEMENT_PERCENT", "10"))
DEFAULT_MONTHLY_MAINTENANCE_PERCENT: float = float(os.getenv("DEFAULT_MONTHLY_MAINTENANCE_PERCENT", "5"))
DEFAULT_MONTHLY_VACANCY_PERCENT: float = float(os.getenv("DEFAULT_MONTHLY_VACANCY_PERCENT", "5"))
DEFAULT_CLOSING_COST_PERCENT: float = float(os.getenv("DEFAULT_CLOSING_COST_PERCENT", "3"))

# Filter Thresholds
MIN_CASH_FLOW: float = float(os.getenv("MIN_CASH_FLOW", "100"))
MIN_CASH_ON_CASH_RETURN: float = float(os.getenv("MIN_CASH_ON_CASH_RETURN", "8"))

# Caching
RENTCAST_CACHE_DAYS: int = int(os.getenv("RENTCAST_CACHE_DAYS", "30"))
RENTCAST_CACHE_FILE_PATH: str = os.getenv("RENTCAST_CACHE_FILE_PATH", "data/rentcast_cache.json")
RENTCAST_CACHE_DURATION_SECONDS: int = int(os.getenv("RENTCAST_CACHE_DURATION_SECONDS", "2592000"))  # 30 days in seconds

# Output
OUTPUT_DIRECTORY: str = os.getenv("OUTPUT_DIRECTORY", "output")
OUTPUT_FILENAME_PREFIX: str = os.getenv("OUTPUT_FILENAME_PREFIX", "real_estate_deals")

# Validate required configuration
def validate_config() -> Dict[str, str]:
    """
    Validate that all required configuration variables are set.
    
    Returns:
        Dict[str, str]: Dictionary of missing or invalid configuration variables
    """
    issues: Dict[str, str] = {}
    
    if not ZILLOW_API_KEY:
        issues["ZILLOW_API_KEY"] = "Missing Zillow API Key"
    
    if not ZILLOW_RAPIDAPI_HOST:
        issues["ZILLOW_RAPIDAPI_HOST"] = "Missing Zillow RapidAPI Host"
    
    if not RENTCAST_API_KEY:
        issues["RENTCAST_API_KEY"] = "Missing RentCast API Key"
    
    return issues