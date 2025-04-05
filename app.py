"""
Streamlit web UI for the Real Estate Deal Finder application.

This script provides a graphical interface for the tool, allowing users to:
1. Input ZIP codes
2. Adjust financial assumptions and filter criteria
3. Run the analysis
4. View and download the results
5. Shortlist properties and add notes
"""

import re
import os
import json
import logging
import streamlit as st
import pandas as pd

from src.real_estate_deal_finder import config
from src.real_estate_deal_finder import logging_config
from src.real_estate_deal_finder.orchestrator import RealEstateOrchestrator
from src.real_estate_deal_finder.calculations import (
    calculate_monthly_mortgage,
    calculate_cash_flow,
    calculate_coc_return
)

# Constants
SHORTLIST_FILE = "data/shortlist.json"

# Shortlist functions
def load_shortlist():
    """
    Load the shortlist from the JSON file.
    
    Returns:
        List of dictionaries containing shortlisted properties
    """
    try:
        if os.path.exists(SHORTLIST_FILE):
            with open(SHORTLIST_FILE, "r") as f:
                return json.load(f)
        return []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        st.error(f"Error loading shortlist: {e}")
        return []

def save_shortlist(shortlist_data):
    """
    Save the shortlist to the JSON file.
    
    Args:
        shortlist_data: List of dictionaries containing shortlisted properties
    """
    try:
        os.makedirs(os.path.dirname(SHORTLIST_FILE), exist_ok=True)
        with open(SHORTLIST_FILE, "w") as f:
            json.dump(shortlist_data, f, indent=4)
    except IOError as e:
        st.error(f"Error saving shortlist: {e}")

# Initialize shortlist in session state
if 'shortlist' not in st.session_state:
    st.session_state.shortlist = load_shortlist()


# Set up logging
logging_config.setup_logging()
logger = logging.getLogger(__name__)


# Define helper functions
def parse_zip_codes(zip_input: str) -> list:
    """
    Parse and validate ZIP codes from text input.
    
    Args:
        zip_input: String containing ZIP codes (comma or newline separated)
        
    Returns:
        List of valid 5-digit ZIP codes
    """
    # Split by both commas and newlines
    raw_zips = re.split(r'[,\n]', zip_input)
    
    # Clean and validate ZIP codes
    valid_zips = []
    zip_pattern = re.compile(r'^\d{5}$')
    
    for zip_code in raw_zips:
        # Remove whitespace and skip empty strings
        zip_code = zip_code.strip()
        if not zip_code or zip_code.startswith('#'):
            continue
            
        # Validate format (5 digits)
        if zip_pattern.match(zip_code):
            valid_zips.append(zip_code)
            
    return valid_zips


@st.cache_data
def convert_df_to_csv(df):
    """
    Convert DataFrame to CSV for download.
    
    Args:
        df: Pandas DataFrame to convert
        
    Returns:
        CSV string encoded as UTF-8
    """
    return df.to_csv(index=False).encode('utf-8')


def format_currency(value):
    """Format a value as currency."""
    if pd.isna(value):
        return "N/A"
    return f"${value:,.2f}"


def format_percentage(value):
    """Format a value as percentage."""
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}%"


def recalculate_metrics(df: pd.DataFrame, config_overrides: dict) -> pd.DataFrame:
    """
    Recalculate financial metrics based on updated config values.
    
    Args:
        df: Original DataFrame with property data
        config_overrides: Dictionary containing new financial assumptions
        
    Returns:
        DataFrame with recalculated metrics
    """
    # Create a copy to avoid modifying the original
    recalc_df = df.copy()
    
    # Extract configuration values
    interest_rate = config_overrides.get('interest_rate_decimal', 0.075)
    down_payment_percent = config_overrides.get('down_payment_percent', 0.20)
    loan_term_years = config_overrides.get('loan_term_years', 30)
    monthly_expenses = config_overrides.get('monthly_expenses', 0.0)
    rent_adjustment_percent = config_overrides.get('rent_adjustment_percent', 0.0)
    
    # Function to recalculate mortgage for each row
    def recalc_mortgage(row):
        if pd.isna(row.get('price')):
            return None
        return calculate_monthly_mortgage(
            row['price'], 
            down_payment_percent, 
            interest_rate, 
            loan_term_years
        )
    
    # Recalculate mortgage payments
    recalc_df['estimated_mortgage'] = recalc_df.apply(recalc_mortgage, axis=1)
    
    # Adjust rent if needed
    if rent_adjustment_percent != 0:
        recalc_df['adjusted_rent'] = recalc_df['estimated_rent'] * (1 + rent_adjustment_percent / 100)
    else:
        recalc_df['adjusted_rent'] = recalc_df['estimated_rent']
    
    # Function to recalculate cash flow
    def recalc_cash_flow(row):
        return calculate_cash_flow(
            row['adjusted_rent'],
            row['estimated_mortgage'],
            monthly_expenses
        )
    
    # Recalculate monthly cash flow
    recalc_df['estimated_monthly_cash_flow'] = recalc_df.apply(recalc_cash_flow, axis=1)
    
    # Recalculate annual cash flow
    recalc_df['estimated_annual_cash_flow'] = recalc_df['estimated_monthly_cash_flow'] * 12
    
    # Function to recalculate CoC return
    def recalc_coc_return(row):
        if pd.isna(row.get('price')) or pd.isna(row.get('estimated_annual_cash_flow')):
            return None
        return calculate_coc_return(
            row['price'],
            down_payment_percent,
            row['estimated_annual_cash_flow']
        )
    
    # Recalculate CoC return
    recalc_df['estimated_coc_return'] = recalc_df.apply(recalc_coc_return, axis=1)
    
    # Clean up
    recalc_df.drop('adjusted_rent', axis=1, inplace=True, errors='ignore')
    
    return recalc_df


# Configure Streamlit page
st.set_page_config(
    page_title="Real Estate Deal Finder",
    page_icon="🏠",
    layout="wide"
)

# Main title
st.title("🏠 Real Estate Deal Finder")
st.markdown("""
Find cash-flowing rental properties in your target ZIP codes using real-time data 
from Zillow and RentCast APIs. Adjust the financial parameters in the sidebar to 
match your investment criteria.
""")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Financial Assumptions
    st.subheader("Financial Assumptions")
    
    dp_percent_ui = st.slider(
        "Down Payment %",
        min_value=0,
        max_value=100,
        value=int(config.DEFAULT_DOWN_PAYMENT_PERCENT),
        step=1,
        format="%d"
    )
    
    interest_rate_ui = st.slider(
        "Interest Rate %",
        min_value=0.0,
        max_value=20.0,
        value=float(config.DEFAULT_INTEREST_RATE),
        step=0.1,
        format="%.1f"
    )
    
    loan_term_ui = st.slider(
        "Loan Term (Years)",
        min_value=1,
        max_value=40,
        value=int(config.DEFAULT_LOAN_TERM_YEARS),
        step=1
    )
    
    st.markdown("#### Monthly Expenses")
    
    property_tax_ui = st.slider(
        "Annual Property Tax %",
        min_value=0.0,
        max_value=5.0,
        value=float(config.DEFAULT_ANNUAL_PROPERTY_TAX_PERCENT),
        step=0.1,
        format="%.1f"
    )
    
    insurance_ui = st.slider(
        "Annual Insurance %",
        min_value=0.0,
        max_value=3.0,
        value=float(config.DEFAULT_ANNUAL_INSURANCE_PERCENT),
        step=0.1,
        format="%.1f"
    )
    
    hoa_ui = st.number_input(
        "Monthly HOA $",
        min_value=0,
        value=int(config.DEFAULT_MONTHLY_HOA),
        step=10
    )
    
    property_mgmt_ui = st.slider(
        "Property Management %",
        min_value=0.0,
        max_value=20.0,
        value=float(config.DEFAULT_MONTHLY_PROPERTY_MANAGEMENT_PERCENT),
        step=0.5,
        format="%.1f"
    )
    
    maintenance_ui = st.slider(
        "Maintenance %",
        min_value=0.0,
        max_value=20.0,
        value=float(config.DEFAULT_MONTHLY_MAINTENANCE_PERCENT),
        step=0.5,
        format="%.1f"
    )
    
    vacancy_ui = st.slider(
        "Vacancy %",
        min_value=0.0,
        max_value=20.0,
        value=float(config.DEFAULT_MONTHLY_VACANCY_PERCENT),
        step=0.5,
        format="%.1f"
    )
    
    # Filter Criteria
    st.subheader("Filter Criteria")
    
    min_coc_ui = st.slider(
        "Minimum Cash-on-Cash Return %",
        min_value=0.0,
        max_value=50.0,
        value=float(config.MIN_CASH_ON_CASH_RETURN),
        step=0.5,
        format="%.1f"
    )
    
    min_cf_ui = st.number_input(
        "Minimum Monthly Cash Flow $",
        min_value=0,
        value=int(config.MIN_CASH_FLOW),
        step=50
    )

# Main area input
st.header("📍 Input ZIP Codes")
zip_input_str = st.text_area(
    "Enter ZIP codes (one per line or comma-separated):",
    height=150,
    placeholder="90210\n10001\n60606\n# You can add comments with #"
)

run_button_clicked = st.button("🚀 Run Analysis", type="primary")

# Processing logic when button is clicked
if run_button_clicked:
    # Parse and validate ZIP codes
    zip_codes_list = parse_zip_codes(zip_input_str)
    
    if not zip_codes_list:
        st.warning("Please enter at least one valid 5-digit ZIP code.")
        st.stop()
    
    st.info(f"Starting analysis for {len(zip_codes_list)} ZIP codes...")
    
    # Create a copy of configuration with UI values
    updated_config = {
        'DEFAULT_DOWN_PAYMENT_PERCENT': dp_percent_ui,
        'DEFAULT_INTEREST_RATE': interest_rate_ui,
        'DEFAULT_LOAN_TERM_YEARS': loan_term_ui,
        'DEFAULT_ANNUAL_PROPERTY_TAX_PERCENT': property_tax_ui,
        'DEFAULT_ANNUAL_INSURANCE_PERCENT': insurance_ui,
        'DEFAULT_MONTHLY_HOA': hoa_ui,
        'DEFAULT_MONTHLY_PROPERTY_MANAGEMENT_PERCENT': property_mgmt_ui,
        'DEFAULT_MONTHLY_MAINTENANCE_PERCENT': maintenance_ui,
        'DEFAULT_MONTHLY_VACANCY_PERCENT': vacancy_ui,
        'MIN_CASH_ON_CASH_RETURN': min_coc_ui,
        'MIN_CASH_FLOW': min_cf_ui
    }
    
    # For debugging
    logger.debug(f"Running analysis with parameters: {updated_config}")
    
    try:
        # Run the analysis
        with st.spinner("Fetching property data and calculating metrics... This may take a while."):
            # Create orchestrator
            orchestrator = RealEstateOrchestrator()
            
            # Apply custom configuration
            orchestrator.min_coc_return = min_coc_ui
            orchestrator.min_cash_flow = min_cf_ui
            orchestrator.down_payment_percent = dp_percent_ui / 100.0  # Convert to decimal
            orchestrator.interest_rate_decimal = interest_rate_ui / 100.0  # Convert to decimal
            orchestrator.loan_term_years = loan_term_ui
            
            # Process ZIP codes
            filtered_results = orchestrator.process_zip_codes(zip_codes_list)
            
            # Store original results and config in session state
            if 'original_results' not in st.session_state or st.session_state.get('last_run_zip_codes') != zip_codes_list:
                st.session_state.original_results = filtered_results.copy()
                st.session_state.last_run_zip_codes = zip_codes_list.copy()  # Track which ZIPs these results are for
                st.session_state.run_config = {
                    'interest_rate_decimal': interest_rate_ui / 100.0,
                    'down_payment_percent': dp_percent_ui / 100.0,
                    'loan_term_years': loan_term_ui,
                    'monthly_expenses': orchestrator.calculate_monthly_expenses(300000)  # Sample price to get expenses
                }
    
    except Exception as e:
        st.error("An error occurred during analysis:")
        st.exception(e)
        logger.error(f"Error during analysis: {e}", exc_info=True)
        st.stop()
    
    # Display results
    st.header("📊 Results")
    
    if filtered_results:
        # Convert to DataFrame
        df = pd.DataFrame(filtered_results)
        
        # Rename and select columns for display
        if len(df.columns) > 0:
            # Add selection column (must be added before renaming)
            df.insert(0, "Select", False)
            
            # Keep the original zillow_url before renaming for shortlist functionality
            df['link'] = df['zillow_url'] if 'zillow_url' in df.columns else None
            
            # Define column mapping
            column_mapping = {
                'address': 'Address',
                'price': 'Price',
                'bedrooms': 'Beds',
                'bathrooms': 'Baths',
                'sqft': 'Sq Ft',
                'year_built': 'Year Built',
                'property_type': 'Type',
                'estimated_rent': 'Est. Rent',
                'estimated_mortgage': 'Est. Mortgage',
                'monthly_expenses': 'Monthly Expenses',
                'estimated_monthly_cash_flow': 'Monthly Cash Flow',
                'estimated_annual_cash_flow': 'Annual Cash Flow',
                'estimated_coc_return': 'CoC Return %',
                'zip_code': 'ZIP Code',
                'zillow_url': 'Zillow Link'
            }
            
            # Rename columns that exist in the DataFrame
            existing_columns = [col for col in column_mapping.keys() if col in df.columns]
            df = df.rename(columns={col: column_mapping[col] for col in existing_columns})
            
            # Define display columns and order
            display_columns = [
                'Select', 'Address', 'ZIP Code', 'Price', 'Beds', 'Baths', 'Sq Ft',
                'Est. Rent', 'Est. Mortgage', 'Monthly Expenses', 'Monthly Cash Flow',
                'CoC Return %', 'Type', 'Year Built', 'Zillow Link'
            ]
            
            # Filter to only display columns that exist in the DataFrame
            display_columns = [col for col in display_columns if col in df.columns]
            
            # Store the unformatted DataFrame for adding to shortlist
            unformatted_df = df.copy()
            
            # Format currency and percentage columns
            for col in df.columns:
                if col in ['Price', 'Est. Rent', 'Est. Mortgage', 'Monthly Expenses', 
                           'Monthly Cash Flow', 'Annual Cash Flow']:
                    df[col] = df[col].apply(format_currency)
                elif col in ['CoC Return %']:
                    df[col] = df[col].apply(format_percentage)
            
            # Display information about selection
            st.info("Select properties below and click 'Add Selected to Shortlist'.")
            
            # Add sensitivity analysis feature if original results exist
            if 'original_results' in st.session_state:
                with st.expander("📊 Sensitivity Analysis / Scenario Modeling"):
                    st.markdown("""
                    Adjust the financial parameters below to see how changes would affect your metrics 
                    without re-running the search.
                    """)
                    
                    # Initialize sensitivity values in session state if they don't exist
                    if 'sensitivity_rate_perc' not in st.session_state:
                        st.session_state.sensitivity_rate_perc = float(st.session_state.run_config.get('interest_rate_decimal', 0.075) * 100)
                    
                    if 'sensitivity_expenses' not in st.session_state:
                        sample_price = 300000  # Use a sample price for default expenses
                        st.session_state.sensitivity_expenses = float(orchestrator.calculate_monthly_expenses(sample_price))
                    
                    if 'sensitivity_rent_adj_perc' not in st.session_state:
                        st.session_state.sensitivity_rent_adj_perc = 0.0
                        
                    # Create widget columns
                    col1, col2, col3 = st.columns(3)
                    
                    # Column 1: Interest Rate
                    with col1:
                        sensitivity_rate = st.slider(
                            "Interest Rate %",
                            min_value=1.0,
                            max_value=20.0,
                            value=float(st.session_state.sensitivity_rate_perc),
                            step=0.1,
                            key="sensitivity_rate_widget"
                        )
                        st.session_state.sensitivity_rate_perc = sensitivity_rate
                    
                    # Column 2: Monthly Expenses
                    with col2:
                        sensitivity_expenses = st.number_input(
                            "Monthly Expenses ($)",
                            min_value=0.0,
                            value=float(st.session_state.sensitivity_expenses),
                            step=25.0,
                            format="%.2f",
                            key="sensitivity_expenses_widget"
                        )
                        st.session_state.sensitivity_expenses = sensitivity_expenses
                    
                    # Column 3: Rent Adjustment
                    with col3:
                        sensitivity_rent_adj = st.slider(
                            "Rent Adjustment %",
                            min_value=-20.0,
                            max_value=20.0,
                            value=float(st.session_state.sensitivity_rent_adj_perc),
                            step=1.0,
                            key="sensitivity_rent_adj_widget"
                        )
                        st.session_state.sensitivity_rent_adj_perc = sensitivity_rent_adj
                    
                    # Create button columns
                    btn_col1, btn_col2 = st.columns(2)
                    
                    with btn_col1:
                        # Create recalculation button
                        recalc_button = st.button("Recalculate Metrics", type="primary")
                    
                    with btn_col2:
                        # Create reset button
                        reset_button = st.button("Reset to Original Values", type="secondary")
                    
                    # Handle reset button
                    if reset_button:
                        # Reset sensitivity values to original
                        st.session_state.sensitivity_rate_perc = float(st.session_state.run_config.get('interest_rate_decimal', 0.075) * 100)
                        sample_price = 300000
                        st.session_state.sensitivity_expenses = float(orchestrator.calculate_monthly_expenses(sample_price))
                        st.session_state.sensitivity_rent_adj_perc = 0.0
                        
                        # Clear recalculated results
                        if 'recalculated_results' in st.session_state:
                            del st.session_state.recalculated_results
                        
                        # Rerun the app to update the UI
                        st.rerun()
                    
                    # Handle recalculation button
                    if recalc_button:
                        # Create config overrides dictionary
                        config_overrides = {
                            'interest_rate_decimal': st.session_state.sensitivity_rate_perc / 100.0,
                            'down_payment_percent': st.session_state.run_config.get('down_payment_percent', 0.20),
                            'loan_term_years': st.session_state.run_config.get('loan_term_years', 30),
                            'monthly_expenses': st.session_state.sensitivity_expenses,
                            'rent_adjustment_percent': st.session_state.sensitivity_rent_adj_perc
                        }
                        
                        # Convert original results to DataFrame
                        original_df = pd.DataFrame(st.session_state.original_results)
                        
                        # Recalculate metrics based on new parameters
                        recalculated_df = recalculate_metrics(original_df, config_overrides)
                        
                        # Store the recalculated results in session state
                        st.session_state.recalculated_results = recalculated_df.to_dict('records')
                        
                        # Use the recalculated results instead of original
                        df = pd.DataFrame(st.session_state.recalculated_results)
                        
                        # Add selection column
                        df.insert(0, "Select", False)
                        
                        # Keep the original zillow_url
                        df['link'] = df['zillow_url'] if 'zillow_url' in df.columns else None
                        
                        # Apply same column mappings as before
                        column_mapping = {
                            'address': 'Address',
                            'price': 'Price',
                            'bedrooms': 'Beds',
                            'bathrooms': 'Baths',
                            'sqft': 'Sq Ft',
                            'year_built': 'Year Built',
                            'property_type': 'Type',
                            'estimated_rent': 'Est. Rent',
                            'estimated_mortgage': 'Est. Mortgage',
                            'monthly_expenses': 'Monthly Expenses',
                            'estimated_monthly_cash_flow': 'Monthly Cash Flow',
                            'estimated_annual_cash_flow': 'Annual Cash Flow',
                            'estimated_coc_return': 'CoC Return %',
                            'zip_code': 'ZIP Code',
                            'zillow_url': 'Zillow Link'
                        }
                        
                        # Rename columns that exist in the DataFrame
                        existing_columns = [col for col in column_mapping.keys() if col in df.columns]
                        df = df.rename(columns={col: column_mapping[col] for col in existing_columns})
                        
                        # Store the unformatted DataFrame for adding to shortlist
                        unformatted_df = df.copy()
                        
                        # Format currency and percentage columns
                        for col in df.columns:
                            if col in ['Price', 'Est. Rent', 'Est. Mortgage', 'Monthly Expenses', 
                                       'Monthly Cash Flow', 'Annual Cash Flow']:
                                df[col] = df[col].apply(format_currency)
                            elif col in ['CoC Return %']:
                                df[col] = df[col].apply(format_percentage)
                        
                        # Display a notification to show recalculation is complete
                        st.success("Metrics recalculated with new parameters!")
            
            # Display dataframe as an editable data editor
            edited_df = st.data_editor(
                df,
                column_config={
                    "Select": st.column_config.CheckboxColumn(required=True),
                    "Zillow Link": st.column_config.LinkColumn("Zillow Link", display_text="View")
                },
                disabled=df.columns.difference(["Select"]),  # Make only 'Select' editable
                hide_index=True,
                use_container_width=True,
                key="results_editor"
            )
            
            # Add selected properties to shortlist
            selected_rows = edited_df[edited_df.Select]
            
            if st.button("Add Selected to Shortlist"):
                added_count = 0
                
                for index, row in selected_rows.iterrows():
                    # Use original data for the shortlist (not formatted)
                    original_row = unformatted_df.loc[index]
                    
                    # Use Zillow link as a unique identifier
                    property_link = original_row.get('link')
                    
                    # Check if property is already in shortlist
                    is_already_shortlisted = any(
                        item.get('link') == property_link 
                        for item in st.session_state.shortlist
                    )
                    
                    if not is_already_shortlisted and property_link is not None:
                        # Convert row to dictionary and add notes field
                        new_item = original_row.to_dict()
                        new_item['notes'] = ""
                        
                        # Add to shortlist
                        st.session_state.shortlist.append(new_item)
                        added_count += 1
                
                # Save shortlist and show success/warning message
                if added_count > 0:
                    save_shortlist(st.session_state.shortlist)
                    st.success(f"Added {added_count} properties to shortlist.")
                else:
                    st.warning("Selected properties are already in the shortlist or none selected.")
            
            # Add download button
            csv_data = convert_df_to_csv(df)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv_data,
                file_name="real_estate_deals_filtered.csv",
                mime="text/csv"
            )
            
            # Display metrics comparison if recalculated results exist
            if 'recalculated_results' in st.session_state and 'original_results' in st.session_state:
                with st.expander("📈 Metrics Comparison (Original vs Recalculated)"):
                    # Create DataFrames for comparison
                    original_df = pd.DataFrame(st.session_state.original_results)
                    recalc_df = pd.DataFrame(st.session_state.recalculated_results)
                    
                    # Create comparison metrics
                    if not original_df.empty and not recalc_df.empty:
                        # Calculate averages for key metrics
                        comparison_data = {
                            "Metric": [
                                "Avg. Monthly Mortgage", 
                                "Avg. Monthly Cash Flow", 
                                "Avg. Annual Cash Flow",
                                "Avg. Cash-on-Cash Return"
                            ],
                            "Original": [
                                original_df['estimated_mortgage'].mean(),
                                original_df['estimated_monthly_cash_flow'].mean(),
                                original_df['estimated_annual_cash_flow'].mean(),
                                original_df['estimated_coc_return'].mean()
                            ],
                            "Recalculated": [
                                recalc_df['estimated_mortgage'].mean(),
                                recalc_df['estimated_monthly_cash_flow'].mean(),
                                recalc_df['estimated_annual_cash_flow'].mean(),
                                recalc_df['estimated_coc_return'].mean()
                            ]
                        }
                        
                        # Create a comparison DataFrame
                        comparison_df = pd.DataFrame(comparison_data)
                        
                        # Add a difference column
                        comparison_df["Difference"] = comparison_df["Recalculated"] - comparison_df["Original"]
                        comparison_df["Change %"] = (comparison_df["Difference"] / comparison_df["Original"]) * 100
                        
                        # Format the values for display
                        for col in ["Original", "Recalculated", "Difference"]:
                            comparison_df[col] = comparison_df.apply(
                                lambda row: format_currency(row[col]) if row["Metric"] in [
                                    "Avg. Monthly Mortgage", 
                                    "Avg. Monthly Cash Flow", 
                                    "Avg. Annual Cash Flow"
                                ] else format_percentage(row[col]), 
                                axis=1
                            )
                        
                        # Format the change percentage
                        comparison_df["Change %"] = comparison_df["Change %"].apply(
                            lambda x: f"{x:+.2f}%" if not pd.isna(x) else "N/A"
                        )
                        
                        # Display the comparison table
                        st.table(comparison_df)
                        
                        # Display parameter changes
                        st.subheader("Parameter Changes")
                        
                        # Get original and new parameters
                        orig_params = st.session_state.run_config
                        
                        # Display changes
                        params_data = {
                            "Parameter": [
                                "Interest Rate",
                                "Monthly Expenses",
                                "Rent Adjustment"
                            ],
                            "Original": [
                                f"{orig_params.get('interest_rate_decimal', 0.075) * 100:.1f}%",
                                f"${orig_params.get('monthly_expenses', 0)}",
                                "0.0%"
                            ],
                            "New": [
                                f"{st.session_state.sensitivity_rate_perc:.1f}%",
                                f"${st.session_state.sensitivity_expenses:.2f}",
                                f"{st.session_state.sensitivity_rent_adj_perc:+.1f}%"
                            ]
                        }
                        
                        # Create and display parameter comparison
                        params_df = pd.DataFrame(params_data)
                        st.table(params_df)
            
            st.success(f"Found {len(filtered_results)} properties meeting your criteria!")
        else:
            st.warning("No data returned from analysis.")
    else:
        st.warning("No properties found matching the specified criteria.")
        st.info("""
        Try adjusting your filter criteria in the sidebar:
        - Lower the minimum cash-on-cash return
        - Lower the minimum monthly cash flow
        - Check different ZIP codes
        """)

# Shortlist Section
st.header("⭐ My Shortlist")

if not st.session_state.shortlist:
    st.info("Your shortlist is currently empty. Select properties from the results and click 'Add Selected to Shortlist'.")
else:
    st.caption(f"You have {len(st.session_state.shortlist)} properties in your shortlist.")
    
    # Add search functionality
    search_term = st.text_input("🔍 Search shortlist by address:", placeholder="Enter address keywords...")
    
    # Show counts when filtering
    if search_term:
        # Count properties that match the search term
        matching_count = sum(1 for item in st.session_state.shortlist 
                           if search_term.lower() in str(item.get('Address', item.get('address', ''))).lower())
        st.caption(f"Showing {matching_count} of {len(st.session_state.shortlist)} properties matching '{search_term}'.")
    
    # Create tabs for sorting options
    shortlist_tab1, shortlist_tab2, shortlist_tab3 = st.tabs(["Sort by Price", "Sort by Cash Flow", "Sort by CoC Return"])
    
    with shortlist_tab1:
        # Filter the shortlist by search term
        filtered_shortlist = st.session_state.shortlist
        if search_term:
            filtered_shortlist = [
                item for item in st.session_state.shortlist
                if search_term.lower() in str(item.get('Address', item.get('address', ''))).lower()
            ]
        
        # Sort the filtered shortlist by price
        sorted_shortlist = sorted(filtered_shortlist, key=lambda x: x.get('price', 0), reverse=True)
        
        # Add clear all button
        if st.button("Clear All Shortlisted Properties", type="secondary"):
            if st.session_state.shortlist:
                # Ask for confirmation
                if st.warning("Are you sure you want to remove all properties from your shortlist?"):
                    # Clear the shortlist
                    st.session_state.shortlist = []
                    save_shortlist([])
                    st.success("Shortlist cleared!")
                    st.rerun()
        
        # Display each property in an expander
        for index, item in enumerate(sorted_shortlist):
            # Create a detailed title for the expander
            address = item.get('Address', item.get('address', f'Property {index+1}'))
            price = item.get('Price', item.get('price', 'Unknown'))
            if isinstance(price, str) and price.startswith('$'):
                price_display = price
            else:
                price_display = f"${price:,.2f}" if price and not isinstance(price, str) else price
            
            expander_title = f"{address} - {price_display}"
            
            with st.expander(expander_title):
                # Create two columns for layout
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Display key property details
                    st.markdown("**Property Details:**")
                    
                    # Get raw values for bedrooms and bathrooms
                    beds = item.get('Beds', item.get('bedrooms', 'N/A'))
                    baths = item.get('Baths', item.get('bathrooms', 'N/A'))
                    
                    # Get and format financial values
                    rent = item.get('Est. Rent', item.get('estimated_rent', 'N/A'))
                    rent_display = f"${rent:,.2f}" if rent and not isinstance(rent, str) else rent
                    
                    mortgage = item.get('Est. Mortgage', item.get('estimated_mortgage', 'N/A'))
                    mortgage_display = f"${mortgage:,.2f}" if mortgage and not isinstance(mortgage, str) else mortgage
                    
                    cash_flow = item.get('Monthly Cash Flow', item.get('estimated_monthly_cash_flow', 'N/A'))
                    cash_flow_display = f"${cash_flow:,.2f}" if cash_flow and not isinstance(cash_flow, str) else cash_flow
                    
                    coc_return = item.get('CoC Return %', item.get('estimated_coc_return', 'N/A'))
                    coc_display = f"{coc_return:.2f}%" if coc_return and not isinstance(coc_return, str) else coc_return
                    
                    # Display the details
                    st.markdown(f"**Beds/Baths:** {beds}/{baths}")
                    st.markdown(f"**Monthly Rent:** {rent_display}")
                    st.markdown(f"**Monthly Mortgage:** {mortgage_display}")
                    st.markdown(f"**Monthly Cash Flow:** {cash_flow_display}")
                    st.markdown(f"**Cash-on-Cash Return:** {coc_display}")
                
                with col2:
                    # Display Zillow link
                    zillow_link = item.get('Zillow Link', item.get('zillow_url', item.get('link', '#')))
                    if zillow_link and zillow_link != '#':
                        st.markdown(f"[View on Zillow]({zillow_link})")
                    
                    # Create a unique key for each property's remove button
                    remove_key = f"remove_{item.get('link', index)}"
                    
                    # Add remove button
                    if st.button("Remove from Shortlist", key=remove_key):
                        # Find the item in the actual session state list
                        for i, shortlist_item in enumerate(st.session_state.shortlist):
                            if shortlist_item.get('link') == item.get('link'):
                                # Remove the item
                                st.session_state.shortlist.pop(i)
                                # Save the updated shortlist
                                save_shortlist(st.session_state.shortlist)
                                # Rerun the app to update the display
                                st.rerun()
                                break
                
                # Notes section (full width)
                st.markdown("**Notes:**")
                
                # Create a unique key for each property's notes
                note_key = f"note_{item.get('link', index)}"
                
                # Get current notes
                current_note = item.get('notes', '')
                
                # Create the notes text area
                new_note = st.text_area(
                    "Add your notes here:",
                    value=current_note,
                    key=note_key,
                    height=100,
                    label_visibility="collapsed"
                )
                
                # If notes have changed, update them
                if new_note != current_note:
                    # Find the item in the actual session state list
                    for i, shortlist_item in enumerate(st.session_state.shortlist):
                        if shortlist_item.get('link') == item.get('link'):
                            # Update the notes
                            st.session_state.shortlist[i]['notes'] = new_note
                            # Save the updated shortlist
                            save_shortlist(st.session_state.shortlist)
                            # No need to rerun here as text areas update without rerunning
                            break
    
    with shortlist_tab2:
        # Filter the shortlist by search term
        filtered_shortlist = st.session_state.shortlist
        if search_term:
            filtered_shortlist = [
                item for item in st.session_state.shortlist
                if search_term.lower() in str(item.get('Address', item.get('address', ''))).lower()
            ]
        
        # Sort the filtered shortlist by monthly cash flow (descending)
        sorted_shortlist = sorted(
            filtered_shortlist, 
            key=lambda x: x.get('estimated_monthly_cash_flow', 0) 
                if isinstance(x.get('estimated_monthly_cash_flow'), (int, float)) else -9999, 
            reverse=True
        )
        
        # Display message if empty
        if not sorted_shortlist:
            st.info("No properties in your shortlist.")
        else:
            # Display each property in an expander
            for index, item in enumerate(sorted_shortlist):
                # Create a detailed title for the expander
                address = item.get('Address', item.get('address', f'Property {index+1}'))
                price = item.get('Price', item.get('price', 'Unknown'))
                if isinstance(price, str) and price.startswith('$'):
                    price_display = price
                else:
                    price_display = f"${price:,.2f}" if price and not isinstance(price, str) else price
                
                expander_title = f"{address} - {price_display}"
                
                with st.expander(expander_title):
                    # Create two columns for layout
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Display key property details
                        st.markdown("**Property Details:**")
                        
                        # Get raw values for bedrooms and bathrooms
                        beds = item.get('Beds', item.get('bedrooms', 'N/A'))
                        baths = item.get('Baths', item.get('bathrooms', 'N/A'))
                        
                        # Get and format financial values
                        rent = item.get('Est. Rent', item.get('estimated_rent', 'N/A'))
                        rent_display = f"${rent:,.2f}" if rent and not isinstance(rent, str) else rent
                        
                        mortgage = item.get('Est. Mortgage', item.get('estimated_mortgage', 'N/A'))
                        mortgage_display = f"${mortgage:,.2f}" if mortgage and not isinstance(mortgage, str) else mortgage
                        
                        cash_flow = item.get('Monthly Cash Flow', item.get('estimated_monthly_cash_flow', 'N/A'))
                        cash_flow_display = f"${cash_flow:,.2f}" if cash_flow and not isinstance(cash_flow, str) else cash_flow
                        
                        coc_return = item.get('CoC Return %', item.get('estimated_coc_return', 'N/A'))
                        coc_display = f"{coc_return:.2f}%" if coc_return and not isinstance(coc_return, str) else coc_return
                        
                        # Display the details
                        st.markdown(f"**Beds/Baths:** {beds}/{baths}")
                        st.markdown(f"**Monthly Rent:** {rent_display}")
                        st.markdown(f"**Monthly Mortgage:** {mortgage_display}")
                        st.markdown(f"**Monthly Cash Flow:** {cash_flow_display}")
                        st.markdown(f"**Cash-on-Cash Return:** {coc_display}")
                    
                    with col2:
                        # Display Zillow link
                        zillow_link = item.get('Zillow Link', item.get('zillow_url', item.get('link', '#')))
                        if zillow_link and zillow_link != '#':
                            st.markdown(f"[View on Zillow]({zillow_link})")
                        
                        # Create a unique key for each property's remove button
                        remove_key = f"remove_{item.get('link', index)}_cf"
                        
                        # Add remove button
                        if st.button("Remove from Shortlist", key=remove_key):
                            # Find the item in the actual session state list
                            for i, shortlist_item in enumerate(st.session_state.shortlist):
                                if shortlist_item.get('link') == item.get('link'):
                                    # Remove the item
                                    st.session_state.shortlist.pop(i)
                                    # Save the updated shortlist
                                    save_shortlist(st.session_state.shortlist)
                                    # Rerun the app to update the display
                                    st.rerun()
                                    break
                    
                    # Notes section (full width)
                    st.markdown("**Notes:**")
                    
                    # Create a unique key for each property's notes
                    note_key = f"note_{item.get('link', index)}_cf"
                    
                    # Get current notes
                    current_note = item.get('notes', '')
                    
                    # Create the notes text area
                    new_note = st.text_area(
                        "Add your notes here:",
                        value=current_note,
                        key=note_key,
                        height=100,
                        label_visibility="collapsed"
                    )
                    
                    # If notes have changed, update them
                    if new_note != current_note:
                        # Find the item in the actual session state list
                        for i, shortlist_item in enumerate(st.session_state.shortlist):
                            if shortlist_item.get('link') == item.get('link'):
                                # Update the notes
                                st.session_state.shortlist[i]['notes'] = new_note
                                # Save the updated shortlist
                                save_shortlist(st.session_state.shortlist)
                                # No need to rerun here as text areas update without rerunning
                                break
    
    with shortlist_tab3:
        # Filter the shortlist by search term
        filtered_shortlist = st.session_state.shortlist
        if search_term:
            filtered_shortlist = [
                item for item in st.session_state.shortlist
                if search_term.lower() in str(item.get('Address', item.get('address', ''))).lower()
            ]
        
        # Sort the filtered shortlist by CoC return (descending)
        sorted_shortlist = sorted(
            filtered_shortlist, 
            key=lambda x: x.get('estimated_coc_return', 0) 
                if isinstance(x.get('estimated_coc_return'), (int, float)) else -9999, 
            reverse=True
        )
        
        # Display message if empty
        if not sorted_shortlist:
            st.info("No properties in your shortlist.")
        else:
            # Display each property in an expander
            for index, item in enumerate(sorted_shortlist):
                # Create a detailed title for the expander
                address = item.get('Address', item.get('address', f'Property {index+1}'))
                price = item.get('Price', item.get('price', 'Unknown'))
                if isinstance(price, str) and price.startswith('$'):
                    price_display = price
                else:
                    price_display = f"${price:,.2f}" if price and not isinstance(price, str) else price
                
                expander_title = f"{address} - {price_display}"
                
                with st.expander(expander_title):
                    # Create two columns for layout
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Display key property details
                        st.markdown("**Property Details:**")
                        
                        # Get raw values for bedrooms and bathrooms
                        beds = item.get('Beds', item.get('bedrooms', 'N/A'))
                        baths = item.get('Baths', item.get('bathrooms', 'N/A'))
                        
                        # Get and format financial values
                        rent = item.get('Est. Rent', item.get('estimated_rent', 'N/A'))
                        rent_display = f"${rent:,.2f}" if rent and not isinstance(rent, str) else rent
                        
                        mortgage = item.get('Est. Mortgage', item.get('estimated_mortgage', 'N/A'))
                        mortgage_display = f"${mortgage:,.2f}" if mortgage and not isinstance(mortgage, str) else mortgage
                        
                        cash_flow = item.get('Monthly Cash Flow', item.get('estimated_monthly_cash_flow', 'N/A'))
                        cash_flow_display = f"${cash_flow:,.2f}" if cash_flow and not isinstance(cash_flow, str) else cash_flow
                        
                        coc_return = item.get('CoC Return %', item.get('estimated_coc_return', 'N/A'))
                        coc_display = f"{coc_return:.2f}%" if coc_return and not isinstance(coc_return, str) else coc_return
                        
                        # Display the details
                        st.markdown(f"**Beds/Baths:** {beds}/{baths}")
                        st.markdown(f"**Monthly Rent:** {rent_display}")
                        st.markdown(f"**Monthly Mortgage:** {mortgage_display}")
                        st.markdown(f"**Monthly Cash Flow:** {cash_flow_display}")
                        st.markdown(f"**Cash-on-Cash Return:** {coc_display}")
                    
                    with col2:
                        # Display Zillow link
                        zillow_link = item.get('Zillow Link', item.get('zillow_url', item.get('link', '#')))
                        if zillow_link and zillow_link != '#':
                            st.markdown(f"[View on Zillow]({zillow_link})")
                        
                        # Create a unique key for each property's remove button
                        remove_key = f"remove_{item.get('link', index)}_coc"
                        
                        # Add remove button
                        if st.button("Remove from Shortlist", key=remove_key):
                            # Find the item in the actual session state list
                            for i, shortlist_item in enumerate(st.session_state.shortlist):
                                if shortlist_item.get('link') == item.get('link'):
                                    # Remove the item
                                    st.session_state.shortlist.pop(i)
                                    # Save the updated shortlist
                                    save_shortlist(st.session_state.shortlist)
                                    # Rerun the app to update the display
                                    st.rerun()
                                    break
                    
                    # Notes section (full width)
                    st.markdown("**Notes:**")
                    
                    # Create a unique key for each property's notes
                    note_key = f"note_{item.get('link', index)}_coc"
                    
                    # Get current notes
                    current_note = item.get('notes', '')
                    
                    # Create the notes text area
                    new_note = st.text_area(
                        "Add your notes here:",
                        value=current_note,
                        key=note_key,
                        height=100,
                        label_visibility="collapsed"
                    )
                    
                    # If notes have changed, update them
                    if new_note != current_note:
                        # Find the item in the actual session state list
                        for i, shortlist_item in enumerate(st.session_state.shortlist):
                            if shortlist_item.get('link') == item.get('link'):
                                # Update the notes
                                st.session_state.shortlist[i]['notes'] = new_note
                                # Save the updated shortlist
                                save_shortlist(st.session_state.shortlist)
                                # No need to rerun here as text areas update without rerunning
                                break

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center">
<p>Real Estate Deal Finder | Made with Streamlit | Data from Zillow & RentCast</p>
</div>
""", unsafe_allow_html=True)