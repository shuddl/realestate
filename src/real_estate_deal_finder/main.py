"""
Main entry point for the Real Estate Deal Finder application.

This module initializes the application, sets up logging, runs the orchestrator,
and outputs the results to a CSV file.
"""

import argparse
import logging
import sys
import os
import re
from typing import List, Dict, Any, Optional

from src.real_estate_deal_finder import config
from src.real_estate_deal_finder import logging_config
from src.real_estate_deal_finder.orchestrator import RealEstateOrchestrator
from src.real_estate_deal_finder.output import save_results_to_csv


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Namespace containing the parsed arguments
    """
    parser = argparse.ArgumentParser(description="Real Estate Deal Finder CLI")
    
    # Create a mutually exclusive group for ZIP code input
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--zipcodes', type=str, help='Comma-separated list of ZIP codes to process (e.g., "90210,10001").')
    group.add_argument('--zipfile', type=str, help='Path to a text file containing one ZIP code per line.')
    
    return parser.parse_args()


def load_zip_codes(args: argparse.Namespace) -> List[str]:
    """
    Load and validate ZIP codes from command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        List of valid 5-digit ZIP codes
    """
    logger = logging.getLogger(__name__)
    zip_codes_list: List[str] = []
    
    # Process ZIP codes from file
    if args.zipfile:
        try:
            with open(args.zipfile, 'r') as f:
                # Read lines, strip whitespace, and filter out empty lines
                raw_zip_codes = [line.strip() for line in f if line.strip()]
                logger.info(f"Read {len(raw_zip_codes)} ZIP codes from file: {args.zipfile}")
                zip_codes_list.extend(raw_zip_codes)
        except FileNotFoundError:
            logger.error(f"ZIP code file not found: {args.zipfile}")
            return []
        except Exception as e:
            logger.error(f"Error reading ZIP code file: {e}")
            return []
    
    # Process ZIP codes from command line
    elif args.zipcodes:
        # Split by comma and strip whitespace
        raw_zip_codes = [z.strip() for z in args.zipcodes.split(',') if z.strip()]
        logger.info(f"Received {len(raw_zip_codes)} ZIP codes from command line")
        zip_codes_list.extend(raw_zip_codes)
    
    # Validate ZIP codes (must be 5 digits)
    valid_zip_codes = []
    zip_pattern = re.compile(r'^\d{5}$')
    
    for zip_code in zip_codes_list:
        if zip_pattern.match(zip_code):
            valid_zip_codes.append(zip_code)
        else:
            logger.warning(f"Invalid ZIP code format (must be 5 digits): {zip_code}")
    
    if len(valid_zip_codes) < len(zip_codes_list):
        logger.warning(f"Filtered out {len(zip_codes_list) - len(valid_zip_codes)} invalid ZIP codes")
    
    return valid_zip_codes


def main() -> int:
    """
    Main function to run the Real Estate Deal Finder application.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Initialize logger
    logger = logging.getLogger(__name__)
    logger.info("Real Estate Deal Finder starting...")
    
    # Check for configuration issues
    config_issues = config.validate_config()
    if config_issues:
        for key, message in config_issues.items():
            logger.error("Configuration error: %s - %s", key, message)
        logger.error("Please set the required environment variables in your .env file")
        return 1
    
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Load and validate ZIP codes
        zip_codes = load_zip_codes(args)
        
        if not zip_codes:
            logger.error("No valid ZIP codes provided or found. Exiting.")
            return 1
        
        logger.info(f"Loaded {len(zip_codes)} valid ZIP codes to process.")
        
        # Create and run the orchestrator
        orchestrator = RealEstateOrchestrator()
        logger.info("Starting property search and analysis...")
        filtered_results = orchestrator.process_zip_codes(zip_codes)
        
        # Save results to CSV
        output_file_path = save_results_to_csv(filtered_results)
        
        if output_file_path:
            logger.info(f"Successfully completed analysis. Results saved to: {output_file_path}")
        else:
            logger.info("Analysis completed, but no properties met the criteria or an error occurred during saving.")
        
    except Exception as e:
        logger.error(f"An error occurred during execution: {e}", exc_info=True)
        return 1
    
    logger.info("Real Estate Deal Finder completed successfully")
    return 0


if __name__ == "__main__":
    # Set up logging
    logging_config.setup_logging()
    
    # Run the main function
    exit_code = main()
    
    # Exit with the appropriate code
    sys.exit(exit_code)