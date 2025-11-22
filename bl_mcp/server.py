"""FastMCP server for Black-Litterman portfolio optimization."""

from enum import Enum
from typing import Optional, Union

from fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator

from . import tools

# Initialize FastMCP server
mcp = FastMCP("black-litterman-portfolio")


# Enum types for preventing LLM hallucination
class ExpectedReturnsMethod(str, Enum):
    """
    Methods for calculating expected returns.
    
    Prevents LLM from inventing non-existent methods.
    """
    HISTORICAL_MEAN = "historical_mean"
    EMA = "ema"


class CovarianceMethod(str, Enum):
    """
    Methods for calculating covariance matrix.
    
    Prevents LLM from inventing non-existent methods.
    """
    LEDOIT_WOLF = "ledoit_wolf"
    SAMPLE = "sample"
    EXPONENTIAL = "exp"


class InvestmentStyle(str, Enum):
    """
    Investment style for risk aversion adjustment.
    
    Adjusts market-implied risk aversion based on investor preference.
    - Aggressive: 0.5x market δ (higher concentration, higher risk)
    - Balanced: 1.0x market δ (market equilibrium, default)
    - Conservative: 2.0x market δ (higher diversification, lower risk)
    """
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"


# Pydantic models for type safety
class ViewMatrix(BaseModel):
    """
    Black-Litterman view matrix in P, Q format.
    
    Provides automatic validation of view structure to prevent LLM errors.
    """
    
    P: Union[list[dict[str, float]], list[list[float]]] = Field(
        ...,
        description=(
            "Picking matrix. Each element represents one view. "
            "Format 1 (Dict): [{'NVDA': 1, 'AAPL': -1}] - ticker names. "
            "Format 2 (NumPy): [[1, -1, 0]] - index-based. "
            "Number of rows must match Q length. "
            "Example: [{'AAPL': 1}] for absolute view, "
            "[{'NVDA': 1, 'AAPL': -1}] for relative view."
        )
    )
    
    Q: list[float] = Field(
        ...,
        description=(
            "Expected returns for each view (annualized, in decimals). "
            "Example: [0.10] means 10% expected return. "
            "Length must match number of rows in P. "
            "Example: [0.10] for single view, [0.20, 0.15] for two views."
        )
    )
    
    @field_validator('Q')
    @classmethod
    def validate_q_length(cls, v, info):
        """Ensure Q length matches P rows."""
        P = info.data.get('P')
        if P is not None and len(v) != len(P):
            raise ValueError(
                f"Q length ({len(v)}) must match number of views in P ({len(P)}). "
                f"Each view needs exactly one expected return value."
            )
        return v
    
    @field_validator('P')
    @classmethod
    def validate_p_not_empty(cls, v):
        """Ensure P is not empty."""
        if not v:
            raise ValueError("P matrix cannot be empty. Provide at least one view.")
        return v


def calculate_expected_returns(
    tickers: list[str],
    start_date: str,
    end_date: Optional[str] = None,
    method: ExpectedReturnsMethod = ExpectedReturnsMethod.HISTORICAL_MEAN
) -> dict:
    """
    Calculate expected returns for assets using historical price data.
    
    **Purpose**: Compute annualized expected returns based on historical price movements.
    Use this when you need return estimates for portfolio optimization or analysis.
    
    **When to Use**:
    - Before portfolio optimization to estimate future returns
    - For backtesting investment strategies
    - To compare historical performance across assets
    
    **Constraints**:
    - Requires at least 60 days of historical data
    - Maximum 100 tickers per call (performance limitation)
    - Returns are annualized (multiply by 252 trading days)
    
    Args:
        tickers: List of ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
                Supports most US stocks. Maximum 100 tickers.
        start_date: Start date in YYYY-MM-DD format (e.g., "2023-01-01")
                   Minimum 60 days from end_date recommended for statistical significance.
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
        method: Calculation method (Enum - LLM MUST use exact values):
               - "historical_mean" (default, RECOMMENDED): Simple average of returns
               - "ema": Exponential moving average (gives more weight to recent data)
               
               ⚠️ Only these two values are allowed. Do not invent other methods.
    
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
    return tools.calculate_expected_returns(tickers, start_date, end_date, method.value)


def calculate_covariance_matrix(
    tickers: list[str],
    start_date: str,
    end_date: Optional[str] = None,
    method: CovarianceMethod = CovarianceMethod.LEDOIT_WOLF
) -> dict:
    """
    Calculate covariance matrix for assets using historical price data.
    
    **Purpose**: Measure how assets move together (correlation) and their volatilities.
    The covariance matrix is essential for risk estimation and portfolio diversification.
    
    **When to Use**:
    - Before portfolio optimization to estimate risk
    - To analyze diversification benefits
    - To identify correlated assets
    
    **Constraints**:
    - Requires at least 60 days of historical data (252 days recommended)
    - Maximum 100 tickers per call
    - Output is annualized (252 trading days)
    - Matrix must be positive semi-definite (ensured by ledoit_wolf)
    
    Args:
        tickers: List of ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
                Must be the same tickers used in expected returns.
        start_date: Start date in YYYY-MM-DD format (e.g., "2023-01-01")
                   Recommend at least 252 days (1 year) for stable estimates.
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
        method: Calculation method (Enum - LLM MUST use exact values):
               - "ledoit_wolf" (default, HIGHLY RECOMMENDED): Shrinkage estimator
                 More stable and works well with limited data
               - "sample": Sample covariance (can be unstable with few observations)
               - "exp": Exponentially-weighted (emphasizes recent volatility)
               
               ⚠️ Only these three values are allowed. Do not invent other methods.
    
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
    return tools.calculate_covariance_matrix(tickers, start_date, end_date, method.value)


def create_investor_view(
    view_dict: dict,
    tickers: list[str],
    confidence: float = 0.5
) -> dict:
    """
    Create and validate investor views for Black-Litterman model.
    
    **Purpose**: Express your investment opinions about expected returns for specific assets.
    These views will be combined with market equilibrium to create optimal portfolios.
    
    **Note**: This is a validation-only tool. For portfolio optimization, use
    `optimize_portfolio_bl` directly with views parameter.
    
    **When to Use**:
    - To validate view format before optimization
    - To check if tickers are valid
    - For testing and debugging views
    
    **Constraints**:
    - All tickers in view_dict must exist in tickers list
    - Expected returns must be in decimal format (0.10 = 10%)
    - Confidence must be between 0.0 and 1.0
    
    Args:
        view_dict: Dictionary mapping tickers to expected annual returns (decimals)
                  Example: {"AAPL": 0.10} means "I expect AAPL to return 10% annually"
                          {"MSFT": -0.05} means "I expect MSFT to decline 5%"
                  Format: Decimals (0.10 = 10%, not 10)
        tickers: List of all valid tickers in the portfolio
                Must include all tickers mentioned in view_dict
        confidence: How confident you are in your views (0.0 to 1.0)
                   - 0.0: No confidence (views ignored)
                   - 0.5: Moderate confidence (default, neutral)
                   - 1.0: Complete confidence (views dominate)
    
    Returns:
        Dictionary containing:
        - success: Whether view creation succeeded
        - views: Your validated view dictionary
        - confidence: Confidence level (normalized to 0.0-1.0)
        - num_views: Number of views provided
    
    Example:
        Input: view_dict={"AAPL": 0.10, "MSFT": 0.05}, 
               tickers=["AAPL", "MSFT", "GOOGL"], 
               confidence=0.7
        Output: {"success": True, "views": {"AAPL": 0.10, "MSFT": 0.05}, 
                "confidence": 0.7, "num_views": 2}
    """
    return tools.create_investor_view(view_dict, tickers, confidence)


@mcp.tool()
def optimize_portfolio_bl(
    tickers: list[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    market_caps: Optional[dict] = None,
    views: Optional[Union[ViewMatrix, dict]] = None,
    confidence: Optional[float | list] = None,  # Can be float or list
    investment_style: InvestmentStyle = InvestmentStyle.BALANCED,
    risk_aversion: Optional[float] = None  # Advanced parameter (last)
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
        market_caps: Dictionary of market capitalizations in USD (optional)
                    Example: {"AAPL": 3000000000000, "MSFT": 2500000000000}
                    Units: USD (United States Dollars)
                    
                    Purpose: Determines market equilibrium weights (larger cap = higher weight)
                    If not provided, equal weighting is used (each asset gets 1/N weight)
        views: Your investment views in P, Q format (optional)
              
              Type: ViewMatrix (Pydantic model) or dict
              Format: {"P": [...], "Q": [...]}
              
              Using Pydantic model (RECOMMENDED for type safety):
                  ViewMatrix(P=[{"AAPL": 1}], Q=[0.10])
              
              Using dict (backward compatible):
                  {"P": [{"AAPL": 1}], "Q": [0.10]}
              
              Examples:
              1. Absolute view:
                 {"P": [{"AAPL": 1}], "Q": [0.10]}
                 - "AAPL will return 10%"
                 
              2. Relative view:
                 {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
                 - "NVDA will outperform AAPL by 20%"
                 - "엔비디아가 애플보다 20% 높다"
                 
              3. Multiple relative views:
                 {"P": [{"NVDA": 1, "AAPL": -1}, {"NVDA": 1, "MSFT": -1}], "Q": [0.30, 0.30]}
                 - "NVDA vs AAPL: 30% higher"
                 - "NVDA vs MSFT: 30% higher"
                 - "엔비디아가 애플과 마이크로소프트보다 30% 높다"
                 
              4. NumPy format (advanced):
                 {"P": [[1, -1, 0]], "Q": [0.20]}
              
              If not provided, uses only market equilibrium
              
        confidence: How confident you are in your views (0.0-1.0 or 0-100)
                   Higher confidence = views have more influence on final weights
                   
                   Formats:
                   - Single float: 0.7 or 70 → same confidence for all views
                   - List: [0.9, 0.8] → different confidence per view
                   - None: Defaults to 0.5 (neutral)
                   
                   Interpretation guide:
                   - 0.95 (95%): Very confident (strong conviction)
                   - 0.85 (85%): Confident (based on solid analysis)
                   - 0.70 (70%): Fairly confident (reasonable evidence)
                   - 0.50 (50%): Neutral (weak evidence, default)
                   - 0.30 (30%): Uncertain (speculative)
                   
                   Only used if views are provided
        investment_style: Investment style for automatic risk aversion adjustment (Enum)
                         Adjusts market-implied risk aversion based on preference.
                         
                         ✅ RECOMMENDED: Use this parameter for risk preference
                         
                         - "aggressive": δ × 0.5 (high concentration, high risk)
                           Natural language: "공격적인 투자", "aggressive style"
                         - "balanced": δ × 1.0 (market equilibrium, DEFAULT)
                           Natural language: "균형 잡힌 투자", "balanced approach"
                         - "conservative": δ × 2.0 (high diversification, low risk)
                           Natural language: "보수적인 투자", "conservative strategy"
                         
                         Auto-calculates from SPY market data and adjusts by multiplier.
                         Ignored if risk_aversion is manually specified.
                         
        risk_aversion: ⚠️ ADVANCED PARAMETER - DO NOT USE unless you are an expert
                      
                      This parameter is for research and backtesting ONLY.
                      
                      🚫 LLMs should NEVER set this parameter directly!
                      ✅ Use investment_style instead (it auto-calculates from market data)
                      
                      If provided:
                      - Overrides market-implied calculation
                      - Ignores investment_style setting
                      - You take full responsibility for the value
                      
                      Academic reference values (if you must use):
                      - 2.0: Aggressive (high concentration risk)
                      - 2.5: Market equilibrium (academic standard)
                      - 3.0-3.5: Moderate (balanced diversification)
                      - 4.0+: Conservative (high diversification)
    
    Returns:
        Dictionary containing:
        - success: Whether optimization succeeded (boolean)
        - weights: Optimal portfolio weights (dict, only if success=True)
        - expected_return: Expected portfolio return annualized (only if success=True)
        - volatility: Expected portfolio volatility annualized (only if success=True)
        - sharpe_ratio: Sharpe ratio (only if success=True)
        - posterior_returns: Expected returns after incorporating views (only if success=True)
        - prior_returns: Market-implied equilibrium returns (only if success=True)
        - has_views: Whether views were used (only if success=True)
        - error: Error message (string, only if success=False)
        - error_type: Error type name (string, only if success=False)
        - traceback: Full error traceback (string, only if success=False)
        
        Common error cases (LLM can retry with corrections):
        - "Ticker 'XYZ' not found": Invalid ticker symbol, remove it and retry
        - "Insufficient data": Need at least 60 days, try longer period
        - "Singular matrix": Assets too correlated, add more diverse tickers
        - "Views validation failed": P/Q dimension mismatch, check lengths
        - "must use P, Q format": Old dict format used, convert to P, Q
        - "not found in tickers list": View ticker not in portfolio, add it to tickers
    
    Examples:
        # Example 1: Absolute view
        Natural language: "AAPL will return 10%"
        Tool call: 
            tickers=["AAPL", "MSFT", "GOOGL"], 
            period="1Y",
            views={"P": [{"AAPL": 1}], "Q": [0.10]}, 
            confidence=0.7
        
        # Example 2: Relative view (Korean)
        Natural language: "엔비디아가 애플보다 30% 높다"
        Tool call:
            tickers=["NVDA", "AAPL", "MSFT"], 
            period="5Y",
            views={"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.30]},
            confidence=0.85
        
        # Example 3: Aggressive investment style (RECOMMENDED approach)
        Natural language: "공격적인 투자 성향으로 분석해줘"
        Tool call:
            tickers=["AAPL", "MSFT", "GOOGL"],
            period="1Y",
            investment_style="aggressive"  # Auto-calculated δ × 0.5
        
        # Example 4: Pessimistic market view
        Natural language: "시장 전망이 안 좋을 때의 결과 보여줘"
        Tool call:
            tickers=["AAPL", "MSFT", "GOOGL"],
            period="1Y",
            views={"P": [{"AAPL": 1}, {"MSFT": 1}, {"GOOGL": 1}], 
                   "Q": [-0.05, -0.05, -0.05]},  # Negative returns
            confidence=0.6
        
        # Example 5: Ticker mapping (Korean stocks)
        Natural language: "삼성전자랑 애플로 포트폴리오 짜줘"
        Tool call:
            tickers=["005930.KS", "AAPL"],  # 005930.KS = Samsung Electronics
            period="1Y"
    """
    # Convert ViewMatrix to dict if needed (Pydantic model_dump)
    if isinstance(views, ViewMatrix):
        views = views.model_dump()
    
    return tools.optimize_portfolio_bl(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        period=period,
        market_caps=market_caps,
        views=views,
        confidence=confidence,
        investment_style=investment_style.value,
        risk_aversion=risk_aversion
    )
