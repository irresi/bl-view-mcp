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
    views: Optional[Union[ViewMatrix, dict, str]] = None,
    confidence: Optional[float | list] = None,  # Can be float or list
    investment_style: InvestmentStyle = InvestmentStyle.BALANCED,
    risk_aversion: Optional[float] = None,  # Advanced parameter
    sensitivity_range: Optional[list[float]] = None  # Sensitivity analysis
) -> dict:
    """
    Optimize portfolio using Black-Litterman model.

    ## Quick Reference
    **Use for**: Portfolio weight allocation
    **Don't use for**: Stats only → get_asset_stats

    ## Views Format (CRITICAL)
    ❌ {"AAPL": 0.10}                    → WRONG (old format)
    ❌ {"P": {"AAPL": 1}, "Q": [0.10]}   → WRONG (P must be LIST)
    ✅ {"P": [{"AAPL": 1}], "Q": [0.10]} → Absolute: "AAPL +10%"
    ✅ {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]} → Relative: "NVDA > AAPL by 20%"

    ## Key Parameters
    - tickers: ["AAPL", "MSFT", "GOOGL"]
    - period: "1Y" (recommended) or start_date: "2023-01-01"
    - views: P, Q format above (optional)
    - confidence: 0.0-1.0 (default 0.5) or list [0.9, 0.7]
    - investment_style: "aggressive" / "balanced" / "conservative"
    - sensitivity_range: [0.3, 0.5, 0.9] for confidence sensitivity analysis
    - risk_aversion: ⚠️ DO NOT USE (use investment_style instead)

    ## Returns (Key Fields)
    - **weights**: Portfolio allocation (sums to 1.0) ← USE THIS FOR INVESTMENT
    - prior_returns: Per-asset returns BEFORE views (NOT weights, don't sum to 1.0)
    - posterior_returns: Per-asset returns AFTER views (NOT weights)
    - expected_return, volatility, sharpe_ratio: Portfolio metrics

    ## Examples
    Absolute view: tickers=["AAPL","MSFT"], views={"P":[{"AAPL":1}],"Q":[0.10]}, confidence=0.7
    Relative view: tickers=["NVDA","AAPL"], views={"P":[{"NVDA":1,"AAPL":-1}],"Q":[0.20]}, confidence=0.8

    ## Visualization (Investment Safety)
    Create dashboard from `_visualization_hint`. Required:
    - Pie: weights (verify sum≈1.0)
    - Bar: prior vs posterior returns
    - Table: metrics + raw data
    ⚠️ NEVER fabricate data. Include disclaimer: "투자 결정 전 원본 데이터를 확인하세요."
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
        risk_aversion=risk_aversion,
        sensitivity_range=sensitivity_range
    )


@mcp.tool()
def upload_price_data(
    ticker: str,
    prices: Optional[list[dict]] = None,
    file_path: Optional[str] = None,
    date_column: str = "date",
    close_column: str = "close",
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

    Two input modes (provide EXACTLY ONE):
    1. Direct data: Use 'prices' parameter for small datasets (<100 rows)
    2. File path: Use 'file_path' parameter for large datasets or files

    Args:
        ticker: Ticker symbol to use (e.g., "005930.KS" for Samsung Electronics)
                This will be the identifier used in optimize_portfolio_bl

        prices: [Mode 1] List of price data dictionaries, each containing:
                - date: Date string in "YYYY-MM-DD" format
                - close: Closing price (float)

                Example:
                [
                    {"date": "2024-01-02", "close": 78000.0},
                    {"date": "2024-01-03", "close": 78500.0},
                    {"date": "2024-01-04", "close": 77800.0}
                ]

        file_path: [Mode 2] Absolute path to CSV or Parquet file
                   Use this for large datasets or when data is already in a file

        date_column: Column name for dates when using file_path (default: "date")
        close_column: Column name for closing prices when using file_path (default: "close")

        source: Source identifier for audit trail (e.g., "user", "pykrx", "external_mcp")
                Default: "user"

    Returns:
        Dictionary containing:
        - ticker: The ticker symbol saved
        - records: Number of records saved
        - date_range: Start and end dates of the data
        - file_path: Path to the saved Parquet file
        - source: Source identifier

    Examples:
        # Example 1: Direct data input (small datasets)
        upload_price_data(
            ticker="005930.KS",
            prices=[
                {"date": "2024-01-02", "close": 78000.0},
                {"date": "2024-01-03", "close": 78500.0},
            ],
            source="pykrx"
        )

        # Example 2: From CSV file (large datasets)
        upload_price_data(
            ticker="KOSPI",
            file_path="/path/to/kospi_data.csv",
            date_column="Date",
            close_column="Close"
        )

        # Example 3: From Parquet file (from another MCP)
        upload_price_data(
            ticker="BTC-KRW",
            file_path="/tmp/crypto_data.parquet"
        )

        # After upload, use in optimization:
        optimize_portfolio_bl(
            tickers=["005930.KS", "AAPL"],
            period="1Y"
        )
    """
    # Validate: exactly one of prices or file_path must be provided
    if prices is not None and file_path is not None:
        raise ValueError(
            "Provide EITHER 'prices' OR 'file_path', not both. "
            "Use 'prices' for direct data input, 'file_path' for loading from file."
        )
    if prices is None and file_path is None:
        raise ValueError(
            "Must provide either 'prices' (direct data) or 'file_path' (load from file). "
            "Example with prices: upload_price_data(ticker='X', prices=[{'date': '2024-01-01', 'close': 100}])"
        )

    if prices is not None:
        # Mode 1: Direct data input
        return data_loader.save_custom_price_data(ticker, prices, source)
    else:
        # Mode 2: Load from file
        return data_loader.load_and_save_from_file(
            ticker, file_path, date_column, close_column, source
        )


class TimeseriesFrequency(str, Enum):
    """
    Timeseries sampling frequency for backtest output.

    - daily: All trading days (can be large for long periods)
    - weekly: Weekly sampling (every Friday)
    - monthly: Monthly sampling (default, recommended)
    """
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


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
    custom_config: Optional[BacktestConfig] = None,
    compare_strategies: bool = False,
    include_equal_weight: bool = False,
    timeseries_freq: TimeseriesFrequency = TimeseriesFrequency.MONTHLY
) -> dict:
    """
    Backtest a portfolio with specified weights.

    ## Quick Reference
    **Use after**: optimize_portfolio_bl() to validate performance
    **Flow**: optimize → backtest(weights=result["weights"])

    ## Key Parameters
    - tickers: ["AAPL", "MSFT", "GOOGL"]
    - weights: {"AAPL": 0.4, "MSFT": 0.6} from optimize result
    - period: "3Y" (recommended for backtest)
    - strategy: "buy_and_hold" / "passive_rebalance" / "risk_managed"
    - benchmark: "SPY" (default) or None to skip
    - compare_strategies: true → compare all strategies at once
    - custom_config: ⚠️ Advanced (rebalance_frequency, fees, stop_loss, etc.)

    ## Returns (Key Fields)
    - total_return, cagr, volatility, sharpe_ratio, max_drawdown
    - timeseries: [{date, value, benchmark, drawdown}, ...]
    - drawdown_details: {max_drawdown, start, end, recovery_date}
    - comparisons: (if compare_strategies=true)
    - alpha, beta, excess_return: (vs benchmark)

    ## Example
    bl = optimize_portfolio_bl(tickers=["AAPL","MSFT"], period="1Y")
    bt = backtest_portfolio(tickers=["AAPL","MSFT"], weights=bl["weights"], period="3Y")

    ## Visualization (Investment Safety)
    Create dashboard from `_visualization_hint`. Required:
    - Line: timeseries (value + benchmark)
    - Area: drawdown (red, MUST show negative values clearly)
    - Table: metrics + raw data
    ⚠️ NEVER fabricate data. Include disclaimer: "투자 결정 전 원본 데이터를 확인하세요."
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
        custom_config=config_dict,
        compare_strategies=compare_strategies,
        include_equal_weight=include_equal_weight,
        timeseries_freq=timeseries_freq.value
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


@mcp.tool()
def get_asset_stats(
    tickers: list[str],
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_var: bool = True
) -> dict:
    """
    Get comprehensive statistics for a list of assets.

    ## Quick Reference
    **Use for**: Check correlations, validate return expectations, get VaR
    **Don't use for**: Portfolio weights → use optimize_portfolio_bl
    **Note**: This is OPTIONAL, not required before optimization

    ## Key Parameters
    - tickers: ["AAPL", "MSFT", "GOOGL"]
    - period: "1Y" (recommended)
    - include_var: false for faster response (skips EGARCH)

    ## Returns
    - assets: {ticker: {price, annual_return, volatility, sharpe, max_drawdown, var_95, percentile_95}}
    - correlation_matrix: {ticker: {ticker: correlation}}
    - covariance_matrix: {ticker: {ticker: covariance}}

    ## Example
    stats = get_asset_stats(tickers=["NVDA","AMD"], period="1Y")
    # → stats["correlation_matrix"]["NVDA"]["AMD"] = 0.75 (highly correlated!)
    # → stats["assets"]["NVDA"]["percentile_95"] = 0.75 (75% is max realistic expectation)

    ## Visualization (Investment Safety)
    Create dashboard from `_visualization_hint`. Required:
    - Heatmap: correlation_matrix (FIXED scale -1 to +1, never auto-scale)
    - Scatter: risk vs return
    - Table: metrics + raw data
    ⚠️ NEVER fabricate data. Include disclaimer: "투자 결정 전 원본 데이터를 확인하세요."
    """
    return tools.get_asset_stats(
        tickers=tickers,
        period=period,
        start_date=start_date,
        end_date=end_date,
        include_var=include_var
    )
