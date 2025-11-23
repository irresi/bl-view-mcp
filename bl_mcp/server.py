"""FastMCP server for Black-Litterman portfolio optimization."""

import json
from enum import Enum
from typing import Optional, Union

from fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator

from . import tools

# Initialize FastMCP server
mcp = FastMCP("black-litterman-portfolio")


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


@mcp.tool()
def optimize_portfolio_bl(
    tickers: list[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
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
                         
                         Auto-calculates from portfolio market data and adjusts by multiplier.
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

        Portfolio Allocation (WEIGHTS - sum to 100%):
        - weights: How much to invest in each asset (e.g., {"AAPL": 0.4, "MSFT": 0.6})
                  These ALWAYS sum to 100%. Use these for actual portfolio construction.

        Portfolio Performance (metrics for TOTAL portfolio):
        - expected_return: Annualized expected return of portfolio (e.g., 0.15 = 15%)
        - volatility: Annualized volatility/risk (e.g., 0.20 = 20%)
        - sharpe_ratio: Risk-adjusted return (expected_return / volatility)

        Individual Asset Expected Returns (NOT weights - do NOT sum to 100%):
        - prior_returns: Market equilibrium returns BEFORE views.
                        Per-asset annual return expectations based on market cap and covariance.
        - posterior_returns: Expected returns AFTER incorporating views.
                            Compare with prior_returns to see how views shifted expectations.

        ⚠️ IMPORTANT: prior_returns and posterior_returns are per-asset return expectations
        (e.g., NVDA: 38%, MSFT: 17%), NOT portfolio weights. They do NOT sum to 100%.

        Other:
        - has_views: Whether views were incorporated (bool)
        - risk_aversion: The δ parameter used
        - period: Data period used

    Raises:
        ValueError: Invalid tickers, views format, or insufficient data
        Exception: Other errors (MCP handles error responses automatically)

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
    # Handle views parameter - can be ViewMatrix, dict, or JSON string
    if views is not None:
        # If string (common from Claude Desktop MCP calls), parse as JSON
        if isinstance(views, str):
            try:
                views = json.loads(views.strip())
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"views must be a valid JSON object, got string that failed to parse: {e}. "
                    f"Example: {{\"P\": [{{\"NVDA\": 1, \"AAPL\": -1}}], \"Q\": [0.20]}}"
                )
        # If ViewMatrix Pydantic model, convert to dict
        elif isinstance(views, ViewMatrix):
            views = views.model_dump()
        # If already dict, use as-is
        elif not isinstance(views, dict):
            raise ValueError(
                f"views must be a dict or ViewMatrix, got {type(views).__name__}. "
                f"Example: {{\"P\": [{{\"NVDA\": 1, \"AAPL\": -1}}], \"Q\": [0.20]}}"
            )

    return tools.optimize_portfolio_bl(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        period=period,
        views=views,
        confidence=confidence,
        investment_style=investment_style.value,
        risk_aversion=risk_aversion
    )
