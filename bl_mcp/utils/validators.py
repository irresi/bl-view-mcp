"""Input validation utilities for Black-Litterman MCP server."""

import re
from datetime import datetime, timedelta
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


def parse_period(period: str) -> timedelta:
    """
    Parse relative period string to timedelta.
    
    Supports formats like:
    - "1D", "7D" (days)
    - "1W", "4W" (weeks)
    - "1M", "3M", "6M" (months, approximated as 30 days)
    - "1Y", "2Y", "5Y" (years, approximated as 365 days)
    
    Args:
        period: Period string (e.g., "1Y", "3M", "7D")
        
    Returns:
        timedelta object representing the period
        
    Raises:
        ValueError: If period format is invalid
    """
    match = re.match(r"^(\d+)([DWMY])$", period.upper())
    if not match:
        raise ValueError(
            f"Invalid period format: '{period}'. "
            f"Use format like '1Y', '3M', '1W', or '7D'"
        )
    
    amount, unit = int(match.group(1)), match.group(2)
    
    if unit == "D":
        return timedelta(days=amount)
    elif unit == "W":
        return timedelta(weeks=amount)
    elif unit == "M":
        # Approximate months as 30 days
        return timedelta(days=amount * 30)
    elif unit == "Y":
        # Approximate years as 365 days
        return timedelta(days=amount * 365)
    else:
        raise ValueError(f"Unsupported unit: {unit}")


def resolve_date_range(
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> tuple[str, str]:
    """
    Resolve date range from either period or absolute dates.
    
    This function follows the mutually exclusive parameter pattern:
    - Provide EITHER 'period' for recent data OR 'start_date' for historical data
    - If both provided, 'start_date' takes precedence (with warning)
    - If neither provided, defaults to '1Y' (1 year)
    
    Args:
        period: Relative period (e.g., '1Y', '3M', '1W', '7D')
        start_date: Absolute start date (YYYY-MM-DD)
        end_date: Absolute end date (YYYY-MM-DD), defaults to today
        
    Returns:
        Tuple of (start_date_str, end_date_str) in YYYY-MM-DD format
        
    Raises:
        ValueError: If date parameters are invalid
        
    Examples:
        >>> resolve_date_range(period="1Y")
        ('2024-11-22', '2025-11-22')  # 1 year back from today
        
        >>> resolve_date_range(start_date="2023-01-01", end_date="2024-01-01")
        ('2023-01-01', '2024-01-01')
        
        >>> resolve_date_range(start_date="2023-01-01")
        ('2023-01-01', '2025-11-22')  # today as end_date
    """
    # Determine end_date (default to today)
    if end_date:
        validate_date(end_date, "end_date")
        target_end = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        target_end = datetime.now()
    
    # Check for mutual exclusivity
    if start_date and period:
        # Warning: both provided, start_date takes precedence
        import warnings
        warnings.warn(
            "Both 'period' and 'start_date' provided. "
            "Using 'start_date' and ignoring 'period'. "
            "Provide EITHER 'period' OR 'start_date' for clarity.",
            UserWarning
        )
        period = None
    
    # Resolve start_date
    if start_date:
        # Absolute date mode
        validate_date(start_date, "start_date")
        target_start = datetime.strptime(start_date, "%Y-%m-%d")
    elif period:
        # Relative period mode
        period_delta = parse_period(period)
        target_start = target_end - period_delta
    else:
        # Default: 1 year back
        period_delta = parse_period("1Y")
        target_start = target_end - period_delta
    
    # Format as strings
    start_str = target_start.strftime("%Y-%m-%d")
    end_str = target_end.strftime("%Y-%m-%d")
    
    # Validate the resolved range
    validate_date_range(start_str, end_str)
    
    return start_str, end_str


def validate_confidence(confidence: float) -> float:
    """
    Validate and normalize confidence level.
    
    Accepts multiple input formats:
    - Decimal (0.0 to 1.0): 0.7, 0.5, 1.0
    - Percentage (5 to 100): 70, 50, 100 (automatically converted to 0.7, 0.5, 1.0)
    - Percentage string: "70%", "50%", "100%" (% symbol is stripped)
    - String numbers: "0.7", "70"
    
    Note: Values between 1 and 5 are ambiguous and rejected to avoid confusion.
    
    Natural Language Guide (for LLM conversion):
    =============================================
    LLMs should convert natural language expressions to numeric confidence:

    Confidence Scale (0.5 = neutral pivot point):
    - "very confident" / "certain" / "absolutely sure" -> 95 (95% or 1.0 for absolute certainty)
    - "confident" / "sure" / "pretty sure" -> 85 (85%)
    - "quite confident" / "fairly sure" -> 75 (75%)
    - "somewhat confident" / "slightly sure" -> 60 (60%)
    - "neutral" / "not sure" / "50-50" -> 50 (50% - neutral, no strong view)
    - "somewhat uncertain" / "not very sure" -> 40 (40%)
    - "uncertain" / "doubtful" -> 30 (30%)
    - "very uncertain" / "no confidence" -> 10 (10%)
    
    Default: 50 (50%) when views provided but confidence not specified
    
    Note: 0.5 is the neutral pivot - views with 50% confidence have minimal impact.
    Higher values (60-100%) strengthen the view, lower values (10-40%) weaken it.
    
    Args:
        confidence: Confidence level
                   - 0.0 to 1.0 for decimal
                   - 0 to 100 for percentage (auto-converted)
                   - String with % symbol: "70%"
        
    Returns:
        Normalized confidence as float (0.0 to 1.0)
        
    Raises:
        ValueError: If confidence is out of range or not convertible
        
    Examples:
        >>> validate_confidence(0.7)    # 0.7
        >>> validate_confidence(70)     # 0.7 (percentage auto-detected)
        >>> validate_confidence("70%")  # 0.7
        >>> validate_confidence("0.7")  # 0.7
    """
    original_input = confidence
    
    # Handle string inputs
    if isinstance(confidence, str):
        # Remove % symbol if present
        if "%" in confidence:
            confidence = confidence.replace("%", "").strip()
        
        # Try to convert to float
        try:
            confidence = float(confidence)
        except ValueError:
            raise ValueError(
                f"Confidence must be numeric or percentage string, got '{original_input}'"
            )
    
    # Check if it's numeric
    if not isinstance(confidence, (int, float)):
        raise ValueError(
            f"Confidence must be numeric, got {type(confidence).__name__}"
        )
    
    # Convert to float
    confidence = float(confidence)
    
    # Auto-detect percentage
    # - Values > 1.0 are assumed to be percentages
    # - But values between 1.0 and 5.0 are ambiguous (reject them)
    # - Values >= 5.0 and <= 100.0 are clear percentages
    if confidence > 1.0:
        if 1.0 < confidence < 5.0:
            # Ambiguous range - could be error or very low percentage
            raise ValueError(
                f"Ambiguous confidence value: {original_input}. "
                f"Use 0.0-1.0 (decimal) or 5-100 (percentage). "
                f"For {confidence}%, use {confidence}. For {confidence/100}, use {confidence/100}."
            )
        elif confidence <= 100.0:
            # Clear percentage range
            confidence = confidence / 100.0
        else:
            raise ValueError(
                f"Confidence must be 0-1 (decimal) or 5-100 (percentage), got {original_input}"
            )
    
    # Validate range
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            f"Confidence must be between 0.0 and 1.0 (or 0-100%), got {original_input}"
        )
    
    return confidence


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
    
    IMPORTANT: views must be a DICTIONARY mapping ticker symbols to expected returns.
    
    Correct format:
        {"AAPL": 0.10, "MSFT": 0.05}  ✅
        {"AAPL": 0.30}                 ✅
    
    WRONG formats:
        0.10                           ❌ (single number, not dict)
        "AAPL"                         ❌ (string, not dict)
        ["AAPL", 0.10]                ❌ (list, not dict)
    
    Args:
        view_dict: Dictionary mapping tickers to expected returns (decimals)
                  Example: {"AAPL": 0.10} means "AAPL expected to return 10%"
        tickers: Valid ticker list
        
    Raises:
        ValueError: If view dictionary is invalid
    """
    if not isinstance(view_dict, dict):
        raise ValueError(
            f"Views must be a DICTIONARY, got {type(view_dict).__name__}.\n"
            f"Correct format: {{'AAPL': 0.10, 'MSFT': 0.05}}\n"
            f"You provided: {view_dict}"
        )
    
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
