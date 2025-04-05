# Real Estate Deal Finder

A Python command-line application to find cash-flowing rental properties (1-4 units) in specified US ZIP codes. This tool fetches property listings from Zillow (via RapidAPI) and rental estimates from RentCast, applies financial calculations to identify potentially profitable investment opportunities, and outputs the results to a CSV file. It's designed as an internal tool for a newsletter author to quickly shortlist investment-worthy properties.

## Features

* Fetches active listings (1-4 units) from Zillow API by ZIP code
* Retrieves average rent estimates from RentCast API by ZIP code and bedroom count
* Implements 30-day caching for RentCast API calls to minimize usage
* Calculates estimated monthly mortgage, cash flow, and cash-on-cash (CoC) return based on configurable assumptions
* Filters properties based on minimum CoC return and minimum monthly cash flow thresholds
* Outputs filtered results to a timestamped CSV file
* Accepts ZIP code input via command-line list or text file

## Technology Stack

* Python 3.9+
* requests (for API calls)
* python-dotenv (for environment variables)
* APScheduler (for time-based caching)
* pytest (for testing)

## Prerequisites

* Python 3.9 or higher
* pip (Python package manager)
* Git

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/real-estate-deal-finder.git
cd real-estate-deal-finder

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env and add your API keys
cp .env.example .env
```

## Configuration

Create a `.env` file in the project root by copying `.env.example` and filling in the required values:

```
# API Keys
ZILLOW_API_KEY="YOUR_ZILLOW_API_KEY"  # Get from RapidAPI Zillow API
ZILLOW_RAPIDAPI_HOST="zillow-com1.p.rapidapi.com"  # Or the current Zillow RapidAPI host
RENTCAST_API_KEY="YOUR_RENTCAST_API_KEY"  # Get from RentCast website

# Application Settings
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Default Financial Parameters
DEFAULT_DOWN_PAYMENT_PERCENT=20  # Percentage
DEFAULT_INTEREST_RATE=7.5  # Annual percentage rate
DEFAULT_LOAN_TERM_YEARS=30
DEFAULT_ANNUAL_PROPERTY_TAX_PERCENT=1.2
DEFAULT_ANNUAL_INSURANCE_PERCENT=0.5
DEFAULT_MONTHLY_HOA=0
DEFAULT_MONTHLY_PROPERTY_MANAGEMENT_PERCENT=10
DEFAULT_MONTHLY_MAINTENANCE_PERCENT=5
DEFAULT_MONTHLY_VACANCY_PERCENT=5
DEFAULT_CLOSING_COST_PERCENT=3

# Filter Thresholds
MIN_CASH_FLOW=100  # Minimum monthly cash flow in dollars
MIN_CASH_ON_CASH_RETURN=8  # Minimum annual CoC return percentage

# Caching
RENTCAST_CACHE_DAYS=30
RENTCAST_CACHE_FILE_PATH="data/rentcast_cache.json"
RENTCAST_CACHE_DURATION_SECONDS=2592000  # 30 days in seconds

# Output
OUTPUT_DIRECTORY="output"
OUTPUT_FILENAME_PREFIX="real_estate_deals"
```

### API Keys

* **ZILLOW_API_KEY**: You'll need to subscribe to the Zillow API on [RapidAPI](https://rapidapi.com/apimaker/api/zillow-com1/) to get this key.
* **RENTCAST_API_KEY**: Sign up for a developer account on the [RentCast website](https://rentcast.io/) to get this key.

## Usage (CLI)

Run the tool from the command line using one of these methods:

### Using comma-separated ZIP codes:

```bash
python src/real_estate_deal_finder/main.py --zipcodes "90210,10001,20500"
```

### Using a file with one ZIP code per line:

```bash
python src/real_estate_deal_finder/main.py --zipfile path/to/your/zipcodes.txt
```

Example ZIP code file format:
```
90210
10001
20500
# This is a comment (lines starting with # are ignored)
```

The filtered results will be saved to a CSV file in the configured output directory (default: `./output/`).
The filename will follow the pattern: `real_estate_deals_YYYYMMDD_HHMMSS.csv`

## Usage (Web UI)

The application includes a Streamlit web interface for easier interaction:

```bash
# Run the Streamlit app
streamlit run app.py
```

This will open a browser window with the web interface where you can:

1. Enter ZIP codes in the text area (one per line or comma-separated)
2. Adjust financial parameters and filter criteria using sliders in the sidebar
3. Click "Run Analysis" to process the data
4. View results in a table format
5. Download the filtered results as a CSV file

The web interface provides a more user-friendly experience with visual controls for all parameters.

## Project Structure

* `src/real_estate_deal_finder/`: Core application code
  * `main.py`: Entry point and command-line interface
  * `api_clients.py`: Zillow and RentCast API client implementations
  * `calculations.py`: Financial calculation functions
  * `config.py`: Configuration loading and validation
  * `logging_config.py`: Logging setup
  * `orchestrator.py`: Main workflow coordination
  * `output.py`: CSV file generation
* `tests/`: Unit and integration tests
* `output/`: Default directory for generated CSV files
* `data/`: Default directory for cache files
* `.env.example`: Example environment variables
* `CLAUDE.md`: Guidelines for AI assistants working with this code

## Running Tests

Run the test suite using pytest:

```bash
pytest
```

For specific test files or cases:

```bash
pytest tests/test_calculations.py
pytest tests/test_calculations.py::test_specific_scenario
```

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.

## License

MIT License