"""FastMCP server for Black-Litterman portfolio optimization."""

import json
from enum import Enum
from typing import Optional, Union

from fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator

from . import tools
from .utils import data_loader

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


class BacktestStrategy(str, Enum):
    """
    Backtesting strategy presets.

    Choose a strategy based on your investment approach:
    - buy_and_hold: No rebalancing. Simple baseline comparison.
    - passive_rebalance: Monthly rebalancing to target weights. Standard ETF approach. (DEFAULT)
    - risk_managed: Monthly rebalancing + 10% stop-loss + 20% max drawdown limit.
    """
    BUY_AND_HOLD = "buy_and_hold"
    PASSIVE_REBALANCE = "passive_rebalance"
    RISK_MANAGED = "risk_managed"


class BacktestConfig(BaseModel):
    """
    Advanced configuration for backtesting.

    ⚠️ For most users, use BacktestStrategy presets instead.
    Only use this for fine-grained control over backtesting parameters.
    """
    rebalance_frequency: str = Field(
        default="monthly",
        description="Rebalancing frequency: 'none', 'weekly', 'monthly', 'quarterly', 'semi-annual', 'annual'"
    )
    fees: float = Field(
        default=0.001,
        description="Transaction fees as decimal (0.001 = 0.1%)",
        ge=0.0,
        le=0.1
    )
    slippage: float = Field(
        default=0.0005,
        description="Slippage as decimal (0.0005 = 0.05%)",
        ge=0.0,
        le=0.1
    )
    stop_loss: Optional[float] = Field(
        default=None,
        description="Stop-loss threshold (0.10 = 10% loss triggers exit)",
        ge=0.0,
        le=1.0
    )
    take_profit: Optional[float] = Field(
        default=None,
        description="Take-profit threshold (0.20 = 20% gain triggers exit)",
        ge=0.0,
        le=10.0
    )
    trailing_stop: bool = Field(
        default=False,
        description="Enable trailing stop-loss (follows price up)"
    )
    max_drawdown_limit: Optional[float] = Field(
        default=None,
        description="Maximum drawdown limit (0.20 = 20% drawdown triggers full exit)",
        ge=0.0,
        le=1.0
    )

    @field_validator('rebalance_frequency')
    @classmethod
    def validate_rebalance_frequency(cls, v):
        """Validate rebalance frequency."""
        valid = ['none', 'weekly', 'monthly', 'quarterly', 'semi-annual', 'annual']
        if v not in valid:
            raise ValueError(f"rebalance_frequency must be one of {valid}, got '{v}'")
        return v


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


@mcp.tool()
def upload_price_data(
    ticker: str,
    prices: list[dict],
    source: str = "user"
) -> dict:
    """
    Upload custom price data for assets not available in pre-loaded datasets.

    Use this tool when you need to work with:
    - International stocks (Korean, Japanese, European markets)
    - Alternative assets (commodities, real estate)
    - Custom indices or benchmarks
    - Data from external sources or other MCP servers

    The uploaded data will be saved as a Parquet file and can be used
    immediately with optimize_portfolio_bl.

    Args:
        ticker: Ticker symbol to use (e.g., "005930.KS" for Samsung Electronics)
                This will be the identifier used in optimize_portfolio_bl
        prices: List of price data dictionaries, each containing:
                - date: Date string in "YYYY-MM-DD" format
                - close: Closing price (float)

                Example:
                [
                    {"date": "2024-01-02", "close": 78000.0},
                    {"date": "2024-01-03", "close": 78500.0},
                    {"date": "2024-01-04", "close": 77800.0}
                ]

                Requirements:
                - Minimum 60 data points recommended
                - Dates should be in chronological order
                - No missing values allowed

        source: Source identifier for audit trail (e.g., "user", "pykrx", "external_mcp")
                Default: "user"

    Returns:
        Dictionary containing:
        - success: True if upload successful
        - ticker: The ticker symbol saved
        - records: Number of records saved
        - date_range: Start and end dates of the data
        - file_path: Path to the saved Parquet file
        - source: Source identifier

    Examples:
        # Korean stock data (삼성전자)
        upload_price_data(
            ticker="005930.KS",
            prices=[
                {"date": "2024-01-02", "close": 78000.0},
                {"date": "2024-01-03", "close": 78500.0},
                ...
            ],
            source="pykrx"
        )

        # After upload, use in optimization:
        optimize_portfolio_bl(
            tickers=["005930.KS", "AAPL"],
            period="1Y"
        )
    """
    return data_loader.save_custom_price_data(ticker, prices, source)


@mcp.tool()
def upload_price_data_from_file(
    ticker: str,
    file_path: str,
    date_column: str = "date",
    close_column: str = "close",
    source: str = "file"
) -> dict:
    """
    Upload custom price data from a CSV or Parquet file.

    Use this tool when:
    - External MCP server saved data to a file
    - User has data in CSV/Parquet format
    - Batch uploading large datasets

    Args:
        ticker: Ticker symbol to use (e.g., "CUSTOM_INDEX")
        file_path: Absolute path to CSV or Parquet file
        date_column: Column name for dates (default: "date")
        close_column: Column name for closing prices (default: "close")
        source: Source identifier (default: "file")

    Returns:
        Dictionary with upload results (same as upload_price_data)

    Examples:
        # From CSV file
        upload_price_data_from_file(
            ticker="KOSPI",
            file_path="/path/to/kospi_data.csv",
            date_column="Date",
            close_column="Close"
        )

        # From Parquet file (typically from another MCP)
        upload_price_data_from_file(
            ticker="BTC-KRW",
            file_path="/tmp/crypto_data.parquet"
        )
    """
    return data_loader.load_and_save_from_file(
        ticker, file_path, date_column, close_column, source
    )


@mcp.tool()
def backtest_portfolio(
    tickers: list[str],
    weights: dict[str, float],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    strategy: BacktestStrategy = BacktestStrategy.PASSIVE_REBALANCE,
    benchmark: Optional[str] = "SPY",
    initial_capital: float = 10000.0,
    custom_config: Optional[BacktestConfig] = None
) -> dict:
    """
    Backtest a portfolio with specified weights.

    This tool evaluates how a portfolio would have performed historically,
    including realistic transaction costs and rebalancing.

    RECOMMENDED WORKFLOW:
    1. First call optimize_portfolio_bl() to get optimal weights
    2. Then call backtest_portfolio() with those weights to validate performance

    Date Range Options (mutually exclusive):
        - Provide 'period' for recent data (RECOMMENDED): "1Y", "3Y", "5Y"
        - Provide 'start_date' for historical data: "2020-01-01"
        - If both provided, 'start_date' takes precedence
        - If neither provided, defaults to "1Y" (1 year)

    Args:
        tickers: List of ticker symbols in the portfolio
        weights: Target weights from optimize_portfolio_bl output
                 Example: {"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25}
                 Weights are automatically normalized to sum to 1.0
        start_date: Backtest start date (YYYY-MM-DD), optional
        end_date: Backtest end date (YYYY-MM-DD), optional
        period: Relative period ("1Y", "3Y", "5Y") - RECOMMENDED
        strategy: Backtesting strategy preset (Enum)

                 ✅ RECOMMENDED: Use strategy presets for most use cases

                 - "buy_and_hold": No rebalancing, simple baseline
                   Natural language: "매입 후 보유", "buy and hold"
                 - "passive_rebalance": Monthly rebalancing (DEFAULT)
                   Natural language: "월별 리밸런싱", "passive investing"
                 - "risk_managed": Monthly rebalancing + 10% stop-loss + 20% MDD limit
                   Natural language: "손절매 포함", "risk managed"

        benchmark: Benchmark ticker for comparison (default: "SPY")
                  Set to None to skip benchmark comparison
        initial_capital: Starting capital (default: 10000)
        custom_config: ⚠️ ADVANCED - Override strategy preset

                      Only use this for fine-grained control.
                      Available options:
                      - rebalance_frequency: "none", "weekly", "monthly", "quarterly", "semi-annual", "annual"
                      - fees: Transaction fees (0.001 = 0.1%)
                      - slippage: Slippage cost (0.0005 = 0.05%)
                      - stop_loss: Stop-loss threshold (0.10 = 10%)
                      - take_profit: Take-profit threshold (0.20 = 20%)
                      - trailing_stop: Enable trailing stop-loss (bool)
                      - max_drawdown_limit: Max drawdown limit (0.20 = 20%)

    Returns:
        Dictionary containing:

        Performance Metrics:
        - total_return: Total cumulative return (0.25 = 25%)
        - cagr: Compound Annual Growth Rate
        - volatility: Annualized volatility
        - sharpe_ratio: Risk-adjusted return (higher is better)
        - sortino_ratio: Downside risk-adjusted return
        - max_drawdown: Worst peak-to-trough decline (negative)
        - calmar_ratio: CAGR / |Max Drawdown|

        Value Metrics:
        - initial_capital: Starting amount
        - final_value: Ending portfolio value

        Cost Metrics:
        - total_fees_paid: Total transaction costs
        - num_rebalances: Number of rebalancing events
        - turnover: Portfolio turnover

        Benchmark Comparison (if benchmark provided):
        - benchmark_return: Benchmark total return
        - excess_return: Portfolio return - Benchmark return
        - alpha: Jensen's alpha (risk-adjusted excess return)
        - beta: Portfolio beta vs benchmark
        - information_ratio: Excess return / Tracking error

        Risk Management:
        - is_liquidated: Whether portfolio was liquidated
        - liquidation_reason: Reason for liquidation (if any)

        Tax Info:
        - holding_periods: Per-ticker holding period info
          - days: Number of days held
          - is_long_term: True if held >= 1 year

    Examples:
        # Example 1: Basic backtest with BL weights
        # Step 1: Get optimal weights
        bl_result = optimize_portfolio_bl(
            tickers=["AAPL", "MSFT", "GOOGL"],
            period="1Y"
        )
        # Step 2: Backtest those weights
        backtest_portfolio(
            tickers=["AAPL", "MSFT", "GOOGL"],
            weights=bl_result["weights"],
            period="3Y",
            strategy="passive_rebalance"
        )

        # Example 2: Risk-managed backtest (Korean)
        Natural language: "손절매 전략으로 백테스트 해줘"
        backtest_portfolio(
            tickers=["NVDA", "AAPL", "MSFT"],
            weights={"NVDA": 0.5, "AAPL": 0.3, "MSFT": 0.2},
            period="5Y",
            strategy="risk_managed"
        )

        # Example 3: Custom configuration
        Natural language: "분기별 리밸런싱, 수수료 0.2%로 테스트"
        backtest_portfolio(
            tickers=["AAPL", "MSFT"],
            weights={"AAPL": 0.6, "MSFT": 0.4},
            period="2Y",
            custom_config={
                "rebalance_frequency": "quarterly",
                "fees": 0.002
            }
        )
    """
    # Handle custom_config - can be BacktestConfig or dict
    config_dict = None
    if custom_config is not None:
        if isinstance(custom_config, BacktestConfig):
            config_dict = custom_config.model_dump()
        elif isinstance(custom_config, dict):
            # Validate via Pydantic
            config_dict = BacktestConfig(**custom_config).model_dump()
        else:
            raise ValueError(
                f"custom_config must be BacktestConfig or dict, got {type(custom_config).__name__}"
            )

    return tools.backtest_portfolio(
        tickers=tickers,
        weights=weights,
        start_date=start_date,
        end_date=end_date,
        period=period,
        strategy=strategy.value,
        benchmark=benchmark,
        initial_capital=initial_capital,
        custom_config=config_dict
    )


@mcp.tool()
def list_available_tickers(
    dataset: Optional[str] = None,
    search: Optional[str] = None
) -> dict:
    """
    List all available tickers that can be used with optimize_portfolio_bl.

    Use this tool to:
    - Check what assets are available before optimization
    - Search for specific tickers
    - See which custom assets have been uploaded

    Args:
        dataset: Filter by dataset (optional)
                 - "snp500": S&P 500 stocks
                 - "nasdaq100": NASDAQ 100 stocks
                 - "etf": Popular ETFs
                 - "crypto": Cryptocurrencies
                 - "custom": User-uploaded data
                 - None: All available tickers
        search: Search pattern (case-insensitive substring match)
                Examples: "AAPL", "tech", "crypto"

    Returns:
        Dictionary containing:
        - tickers: List of available ticker symbols
        - count: Total number of tickers
        - datasets: Available dataset categories
        - custom_tickers: List of user-uploaded tickers (if any)

    Examples:
        # List all available tickers
        list_available_tickers()

        # List only S&P 500 stocks
        list_available_tickers(dataset="snp500")

        # Search for Apple-related tickers
        list_available_tickers(search="AAPL")

        # List custom uploaded data
        list_available_tickers(dataset="custom")
    """
    return data_loader.list_tickers(dataset=dataset, search=search)
