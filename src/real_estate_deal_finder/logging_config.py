"""
Logging configuration for the Real Estate Deal Finder application.

This module provides functions to set up and configure logging for the application.
"""

import logging
import sys
from typing import Optional

from src.real_estate_deal_finder import config

def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure the logging system for the application.
    
    Args:
        level: The logging level to use. If None, uses the level from the config.
    """
    if level is None:
        level = config.LOG_LEVEL
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    # Configure the root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create a logger for this application
    logger = logging.getLogger("real_estate_deal_finder")
    
    # Log the configuration
    logger.debug("Logging configured with level: %s", level)
    
    # Log warnings for any configuration issues
    config_issues = config.validate_config()
    for key, message in config_issues.items():
        logger.warning("Configuration issue: %s - %s", key, message)