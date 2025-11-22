"""FastMCP server for Black-Litterman portfolio optimization."""

from typing import Optional

from fastmcp import FastMCP

from . import tools

# Initialize FastMCP server
mcp = FastMCP("black-litterman-portfolio")


@mcp.tool()
def calculate_expected_returns(
    tickers: list[str],
    start_date: str,
    end_date: Optional[str] = None,
    method: str = "historical_mean"
) -> dict:
    """
    Calculate expected returns for assets using historical data.
    
    This tool computes expected returns based on historical price movements.
    Use this as the first step in portfolio optimization.
    
    Args:
        tickers: List of ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        start_date: Start date in YYYY-MM-DD format (e.g., "2023-01-01")
        end_date: End date in YYYY-MM-DD format (optional, defaults to most recent)
        method: Calculation method - "historical_mean" (default) or "ema" (exponential moving average)
    
    Returns:
        Dictionary containing:
        - success: Whether the calculation succeeded
        - tickers: List of tickers
        - expected_returns: Dictionary mapping tickers to expected returns
        - method: Method used
        - period: Date range and number of days used
    
    Example:
        Input: tickers=["AAPL", "MSFT"], start_date="2023-01-01"
        Output: {"success": True, "expected_returns": {"AAPL": 0.15, "MSFT": 0.12}, ...}
    """
    return tools.calculate_expected_returns(tickers, start_date, end_date, method)


@mcp.tool()
def calculate_covariance_matrix(
    tickers: list[str],
    start_date: str,
    end_date: Optional[str] = None,
    method: str = "ledoit_wolf"
) -> dict:
    """
    Calculate covariance matrix for assets using historical data.
    
    The covariance matrix measures how assets move together. Use this for risk estimation.
    
    Args:
        tickers: List of ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        start_date: Start date in YYYY-MM-DD format (e.g., "2023-01-01")
        end_date: End date in YYYY-MM-DD format (optional, defaults to most recent)
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
        Input: tickers=["AAPL", "MSFT"], start_date="2023-01-01", method="ledoit_wolf"
        Output: {"success": True, "covariance_matrix": {"AAPL": {"AAPL": 0.04, "MSFT": 0.02}, ...}, ...}
    """
    return tools.calculate_covariance_matrix(tickers, start_date, end_date, method)


@mcp.tool()
def create_investor_view(
    view_dict: dict,
    tickers: list[str],
    confidence: float = 0.5
) -> dict:
    """
    Create investor views for Black-Litterman model.
    
    Express your opinions about expected returns for specific assets.
    These views will be combined with market equilibrium to create optimal portfolios.
    
    Args:
        view_dict: Dictionary mapping tickers to expected returns (as decimals)
                  Example: {"AAPL": 0.10} means "I expect AAPL to return 10%"
                          {"MSFT": -0.05} means "I expect MSFT to return -5%"
        tickers: List of all valid tickers in the portfolio
        confidence: How confident you are in your views (0.0 to 1.0)
                   0.0 = no confidence (ignore views)
                   0.5 = moderate confidence (default)
                   1.0 = complete confidence
    
    Returns:
        Dictionary containing:
        - success: Whether view creation succeeded
        - views: Your view dictionary
        - confidence: Confidence level
        - num_views: Number of views
    
    Example:
        Input: view_dict={"AAPL": 0.10, "MSFT": 0.05}, tickers=["AAPL", "MSFT", "GOOGL"], confidence=0.7
        Output: {"success": True, "views": {"AAPL": 0.10, "MSFT": 0.05}, "confidence": 0.7, ...}
    """
    return tools.create_investor_view(view_dict, tickers, confidence)


@mcp.tool()
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
        start_date: Specific start date (YYYY-MM-DD), optional
        end_date: End date (YYYY-MM-DD), optional
        period: Relative period ("1Y", "6M", "3M", "1W"), optional (PREFERRED)
        market_caps: Dictionary of market capitalizations (optional)
                    Example: {"AAPL": 3000000000000, "MSFT": 2500000000000}
                    If not provided, equal weighting is used
        views: Your investment views (optional)
              Example: {"AAPL": 0.10, "MSFT": 0.05}
              If not provided, uses only market equilibrium
        confidence: How confident you are in your views (0-100 or 0.0-1.0)
                   Can be single value (same for all) or dict (per-view):
                   - Single: 0.7 or 70 → all views get 70% confidence
                   - Dict: {"AAPL": 0.8, "MSFT": 0.6} → different per view
                   Only used if views are provided. Default: 0.5 (50%)
        risk_aversion: Risk aversion parameter (optional, auto-calculated if not provided)
                      Higher values = more conservative (typically 2-3 for equities)
    
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
    
    Example:
        Input: tickers=["AAPL", "MSFT", "GOOGL"], period="1Y",
               views={"AAPL": 0.10}, confidence=0.7
        Output: {"success": True, "weights": {"AAPL": 0.40, "MSFT": 0.35, "GOOGL": 0.25},
                "expected_return": 0.15, "volatility": 0.20, "sharpe_ratio": 0.75, ...}
    """
    return tools.optimize_portfolio_bl(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        period=period,
        market_caps=market_caps,
        views=views,
        confidence=confidence,
        risk_aversion=risk_aversion
    )
