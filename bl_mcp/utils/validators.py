"""Input validation utilities for Black-Litterman MCP server."""

from datetime import datetime
from typing import Optional


def validate_tickers(tickers: list[str]) -> None:
    """
    Validate ticker list.
    
    Args:
        tickers: List of ticker symbols
        
    Raises:
        ValueError: If tickers list is invalid
    """
    if not tickers:
        raise ValueError("Tickers list cannot be empty")
    
    if not isinstance(tickers, list):
        raise ValueError(f"Tickers must be a list, got {type(tickers)}")
    
    if not all(isinstance(t, str) for t in tickers):
        raise ValueError("All tickers must be strings")
    
    if len(tickers) != len(set(tickers)):
        raise ValueError("Duplicate tickers found")
    
    # Minimum 2 assets for portfolio optimization
    if len(tickers) < 2:
        raise ValueError("At least 2 tickers required for portfolio optimization")


def validate_date(date_str: str, param_name: str = "date") -> None:
    """
    Validate date string format.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        param_name: Parameter name for error messages
        
    Raises:
        ValueError: If date format is invalid
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(
            f"{param_name} must be in YYYY-MM-DD format, got '{date_str}'"
        ) from e


def validate_date_range(start_date: str, end_date: Optional[str] = None) -> None:
    """
    Validate date range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), optional
        
    Raises:
        ValueError: If date range is invalid
    """
    validate_date(start_date, "start_date")
    
    if end_date is not None:
        validate_date(end_date, "end_date")
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        if start >= end:
            raise ValueError(
                f"start_date ({start_date}) must be before end_date ({end_date})"
            )
        
        # Check if date range is reasonable (at least 60 days recommended)
        days_diff = (end - start).days
        if days_diff < 60:
            raise ValueError(
                f"Date range too short ({days_diff} days). "
                f"At least 60 days recommended for reliable estimates."
            )


def validate_confidence(confidence: float) -> None:
    """
    Validate confidence level.
    
    Args:
        confidence: Confidence level (0.0 to 1.0)
        
    Raises:
        ValueError: If confidence is out of range
    """
    if not isinstance(confidence, (int, float)):
        raise ValueError(f"Confidence must be numeric, got {type(confidence)}")
    
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            f"Confidence must be between 0.0 and 1.0, got {confidence}"
        )


def validate_risk_aversion(risk_aversion: Optional[float]) -> None:
    """
    Validate risk aversion parameter.
    
    Args:
        risk_aversion: Risk aversion coefficient (must be positive)
        
    Raises:
        ValueError: If risk aversion is invalid
    """
    if risk_aversion is not None:
        if not isinstance(risk_aversion, (int, float)):
            raise ValueError(
                f"Risk aversion must be numeric, got {type(risk_aversion)}"
            )
        
        if risk_aversion <= 0:
            raise ValueError(
                f"Risk aversion must be positive, got {risk_aversion}"
            )


def validate_view_dict(view_dict: dict, tickers: list[str]) -> None:
    """
    Validate investor view dictionary.
    
    Args:
        view_dict: Dictionary mapping tickers to expected returns
        tickers: Valid ticker list
        
    Raises:
        ValueError: If view dictionary is invalid
    """
    if not isinstance(view_dict, dict):
        raise ValueError(f"Views must be a dictionary, got {type(view_dict)}")
    
    if not view_dict:
        raise ValueError("View dictionary cannot be empty")
    
    # Check all keys are valid tickers
    invalid_tickers = set(view_dict.keys()) - set(tickers)
    if invalid_tickers:
        raise ValueError(
            f"Invalid tickers in views: {invalid_tickers}. "
            f"Valid tickers: {tickers}"
        )
    
    # Check all values are numeric
    for ticker, expected_return in view_dict.items():
        if not isinstance(expected_return, (int, float)):
            raise ValueError(
                f"Expected return for {ticker} must be numeric, "
                f"got {type(expected_return)}"
            )
        
        # Sanity check: expected returns should be reasonable (-100% to +1000%)
        if not -1.0 <= expected_return <= 10.0:
            raise ValueError(
                f"Expected return for {ticker} seems unreasonable: {expected_return}. "
                f"Should be between -1.0 (-100%) and 10.0 (+1000%)"
            )
