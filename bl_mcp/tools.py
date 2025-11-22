"""Black-Litterman portfolio optimization tools using PyPortfolioOpt."""

from typing import Optional

import numpy as np
import pandas as pd
from pypfopt import black_litterman, expected_returns, risk_models
from pypfopt.black_litterman import BlackLittermanModel

from .utils import data_loader, validators


def _parse_views(views: dict, tickers: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert view formats to P, Q matrices.
    
    Supports two formats:
    1. Dict-based P: {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
       - Absolute view: {"P": [{"AAPL": 1}], "Q": [0.10]}
       - Relative view: {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
    2. NumPy P: {"P": [[1, -1, 0]], "Q": [0.20]}
    
    Args:
        views: Views in P, Q format (dict or NumPy)
        tickers: List of ticker symbols in portfolio
        
    Returns:
        Tuple of (P matrix, Q vector) as numpy arrays
        
    Raises:
        ValueError: If views format is invalid or contains unknown tickers
    """
    # Ensure P, Q format is used
    if "P" not in views or "Q" not in views:
        raise ValueError(
            "Views must use P, Q format. "
            "Examples:\n"
            "  Absolute view: {'P': [{'AAPL': 1}], 'Q': [0.10]}\n"
            "  Relative view: {'P': [{'NVDA': 1, 'AAPL': -1}], 'Q': [0.20]}\n"
            "  NumPy format: {'P': [[1, -1, 0]], 'Q': [0.20]}"
        )
    
    # Parse P and Q
    P_input = views["P"]
    Q = np.array(views["Q"])
    
    # Validate Q
    if Q is None or len(Q) == 0:
        raise ValueError("Q cannot be empty")
    
    # Validate P
    if len(P_input) == 0:
        raise ValueError("P matrix cannot be empty")
    
    if isinstance(P_input[0], dict):
        # Dict-based P: [{"NVDA": 1, "AAPL": -1}, ...]
        P = np.zeros((len(P_input), len(tickers)))
        for i, view_dict in enumerate(P_input):
            for ticker, weight in view_dict.items():
                if ticker not in tickers:
                    raise ValueError(
                        f"Ticker '{ticker}' in P matrix not found in tickers list. "
                        f"Available tickers: {tickers}"
                    )
                j = tickers.index(ticker)
                P[i, j] = weight
    else:
        # NumPy P: [[1, -1, 0], ...]
        P = np.array(P_input)
        
        # Validate dimensions
        if P.shape[1] != len(tickers):
            raise ValueError(
                f"P matrix has {P.shape[1]} columns but there are {len(tickers)} tickers. "
                f"Dimensions must match."
            )
    
    # Validate P and Q dimensions match
    if P.shape[0] != len(Q):
        raise ValueError(
            f"P matrix has {P.shape[0]} rows but Q has {len(Q)} elements. "
            f"Number of views must match."
        )
    
    return P, Q


def _normalize_confidence(
    confidence: float | list | None,
    views: dict,
    tickers: list[str]
) -> list[float]:
    """
    Normalize confidence to list format.
    
    Handles confidence input types and converts to list:
    - None → [0.5, 0.5, ...] (default neutral confidence)
    - Float → [value, value, ...] (same confidence for all views)
    - List → validate and return (per-view confidence)
    
    Args:
        confidence: Confidence in float or list format
        views: Views dict (to determine number of views)
        tickers: List of tickers (unused, kept for compatibility)
        
    Returns:
        List of confidence values (one per view)
        
    Raises:
        ValueError: If confidence format is invalid or length doesn't match views
        TypeError: If confidence type is not supported
    """
    # Determine number of views from Q
    num_views = len(views["Q"])
    
    # Normalize to list based on input type
    if confidence is None:
        # Default: neutral confidence
        return [0.5] * num_views
    
    elif isinstance(confidence, (int, float)):
        # Single value: apply to all views
        validated = validators.validate_confidence(confidence)
        return [validated] * num_views
    
    elif isinstance(confidence, list):
        # List: validate length and values
        if len(confidence) != num_views:
            raise ValueError(
                f"Confidence length ({len(confidence)}) must match "
                f"number of views ({num_views})"
            )
        
        # Validate each confidence value
        validated_list = []
        for i, conf in enumerate(confidence):
            validated = validators.validate_confidence(conf)
            validated_list.append(validated)
        return validated_list
    
    else:
        raise TypeError(
            f"Invalid confidence type: {type(confidence).__name__}. "
            f"Expected float, list, or None"
        )


def calculate_expected_returns(
    tickers: list[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    method: str = "historical_mean"
) -> dict:
    """
    Calculate expected returns for assets using historical data.
    
    This tool computes expected returns based on historical price movements.
    Use this as the first step in portfolio optimization.
    
    Date Range Options (mutually exclusive):
        - Provide 'period' for recent data (RECOMMENDED): "1Y", "3M", "1W"
        - Provide 'start_date' for historical data: "2023-01-01"
        - If both provided, 'start_date' takes precedence
        - If neither provided, defaults to "1Y" (1 year)
    
    Args:
        tickers: List of ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        start_date: Specific start date (YYYY-MM-DD). Use for absolute time ranges.
                   Do NOT use with 'period'.
        end_date: Specific end date (YYYY-MM-DD). Defaults to today if not provided.
        period: Relative period from today (e.g., '1M', '2Y', 'ytd'). 
               Supported: "1D", "7D", "1W", "1M", "3M", "6M", "1Y", "2Y", "5Y"
               Do NOT use with 'start_date'.
        method: Calculation method:
               - "historical_mean" (default, recommended): Simple historical average
               - "ema": Exponential moving average (gives more weight to recent data)
    
    Returns:
        Dictionary containing:
        - success: Whether the calculation succeeded
        - tickers: List of tickers
        - expected_returns: Dictionary mapping tickers to expected returns (annualized)
        - method: Method used
        - period: Date range and number of days used
    
    Example:
        Input: tickers=["AAPL", "MSFT"], period="1Y", method="historical_mean"
        Output: {"success": True, "expected_returns": {"AAPL": 0.15, "MSFT": 0.12}, ...}
    """
    try:
        # Validate inputs
        validators.validate_tickers(tickers)
        
        # Resolve date range (handles period vs absolute dates)
        start_date, end_date = validators.resolve_date_range(
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        # Load price data
        prices = data_loader.load_prices(tickers, start_date, end_date)
        
        # Calculate expected returns using PyPortfolioOpt
        if method == "historical_mean":
            mu = expected_returns.mean_historical_return(prices)
        elif method == "ema":
            mu = expected_returns.ema_historical_return(prices)
        else:
            raise ValueError(
                f"Unknown method: {method}. "
                f"Use 'historical_mean' or 'ema'"
            )
        
        return {
            "success": True,
            "tickers": tickers,
            "expected_returns": mu.to_dict(),
            "method": method,
            "period": {
                "start": start_date,
                "end": end_date or prices.index[-1].strftime("%Y-%m-%d"),
                "days": len(prices)
            }
        }
    
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }


def calculate_covariance_matrix(
    tickers: list[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    method: str = "ledoit_wolf"
) -> dict:
    """
    Calculate covariance matrix for assets using historical data.
    
    The covariance matrix measures how assets move together. Use this for risk estimation
    in portfolio optimization.
    
    Date Range Options (mutually exclusive):
        - Provide 'period' for recent data (RECOMMENDED): "1Y", "3M", "1W"
        - Provide 'start_date' for historical data: "2023-01-01"
        - If both provided, 'start_date' takes precedence
        - If neither provided, defaults to "1Y" (1 year)
    
    Args:
        tickers: List of ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        start_date: Specific start date (YYYY-MM-DD). Use for absolute time ranges.
                   Do NOT use with 'period'.
        end_date: Specific end date (YYYY-MM-DD). Defaults to today if not provided.
        period: Relative period from today (e.g., '1M', '2Y'). 
               Supported: "1D", "7D", "1W", "1M", "3M", "6M", "1Y", "2Y", "5Y"
               Do NOT use with 'start_date'.
        method: Calculation method:
               - "ledoit_wolf" (default, recommended): Shrinkage estimator, more stable
               - "sample": Sample covariance
               - "exp": Exponentially-weighted covariance
    
    Returns:
        Dictionary containing:
        - success: Whether the calculation succeeded
        - tickers: List of tickers
        - covariance_matrix: Nested dictionary of covariances
        - method: Method used
        - period: Date range and number of days used
    
    Example:
        Input: tickers=["AAPL", "MSFT"], period="1Y", method="ledoit_wolf"
        Output: {"success": True, "covariance_matrix": {"AAPL": {"AAPL": 0.04, "MSFT": 0.02}, ...}, ...}
    """
    try:
        # Validate inputs
        validators.validate_tickers(tickers)
        
        # Resolve date range (handles period vs absolute dates)
        start_date, end_date = validators.resolve_date_range(
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        # Load price data
        prices = data_loader.load_prices(tickers, start_date, end_date)
        
        # Calculate covariance matrix using PyPortfolioOpt
        if method == "ledoit_wolf":
            S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()
        elif method == "sample":
            S = risk_models.sample_cov(prices)
        elif method == "exp":
            S = risk_models.exp_cov(prices)
        else:
            raise ValueError(
                f"Unknown method: {method}. "
                f"Use 'ledoit_wolf', 'sample', or 'exp'"
            )
        
        return {
            "success": True,
            "tickers": tickers,
            "covariance_matrix": S.to_dict(),
            "method": method,
            "period": {
                "start": start_date,
                "end": end_date or prices.index[-1].strftime("%Y-%m-%d"),
                "days": len(prices)
            }
        }
    
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }


def create_investor_view(
    view_dict: dict,
    tickers: list[str],
    confidence: float = 0.5
) -> dict:
    """
    Create investor views for Black-Litterman model.
    
    Uses PyPortfolioOpt's absolute_views format - simply pass a dict!
    
    Args:
        view_dict: Dictionary mapping tickers to expected returns
                  Example: {"AAPL": 0.10, "MSFT": -0.05}
        tickers: List of all valid ticker symbols
        confidence: Confidence level (0.0 to 1.0)
    
    Returns:
        Dict with success status and view information
    """
    try:
        # Debug logging
        import logging
        logging.debug(f"create_investor_view called with:")
        logging.debug(f"  view_dict={view_dict} (type: {type(view_dict).__name__})")
        logging.debug(f"  confidence={confidence} (type: {type(confidence).__name__})")
        
        # CRITICAL: Check parameter types first (MCP may swap them!)
        if view_dict is not None:
            if not isinstance(view_dict, dict):
                # Check if view_dict and confidence got swapped
                if isinstance(view_dict, (int, float)) and isinstance(confidence, dict):
                    # Swap them back
                    logging.warning(f"⚠️ PARAMETER SWAP DETECTED! Swapping view_dict={view_dict} and confidence={confidence}")
                    view_dict, confidence = confidence, view_dict
                else:
                    raise ValueError(
                        f"view_dict must be a dict, got {type(view_dict).__name__}. "
                        f"Did you swap view_dict and confidence?"
                    )
        
        # Validate inputs
        validators.validate_view_dict(view_dict, tickers)
        # Validate and normalize confidence (handles string conversion)
        confidence = validators.validate_confidence(confidence)
        
        return {
            "success": True,
            "views": view_dict,
            "confidence": confidence,
            "num_views": len(view_dict),
            "note": "Use these views with optimize_portfolio_bl"
        }
    
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }


def optimize_portfolio_bl(
    tickers: list[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    market_caps: Optional[dict] = None,
    views: Optional[dict] = None,
    confidence: Optional[float | dict] = None,  # Can be float or dict!
    risk_aversion: Optional[float] = None
) -> dict:
    """
    Optimize portfolio using Black-Litterman model.
    
    This is the main optimization tool that combines market equilibrium with your views
    to produce optimal portfolio weights. It uses the Black-Litterman approach:
    - Starts with market-implied equilibrium returns (prior)
    - Incorporates your views with specified confidence (likelihood)
    - Produces posterior returns and optimal weights
    
    Date Range Options (mutually exclusive):
        - Provide 'period' for recent data (RECOMMENDED): "1Y", "3M", "1W"
        - Provide 'start_date' for historical data: "2023-01-01"
        - If both provided, 'start_date' takes precedence
        - If neither provided, defaults to "1Y" (1 year)
    
    Args:
        tickers: List of ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        start_date: Specific start date (YYYY-MM-DD). Use for absolute time ranges.
                   Only use if 'period' is not suitable. Do NOT use with 'period'.
        end_date: Specific end date (YYYY-MM-DD). Defaults to today if not provided.
        period: Relative period from today (e.g., '1M', '2Y'). 
               Supported: "1D", "7D", "1W", "1M", "3M", "6M", "1Y", "2Y", "5Y"
               Do NOT use with 'start_date'.
        market_caps: Dictionary of market capitalizations (optional).
                    Example: {"AAPL": 3000000000000, "MSFT": 2500000000000}
                    If not provided, equal weighting is used.
        views: Your investment views in P, Q format (optional).
              
              Format: {"P": [...], "Q": [...]}
              
              Examples:
              1. Absolute view (single asset):
                 {"P": [{"AAPL": 1}], "Q": [0.10]}
                 - AAPL expected to return 10%
                 
              2. Relative view:
                 {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
                 - NVDA will outperform AAPL by 20%
                 
              3. Multiple views:
                 {"P": [{"NVDA": 1, "AAPL": -1}, {"NVDA": 1, "MSFT": -1}], "Q": [0.20, 0.15]}
                 - NVDA vs AAPL: 20% difference
                 - NVDA vs MSFT: 15% difference
                 
              4. NumPy format (advanced):
                 {"P": [[1, -1, 0]], "Q": [0.20]}
                 - Index-based (NVDA=0, AAPL=1, MSFT=2)
              
              If not provided or None, uses only market equilibrium (no views).
              
        confidence: How confident you are in your views (0.0 to 1.0, default: 0.5).
                   Can be:
                   - Single float: Same confidence for all views. E.g., 0.7 or 70
                   - List: Per-view confidence. E.g., [0.9, 0.8]
                   - None: Defaults to 0.5 (neutral)
                   Only used if views are provided.
                   
                   Confidence scale (Idzorek method):
                   - 0.95 (95%): Very confident
                   - 0.85 (85%): Confident
                   - 0.75 (75%): Quite confident
                   - 0.60 (60%): Somewhat confident
                   - 0.50 (50%): Neutral (default)
                   - 0.30 (30%): Uncertain
                   - 0.10 (10%): Very uncertain
        risk_aversion: Risk aversion parameter (optional, auto-calculated if not provided).
                      Higher values = more conservative (typically 2-3 for equities).
    
    Returns:
        Dictionary containing:
        - success: Whether optimization succeeded
        - weights: Optimal portfolio weights (dictionary)
        - expected_return: Expected portfolio return (annualized)
        - volatility: Expected portfolio volatility (annualized)
        - sharpe_ratio: Sharpe ratio
        - posterior_returns: Expected returns after incorporating views
        - prior_returns: Market-implied equilibrium returns
        - has_views: Whether views were used
    
    Examples:
        # Absolute view
        Input: tickers=["AAPL", "MSFT", "GOOGL"], period="1Y",
               views={"P": [{"AAPL": 1}], "Q": [0.10]}, confidence=0.7
        
        # Relative view
        Input: tickers=["NVDA", "AAPL", "MSFT"], period="5Y",
               views={"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.30]}, confidence=[0.85]
    """
    try:
        # Debug logging to trace parameter values (CRITICAL for debugging!)
        import logging
        logging.warning("=" * 80)
        logging.warning(f"🔍 optimize_portfolio_bl CALLED:")
        logging.warning(f"  📋 tickers = {tickers!r}")
        logging.warning(f"  📊 views = {views!r} (type: {type(views).__name__})")
        logging.warning(f"  🎯 confidence = {confidence!r} (type: {type(confidence).__name__ if confidence else 'None'})")
        logging.warning(f"  📅 start_date = {start_date!r}")
        logging.warning(f"  📅 period = {period!r}")
        logging.warning("=" * 80)
        
        # Validate inputs
        validators.validate_tickers(tickers)
        validators.validate_risk_aversion(risk_aversion)
        
        # CRITICAL: Check parameter types first (MCP may swap them!)
        if views is not None:
            if not isinstance(views, dict):
                # Check if views and confidence got swapped
                if isinstance(views, (int, float)) and isinstance(confidence, dict):
                    # Swap them back
                    logging.warning(f"⚠️ PARAMETER SWAP DETECTED! Swapping views={views} and confidence={confidence}")
                    views, confidence = confidence, views
                else:
                    raise ValueError(
                        f"views must be a dict or None, got {type(views).__name__}. "
                        f"Did you swap views and confidence?"
                    )
        
        # Parse and validate views if provided
        if views:
            # Parse views to P, Q matrices (handles all three formats)
            P, Q = _parse_views(views, tickers)
            
            # Normalize confidence to list format
            conf_list = _normalize_confidence(confidence, views, tickers)
        
        # Resolve date range (handles period vs absolute dates)
        start_date, end_date = validators.resolve_date_range(
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        # Load price data
        prices = data_loader.load_prices(tickers, start_date, end_date)
        
        # Calculate covariance matrix
        S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()
        
        # Handle market caps
        if market_caps is None:
            # Use equal market caps if not provided
            market_caps = {ticker: 1.0 for ticker in tickers}
        
        # Convert to Series with explicit index
        mcaps = pd.Series(market_caps, index=tickers)
        
        # Calculate risk aversion if not provided
        if risk_aversion is None:
            # Use default market-implied risk aversion
            # Typically around 2-3 for equity markets
            risk_aversion = 2.5
        
        # Calculate market-implied prior returns
        market_prior = black_litterman.market_implied_prior_returns(
            mcaps, risk_aversion, S
        )
        
        # Create Black-Litterman model
        if views:
            # Idzorek method: User provides confidence → algorithm reverse-engineers Ω
            # P, Q (matrices) → Explicit view specification
            # conf_list (list) → Per-view confidence → Idzorek calculates optimal Ω
            
            bl = BlackLittermanModel(
                S,
                pi=market_prior,
                P=P,                     # Pick matrix (converted from dict/NumPy)
                Q=Q,                     # View returns vector
                omega="idzorek",         # Reverse-engineer Ω from confidence!
                view_confidences=conf_list  # Per-view confidence list
            )
            # Get posterior returns
            posterior_rets = bl.bl_returns()
            # Get optimized weights
            weights = bl.bl_weights()
            # Calculate portfolio metrics
            perf = bl.portfolio_performance(verbose=False)
        else:
            # No views: use market equilibrium weights directly
            # Market cap weighted portfolio
            weights = mcaps / mcaps.sum()
            posterior_rets = market_prior
            # Manual performance calculation for no-view case
            portfolio_return = weights.dot(posterior_rets)
            portfolio_variance = weights.dot(S).dot(weights)
            portfolio_vol = portfolio_variance ** 0.5
            sharpe = portfolio_return / portfolio_vol if portfolio_vol > 0 else 0
            perf = (portfolio_return, portfolio_vol, sharpe)
        
        return {
            "success": True,
            "weights": weights,
            "expected_return": perf[0],
            "volatility": perf[1],
            "sharpe_ratio": perf[2],
            "posterior_returns": posterior_rets.to_dict(),
            "prior_returns": market_prior.to_dict(),
            "risk_aversion": risk_aversion,
            "has_views": bool(views),
            "period": {
                "start": start_date,
                "end": end_date or prices.index[-1].strftime("%Y-%m-%d"),
                "days": len(prices)
            }
        }
    
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
