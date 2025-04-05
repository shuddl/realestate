"""
Financial calculation functions for the Real Estate Deal Finder application.

This module contains pure functions for calculating mortgage payments,
cash flow, and cash-on-cash return for rental property investments.
"""

import math
from typing import Optional


def calculate_monthly_mortgage(
    total_price: float,
    down_payment_percent: float,
    interest_rate_decimal: float,
    loan_term_years: int
) -> Optional[float]:
    """
    Calculate the monthly mortgage payment using the standard mortgage formula.
    
    Formula:
    M = P * [r(1+r)^n] / [(1+r)^n - 1]
    
    Where:
    - M = monthly payment
    - P = loan amount (total_price * (1 - down_payment_percent))
    - r = monthly interest rate (annual_rate / 12)
    - n = number of payments (loan_term_years * 12)
    
    Args:
        total_price: The total purchase price of the property
        down_payment_percent: The down payment as a decimal (e.g., 0.2 for 20%)
        interest_rate_decimal: The annual interest rate as a decimal (e.g., 0.045 for 4.5%)
        loan_term_years: The loan term in years
        
    Returns:
        The monthly mortgage payment as a float, 0.0 if loan amount is 0,
        or None if inputs are invalid or calculation errors occur
        
    Edge Cases:
        - If loan_amount <= 0: Returns 0.0
        - If loan_term_years <= 0: Returns None
        - If interest_rate_decimal == 0: Returns loan_amount / (loan_term_years * 12)
    """
    # Calculate loan amount
    loan_amount = total_price * (1.0 - down_payment_percent)
    
    # Edge case: No loan needed
    if loan_amount <= 0:
        return 0.0
    
    # Edge case: Invalid loan term
    if loan_term_years <= 0:
        return None
    
    # Edge case: Zero interest rate (simple division)
    if interest_rate_decimal == 0:
        return loan_amount / (loan_term_years * 12)
    
    # Standard mortgage calculation
    try:
        monthly_interest_rate = interest_rate_decimal / 12.0
        number_of_payments = loan_term_years * 12
        
        # Calculate monthly payment using the mortgage formula
        numerator = monthly_interest_rate * math.pow(1 + monthly_interest_rate, number_of_payments)
        denominator = math.pow(1 + monthly_interest_rate, number_of_payments) - 1
        monthly_payment = loan_amount * (numerator / denominator)
        
        return monthly_payment
    except (OverflowError, ValueError, ZeroDivisionError):
        # Return None if calculation errors occur
        return None


def calculate_cash_flow(
    monthly_rent: Optional[float],
    monthly_mortgage: Optional[float],
    monthly_expenses: float
) -> Optional[float]:
    """
    Calculate the monthly cash flow for a rental property.
    
    Cash flow is defined as: monthly_rent - monthly_mortgage - monthly_expenses
    
    Args:
        monthly_rent: The monthly rental income
        monthly_mortgage: The monthly mortgage payment
        monthly_expenses: The total monthly expenses (property taxes, insurance, 
                         HOA, property management, maintenance, vacancy, etc.)
        
    Returns:
        The monthly cash flow as a float, or None if monthly_rent or monthly_mortgage is None
    """
    # Check if required inputs are available
    if monthly_rent is None or monthly_mortgage is None:
        return None
    
    # Calculate cash flow
    cash_flow = monthly_rent - monthly_mortgage - monthly_expenses
    
    return cash_flow


def calculate_coc_return(
    total_price: float,
    down_payment_percent: float,
    annual_cash_flow: Optional[float]
) -> Optional[float]:
    """
    Calculate the cash-on-cash (CoC) return percentage for a rental property investment.
    
    Cash-on-cash return is defined as: (annual_cash_flow / cash_invested) * 100
    
    Args:
        total_price: The total purchase price of the property
        down_payment_percent: The down payment as a decimal (e.g., 0.2 for 20%)
        annual_cash_flow: The annual cash flow (monthly_cash_flow * 12)
        
    Returns:
        The cash-on-cash return as a percentage, or None if inputs are invalid
        
    Edge Cases:
        - If cash_invested <= 0: Returns None
        - If annual_cash_flow is None: Returns None
    """
    # Calculate the cash invested (down payment)
    cash_invested = total_price * down_payment_percent
    
    # Edge case: Invalid cash invested
    if cash_invested <= 0:
        return None
    
    # Edge case: Invalid annual cash flow
    if annual_cash_flow is None:
        return None
    
    # Calculate CoC return as a decimal
    coc_return_decimal = annual_cash_flow / cash_invested
    
    # Convert to percentage
    coc_return_percent = coc_return_decimal * 100.0
    
    return coc_return_percent