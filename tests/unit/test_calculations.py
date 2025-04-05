"""
Unit tests for the financial calculation functions.

Tests for calculate_monthly_mortgage, calculate_cash_flow, and calculate_coc_return
functions in the calculations module.
"""

import pytest
from src.real_estate_deal_finder.calculations import (
    calculate_monthly_mortgage,
    calculate_cash_flow,
    calculate_coc_return
)


class TestCalculateMonthlyMortgage:
    """Tests for the calculate_monthly_mortgage function."""
    
    def test_basic_calculation(self):
        """Test a standard mortgage calculation with typical values."""
        # $300,000 loan with 20% down, 4.5% interest, 30-year term
        result = calculate_monthly_mortgage(
            total_price=300000,
            down_payment_percent=0.20,
            interest_rate_decimal=0.045,
            loan_term_years=30
        )
        
        # Expected result is around $1216.04
        assert round(result, 2) == 1216.04
    
    def test_zero_loan_amount(self):
        """Test when the loan amount is zero (100% down payment)."""
        result = calculate_monthly_mortgage(
            total_price=300000,
            down_payment_percent=1.0,  # 100% down payment
            interest_rate_decimal=0.045,
            loan_term_years=30
        )
        
        assert result == 0.0
    
    def test_zero_interest_rate(self):
        """Test when the interest rate is zero (interest-free loan)."""
        result = calculate_monthly_mortgage(
            total_price=300000,
            down_payment_percent=0.20,
            interest_rate_decimal=0.0,
            loan_term_years=30
        )
        
        # Simple division: loan amount / number of months
        expected = (300000 * 0.8) / (30 * 12)
        assert result == expected
    
    def test_invalid_loan_term(self):
        """Test when the loan term is invalid (zero or negative)."""
        result = calculate_monthly_mortgage(
            total_price=300000,
            down_payment_percent=0.20,
            interest_rate_decimal=0.045,
            loan_term_years=0
        )
        
        assert result is None
        
        result = calculate_monthly_mortgage(
            total_price=300000,
            down_payment_percent=0.20,
            interest_rate_decimal=0.045,
            loan_term_years=-10
        )
        
        assert result is None
    
    def test_edge_cases(self):
        """Test additional edge cases."""
        # Negative price
        result = calculate_monthly_mortgage(
            total_price=-300000,
            down_payment_percent=0.20,
            interest_rate_decimal=0.045,
            loan_term_years=30
        )
        
        # Should return 0.0 as loan amount is negative
        assert result == 0.0
        
        # Very high interest rate
        result = calculate_monthly_mortgage(
            total_price=300000,
            down_payment_percent=0.20,
            interest_rate_decimal=1.0,  # 100% interest
            loan_term_years=30
        )
        
        # Should still return a valid result
        assert result > 0


class TestCalculateCashFlow:
    """Tests for the calculate_cash_flow function."""
    
    def test_positive_cash_flow(self):
        """Test when rent exceeds mortgage and expenses (positive cash flow)."""
        result = calculate_cash_flow(
            monthly_rent=2000,
            monthly_mortgage=1500,
            monthly_expenses=300
        )
        
        assert result == 200
    
    def test_negative_cash_flow(self):
        """Test when mortgage and expenses exceed rent (negative cash flow)."""
        result = calculate_cash_flow(
            monthly_rent=2000,
            monthly_mortgage=1800,
            monthly_expenses=500
        )
        
        assert result == -300
    
    def test_breakeven_cash_flow(self):
        """Test when rent exactly equals mortgage plus expenses (breakeven)."""
        result = calculate_cash_flow(
            monthly_rent=2000,
            monthly_mortgage=1500,
            monthly_expenses=500
        )
        
        assert result == 0
    
    def test_none_inputs(self):
        """Test when rent or mortgage is None."""
        result = calculate_cash_flow(
            monthly_rent=None,
            monthly_mortgage=1500,
            monthly_expenses=300
        )
        
        assert result is None
        
        result = calculate_cash_flow(
            monthly_rent=2000,
            monthly_mortgage=None,
            monthly_expenses=300
        )
        
        assert result is None


class TestCalculateCoCReturn:
    """Tests for the calculate_coc_return function."""
    
    def test_positive_coc_return(self):
        """Test when annual cash flow is positive (positive CoC return)."""
        result = calculate_coc_return(
            total_price=300000,
            down_payment_percent=0.20,
            annual_cash_flow=6000
        )
        
        # $6000 / $60000 = 0.10 or 10%
        assert result == 10.0
    
    def test_negative_coc_return(self):
        """Test when annual cash flow is negative (negative CoC return)."""
        result = calculate_coc_return(
            total_price=300000,
            down_payment_percent=0.20,
            annual_cash_flow=-3000
        )
        
        # -$3000 / $60000 = -0.05 or -5%
        assert result == -5.0
    
    def test_zero_coc_return(self):
        """Test when annual cash flow is zero (zero CoC return)."""
        result = calculate_coc_return(
            total_price=300000,
            down_payment_percent=0.20,
            annual_cash_flow=0
        )
        
        assert result == 0.0
    
    def test_invalid_inputs(self):
        """Test invalid inputs."""
        # Zero down payment
        result = calculate_coc_return(
            total_price=300000,
            down_payment_percent=0.0,
            annual_cash_flow=6000
        )
        
        assert result is None
        
        # None annual cash flow
        result = calculate_coc_return(
            total_price=300000,
            down_payment_percent=0.20,
            annual_cash_flow=None
        )
        
        assert result is None