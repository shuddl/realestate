# Real Estate Deal Finder - Handover Document

## Project Overview

The Real Estate Deal Finder is a Python application designed to help investors identify potentially profitable rental properties. The tool fetches current property listings from Zillow (via RapidAPI) and rent estimates from RentCast, performs financial calculations, and filters properties based on user-defined investment criteria (cash flow and cash-on-cash return).

The application offers both a command-line interface and a web-based Streamlit interface for broader accessibility.

## Core Functionality & Requirements

### Primary Functions
1. Fetch property listings (1-4 units) from the Zillow API for specified ZIP codes
2. Retrieve average rent estimates from the RentCast API based on location and bedroom count
3. Calculate key financial metrics:
   - Monthly mortgage payment
   - Monthly cash flow
   - Cash-on-cash (CoC) return
4. Filter properties that meet minimum cash flow and CoC return criteria
5. Output filtered results to a timestamped CSV file

### Key Requirements
1. **Data Retrieval**:
   - Fetch accurate, up-to-date property listing data from Zillow API
   - Obtain reliable rent estimates from RentCast API
   - Implement 30-day caching for RentCast API calls to minimize API usage

2. **Financial Calculations**:
   - Monthly mortgage payment using the standard formula
   - Monthly cash flow (rent minus mortgage minus expenses)
   - Cash-on-cash return (annual cash flow divided by cash invested)

3. **User Interface**:
   - Command-line interface accepting ZIP codes via arguments or file
   - Streamlit web interface with input fields and adjustable parameters

4. **Output Format**:
   - CSV file with property details and financial metrics
   - Properly formatted currency values and percentages
   - Timestamped filenames for easy organization

## Project Structure

```
real-estate-deal-finder/
├── app.py                          # Streamlit web interface
├── CLAUDE.md                       # Guidelines for AI assistants
├── .env.example                    # Example environment variables
├── .gitignore                      # Git ignore file
├── HANDOVER.md                     # This handover document
├── pytest.ini                      # Pytest configuration
├── README.md                       # Project documentation
├── requirements.txt                # Project dependencies
├── src/
│   └── real_estate_deal_finder/    # Core application code
│       ├── __init__.py             # Package marker
│       ├── api_clients.py          # Zillow and RentCast API clients
│       ├── calculations.py         # Financial calculation functions
│       ├── config.py               # Configuration loading and validation
│       ├── logging_config.py       # Logging setup
│       ├── main.py                 # Command-line entry point
│       ├── orchestrator.py         # Main workflow coordination
│       └── output.py               # CSV file generation
└── tests/                          # Test suite
    ├── conftest.py                 # Pytest fixtures and configuration
    ├── integration/                # Integration tests
    │   ├── test_app.py             # Tests for Streamlit app
    │   └── test_orchestrator.py    # Tests for workflow orchestration
    ├── test_data/                  # Data for tests
    └── unit/                       # Unit tests
        ├── test_api_clients.py     # API client tests
        ├── test_calculations.py    # Financial calculation tests
        ├── test_main.py            # Command-line interface tests
        └── test_output.py          # CSV output tests
```

## Technical Implementation Details

### API Clients
- **ZillowApiClient**: Fetches property listings via Zillow's API (accessed through RapidAPI)
- **RentCastApiClient**: Retrieves rent estimates with file-based 30-day caching

### Financial Calculations
- Standard mortgage formula: `P * [r(1+r)^n] / [(1+r)^n - 1]`
- Cash flow calculation: `monthly_rent - monthly_mortgage - monthly_expenses`
- CoC return calculation: `(annual_cash_flow / cash_invested) * 100`

### Orchestration
- `RealEstateOrchestrator` class coordinates the entire workflow
- Handles ZIP code iteration, API calls, calculations, and filtering

### Output
- CSV file generation with properly formatted values
- Results saved to configurable output directory with timestamped filenames

### User Interfaces
- CLI: Accepts ZIP codes via `--zipcodes` argument or `--zipfile` parameter
- Streamlit: Web interface with adjustable financial parameters and filters

## Configuration Options

The application is highly configurable through environment variables (.env file):

### API Keys
- `ZILLOW_API_KEY` - RapidAPI key for Zillow API access
- `ZILLOW_RAPIDAPI_HOST` - RapidAPI host for Zillow (default: "zillow-com1.p.rapidapi.com")
- `RENTCAST_API_KEY` - API key for RentCast

### Financial Parameters
- `DEFAULT_DOWN_PAYMENT_PERCENT` - Percentage of property price as down payment
- `DEFAULT_INTEREST_RATE` - Annual mortgage interest rate
- `DEFAULT_LOAN_TERM_YEARS` - Mortgage term in years
- Plus various expense parameters (property tax, insurance, HOA, etc.)

### Filter Criteria
- `MIN_CASH_FLOW` - Minimum monthly cash flow in dollars
- `MIN_CASH_ON_CASH_RETURN` - Minimum annual CoC return percentage

### Caching & Output
- `RENTCAST_CACHE_FILE_PATH` - Location of cache file for RentCast data
- `RENTCAST_CACHE_DURATION_SECONDS` - Cache duration in seconds
- `OUTPUT_DIRECTORY` - Directory for saving CSV output files
- `OUTPUT_FILENAME_PREFIX` - Prefix for output filenames

## Testing

The project includes a comprehensive test suite:

### Unit Tests
- **api_clients.py**: Tests for Zillow and RentCast API clients, including caching
- **calculations.py**: Tests for financial calculation functions
- **main.py**: Tests for command-line argument parsing and ZIP code loading
- **output.py**: Tests for CSV generation and formatting

### Integration Tests
- **orchestrator.py**: Tests for the full workflow with mocked API responses
- **app.py**: Tests for the Streamlit app's core functionality

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src/real_estate_deal_finder

# Run specific test files
pytest tests/unit/test_calculations.py
```

## Deployment & Running

### Prerequisites
- Python 3.9+
- API keys for Zillow (via RapidAPI) and RentCast

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/real-estate-deal-finder.git
cd real-estate-deal-finder

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env to add your API keys
```

### Running the Application
```bash
# Command-line interface
python src/real_estate_deal_finder/main.py --zipcodes "90210,10001"
# OR
python src/real_estate_deal_finder/main.py --zipfile zipcodes.txt

# Web interface
streamlit run app.py
```

## Future Enhancements

Potential areas for future development:

1. **Additional Data Sources**: Integrate with more real estate data providers
2. **Advanced Filtering Options**: Allow filtering by additional property characteristics
3. **Property History**: Track changes in property listings over time
4. **Data Visualization**: Add charts and visualizations for market analysis
5. **Geospatial Analysis**: Map-based visualization of properties
6. **Export Formats**: Support additional export formats beyond CSV
7. **User Accounts**: Add user authentication and saved searches
8. **Batch Processing**: Improve performance for large sets of ZIP codes
9. **Mobile Interface**: Create a responsive mobile web interface
10. **Scheduled Runs**: Implement automatic periodic searches

## Maintenance Requirements

### API Changes
- Monitor Zillow RapidAPI and RentCast API for changes in:
  - Authentication methods
  - Endpoint URLs
  - Response formats
  - Rate limits

### Dependency Updates
- Regularly update Python dependencies for security and functionality
- Test thoroughly after updates to key libraries (requests, streamlit, pandas)

### Financial Formula Updates
- Periodically review financial calculation formulas for accuracy
- Update expense assumptions based on market conditions

## Contact Information

For questions or issues regarding this project, please contact:

- **Project Owner**: [Your Name/Organization]
- **Email**: [Your Email]
- **GitHub Repository**: [Repository URL]