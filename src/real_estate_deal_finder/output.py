"""
Output module for the Real Estate Deal Finder application.

This module handles saving the filtered property results to a CSV file.
"""

import csv
import os
import datetime
import logging
from typing import List, Dict, Any, Optional

from src.real_estate_deal_finder import config


def save_results_to_csv(results: List[Dict[str, Any]]) -> Optional[str]:
    """
    Save the filtered property results to a CSV file.
    
    Args:
        results: List of dictionaries containing property details
        
    Returns:
        The full path to the created CSV file, or None if an error occurred
    """
    logger = logging.getLogger(__name__)
    
    # Handle empty results
    if not results:
        logger.info("No properties met the criteria. No CSV file generated.")
        return None
    
    # Get output directory from config
    output_dir = config.OUTPUT_DIRECTORY
    
    # Create output directory if it doesn't exist
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Output directory ensured: {output_dir}")
    except OSError as e:
        logger.error(f"Failed to create output directory {output_dir}: {e}")
        return None
    
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_prefix = config.OUTPUT_FILENAME_PREFIX
    filename = f"{filename_prefix}_{timestamp}.csv"
    full_path = os.path.join(output_dir, filename)
    
    # CSV Headers
    headers = [
        "Address", 
        "Price", 
        "Beds", 
        "Estimated Rent", 
        "Estimated Mortgage", 
        "Estimated Monthly Cash Flow", 
        "Estimated CoC Return", 
        "Property Type", 
        "Zillow Link"
    ]
    
    # Write CSV file
    try:
        with open(full_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            # Write each property row
            for prop_dict in results:
                # Prepare row data with proper formatting and handling None values
                row_data = {
                    "Address": prop_dict.get('address', 'N/A'),
                    "Price": f"${prop_dict.get('price', 0.0):.2f}" if prop_dict.get('price') is not None else "N/A",
                    "Beds": prop_dict.get('bedrooms', 'N/A'),
                    "Estimated Rent": f"${prop_dict.get('estimated_rent', 0.0):.2f}" if prop_dict.get('estimated_rent') is not None else "N/A",
                    "Estimated Mortgage": f"${prop_dict.get('estimated_mortgage', 0.0):.2f}" if prop_dict.get('estimated_mortgage') is not None else "N/A",
                    "Estimated Monthly Cash Flow": f"${prop_dict.get('estimated_monthly_cash_flow', 0.0):.2f}" if prop_dict.get('estimated_monthly_cash_flow') is not None else "N/A",
                    "Estimated CoC Return": f"{prop_dict.get('estimated_coc_return', 0.0):.2f}%" if prop_dict.get('estimated_coc_return') is not None else "N/A",
                    "Property Type": prop_dict.get('property_type', 'N/A'),
                    "Zillow Link": prop_dict.get('zillow_url', 'N/A')
                }
                
                writer.writerow(row_data)
        
        logger.info(f"Successfully saved {len(results)} properties to {full_path}")
        return full_path
    
    except (IOError, PermissionError) as e:
        logger.error(f"Failed to write CSV file {full_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error writing CSV file {full_path}: {e}")
        return None