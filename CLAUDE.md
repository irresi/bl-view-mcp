# Black-Litterman MCP Server

## Project Summary

Black-Litterman portfolio optimization MCP server for AI agents (Claude, Windsurf, Google ADK).

**Core Philosophy**: Prior (Market Equilibrium) + Views (AI Opinions) = Posterior (Optimal Portfolio)

## Development Environment

### Prerequisites

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (Package Manager)

### Setup

```bash
# 1. Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
make install          # Base + agent extras
# or
uv sync               # Base only
uv sync --extra agent # Include agent extras

# 3. Download data (Important: Run before starting the server!)
make download-data      # S&P 500 (~500 tickers, GitHub Release)
make download-nasdaq100 # NASDAQ 100 (~100 tickers)
make download-etf       # ETF (~130 tickers)
make download-crypto    # Crypto (100 symbols, requires --extra crypto)

# 4. Run tests
make test-simple
```

> **stdio mode warning**: Starting the server without data may trigger auto-download taking 30+ seconds.
> LLM may disconnect due to timeout, so **pre-downloading is strongly recommended**.

### Optional Dependencies

```toml
[project.optional-dependencies]
agent = ["google-adk", "google-genai"]  # For ADK Web UI
dev = ["pytest", "mypy", "ruff"]        # For development
```

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies (`uv sync --extra agent`) |
| `make sync` | Install base dependencies only (`uv sync`) |
| `make test-simple` | Run basic tests |
| `make server-stdio` | Server for Windsurf/Claude |
| `make server-http` | HTTP server for Google ADK (port 5000) |
| `make web-ui` | ADK Web UI (port 8000) |
| `make quickstart` | install + sample + test at once |
| `make check` | Check environment status |

### Git Workflow Rules

> **Important**: Do not merge branches directly. Always merge through **Pull Request**.

```bash
# Don't do this
git checkout main
git merge feature-branch

# Correct way
git push origin feature-branch
# -> Create PR on GitHub -> Review -> Merge
```

## Current Architecture (2025-11-24)

### MCP Tools (5 tools)

| Tool | Purpose | Notes |
|------|---------|-------|
| `optimize_portfolio_bl` | BL portfolio optimization | Main tool, VaR warnings + sensitivity analysis |
| `backtest_portfolio` | Portfolio backtesting | timeseries, drawdown_details, strategy comparison |
| `get_asset_stats` | Asset statistics lookup | **NEW** Includes VaR, correlation matrix, covariance |
| `upload_price_data` | Upload custom price data | Direct input + file integration |
| `list_available_tickers` | List available tickers | Search/filter support |

```
server.py (@mcp.tool)
    ├── optimize_portfolio_bl()      # sensitivity_range support
    │       └── tools.py
    ├── backtest_portfolio()         # compare_strategies, include_equal_weight
    │       └── tools.py
    ├── get_asset_stats()            # NEW: VaR, correlation, covariance
    │       └── tools.py
    ├── upload_price_data()          # Direct input + file path integration
    │       └── data_loader.py
    └── list_available_tickers()
            └── data_loader.py
```

**Removed tools**:
- ~~`calculate_var_egarch`~~ -> VaR integrated into `get_asset_stats`
- ~~`upload_price_data_from_file`~~ -> Integrated into `upload_price_data`

**Design philosophy**: Minimize number of tools (5), extend functionality through parameters

### Key Parameters

```python
optimize_portfolio_bl(
    tickers: list[str],           # ["AAPL", "MSFT", "GOOGL"]
    period: str = "1Y",           # "1Y", "6M", "3M" (recommended)
    start_date: str = None,       # "2023-01-01" (choose either period or this)
    views: dict = None,           # P, Q format only
    confidence: float | list = None,  # 0.0-1.0 or list
    investment_style: str = "balanced",  # aggressive/balanced/conservative
    risk_aversion: float = None,  # For advanced users (not recommended)
    sensitivity_range: list[float] = None  # NEW: [0.3, 0.5, 0.9] confidence sensitivity analysis
)
```

**Removed**: `market_caps` parameter -> Auto-loaded

### get_asset_stats Parameters

```python
get_asset_stats(
    tickers: list[str],           # ["AAPL", "MSFT", "GOOGL"]
    period: str = "1Y",           # "1Y", "6M", "3M" (recommended)
    include_var: bool = True      # Set to False for faster response (skips EGARCH VaR)
)
# Returns:
# - assets: {ticker: {current_price, annual_return, volatility, sharpe, max_drawdown, market_cap, var_95, percentile_95}}
# - correlation_matrix: {ticker: {ticker: correlation}}
# - covariance_matrix: {ticker: {ticker: covariance}}
#
# Note: VaR calculation period = period (minimum 1Y, default 3Y)
```

### Views Format (P, Q Only)

```python
# Absolute view: "AAPL will return 10%"
views = {"P": [{"AAPL": 1}], "Q": [0.10]}

# Relative view: "NVDA will outperform AAPL by 20%"
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}

# NumPy format (for CSV/Excel data)
views = {"P": [[1, -1, 0]], "Q": [0.20]}
```

**Breaking Change**: Previous dict format (`{"AAPL": 0.10}`) is no longer supported

### Confidence Format

```python
confidence = 0.7        # Same for all views
confidence = [0.9, 0.8] # Different per view
confidence = None       # Default 0.5
```

**Removed**: dict format (`{"AAPL": 0.9}`) is no longer supported

### backtest_portfolio Parameters

```python
backtest_portfolio(
    tickers: list[str],           # ["AAPL", "MSFT", "GOOGL"]
    weights: dict[str, float],    # {"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25}
    period: str = "1Y",           # "1Y", "3Y", "5Y" (recommended)
    start_date: str = None,       # "2020-01-01" (choose either period or this)
    strategy: str = "passive_rebalance",  # buy_and_hold/passive_rebalance/risk_managed
    benchmark: str = "SPY",       # Benchmark (set None to disable)
    initial_capital: float = 10000.0,
    custom_config: dict = None,   # Advanced settings (overrides strategy)
    compare_strategies: bool = False,   # Compare all strategies (adds comparisons field)
    include_equal_weight: bool = False, # Compare equal-weight portfolio (adds equal_weight field)
    timeseries_freq: str = "monthly"    # daily/weekly/monthly (timeseries sampling frequency)
)
```

### Strategy Presets

| Strategy | Description | Rebalancing | Stop-Loss | MDD Limit |
|----------|-------------|-------------|-----------|-----------|
| `buy_and_hold` | Buy and hold | None | None | None |
| `passive_rebalance` | Passive investment (DEFAULT) | Monthly | None | None |
| `risk_managed` | Risk management | Monthly | 10% | 20% |

### Custom Config Options

```python
custom_config = {
    "rebalance_frequency": "quarterly",  # none/weekly/monthly/quarterly/semi-annual/annual
    "fees": 0.002,           # Transaction fees (0.2%)
    "slippage": 0.001,       # Slippage (0.1%)
    "stop_loss": 0.10,       # Stop-loss (10%)
    "take_profit": 0.30,     # Take-profit (30%)
    "trailing_stop": True,   # Trailing stop
    "max_drawdown_limit": 0.20  # MDD limit (20%)
}
```

### Backtest Output

```python
{
    # Performance Metrics
    "total_return": 0.25,      # Total return (25%)
    "cagr": 0.12,              # Compound annual growth rate (12%)
    "volatility": 0.18,        # Annual volatility (18%)
    "sharpe_ratio": 0.67,      # Sharpe ratio
    "sortino_ratio": 0.85,     # Sortino ratio
    "max_drawdown": -0.15,     # Maximum drawdown (-15%)
    "calmar_ratio": 0.80,      # Calmar ratio

    # Value Metrics
    "initial_capital": 10000.0,
    "final_value": 12500.0,

    # Cost Metrics
    "total_fees_paid": 45.0,
    "num_rebalances": 12,
    "turnover": 0.85,

    # Benchmark (if provided)
    "benchmark_return": 0.20,
    "excess_return": 0.05,     # Excess return
    "alpha": 0.03,             # Jensen's alpha
    "beta": 0.95,              # Beta
    "information_ratio": 0.35,

    # Tax Info
    "holding_periods": {
        "AAPL": {"days": 730, "is_long_term": True},
        ...
    },

    # Timeseries (adjust frequency with timeseries_freq)
    # - "daily": {"date": "2023-01-15", ...} (all trading days, large data for long periods)
    # - "weekly": {"date": "2023-01-20", ...} (Friday-based)
    # - "monthly": {"date": "2023-01", ...} (default, recommended)
    "timeseries": [
        {"date": "2023-01", "value": 10250, "benchmark": 10100, "drawdown": -0.02},
        {"date": "2023-02", "value": 10500, "benchmark": 10300, "drawdown": 0.0},
        ...
    ],

    # Drawdown Details
    "drawdown_details": {
        "max_drawdown": -0.15,
        "max_drawdown_start": "2023-03-01",
        "max_drawdown_end": "2023-04-15",
        "recovery_date": "2023-06-01",  # None if not recovered
        "recovery_days": 47              # None if not recovered
    },

    # Strategy Comparisons (only when compare_strategies=True)
    # Compares strategies other than the selected one
    # Each strategy: total_return, cagr, volatility, sharpe_ratio, sortino_ratio,
    #                max_drawdown, calmar_ratio, final_value
    "comparisons": {
        "buy_and_hold": {"total_return": 0.22, "sharpe_ratio": 0.58, "final_value": 12200, ...},
        "risk_managed": {"total_return": 0.18, "sharpe_ratio": 0.72, "final_value": 11800, ...}
    },

    # Equal Weight (only when include_equal_weight=True)
    # Compare with equal-weight portfolio
    "equal_weight": {
        "total_return": 0.20,
        "sharpe_ratio": 0.55,
        "final_value": 12000,
        "weights": {"AAPL": 0.333, "MSFT": 0.333, "GOOGL": 0.333}
    }
}
```

### VaR Warning System (NEW)

**Design philosophy**: Do not halt calculations, provide information for users to make their own judgment

EGARCH(1,1) model-based VaR analysis is performed when view returns exceed 40%:

```python
# Optimistic view example
result = optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    views={"P": [{"NVDA": 1}], "Q": [0.80]},  # 80% return prediction
    confidence=0.7
)

# Result includes warnings field
if "warnings" in result:
    for warning in result["warnings"]:
        print(warning)
        # Warning: VaR Alert: Your prediction (80%) exceeds the historical 95th percentile (75.9%).
```

**Warning trigger conditions**:
- Absolute View: Q > 40% and Q > 95th percentile return
- Relative View: Q > 95th percentile x 2

**VaR information lookup** (using `get_asset_stats`):

```python
# VaR 95% is integrated into get_asset_stats
stats = get_asset_stats(tickers=["NVDA"], period="1Y")
nvda = stats["assets"]["NVDA"]
print(f"VaR 95%: {nvda['var_95']:.1%}")           # 35%
print(f"95th percentile: {nvda['percentile_95']:.1%}")  # 75%
```

### Typical Workflow

```python
# Step 1: Portfolio optimization (VaR warnings automatically included)
bl_result = optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="1Y",
    views={"P": [{"AAPL": 1, "MSFT": -1}], "Q": [0.10]},
    confidence=0.7
)

# Step 1.5: Check warnings (if any)
if "warnings" in bl_result:
    print("VaR Warning:", bl_result["warnings"])

# Step 2: Backtest with optimization results
backtest_result = backtest_portfolio(
    tickers=["AAPL", "MSFT", "GOOGL"],
    weights=bl_result["weights"],  # Use optimize result directly
    period="3Y",
    strategy="passive_rebalance",
    benchmark="SPY"
)
```

## Design Decisions

### Ticker Order Preserved

User input order is preserved (not sorted)
- Ensures index consistency in NumPy P format
- `load_prices()` generates DataFrame columns in input order

### Risk Aversion Calculation

**Portfolio-based Idzorek method** used:

1. `_calculate_portfolio_risk_aversion()` auto-calculation
   - Formula: delta = (E(r) - rf) / sigma_portfolio^2
   - sigma_portfolio^2 = w_mkt^T x Sigma x w_mkt (uses portfolio's own data)
2. `investment_style` multiplier applied:
   - aggressive: delta x 0.5
   - balanced: delta x 1.0
   - conservative: delta x 2.0
3. Fallback to 2.5 when calculation fails

### Market Caps (Auto-loaded)

```python
# data_loader.py
get_market_caps(tickers)
# 1. Check Parquet cache (data/market_caps.parquet)
# 2. Download from yfinance if not found
# 3. Cache to Parquet on success
# 4. Fallback to equal weight on failure
```

### Prior Calculation

`market_implied_prior_returns(mcaps, delta, Sigma)` -> pi = delta * Sigma * w_mkt

- Market caps auto-loaded (yfinance)
- Fallback to equal weight on failure

## File Structure

```
bl_mcp/
├── server.py      # MCP interface
├── tools.py       # Business logic
└── utils/
    ├── data_loader.py   # Parquet loading, auto-download
    ├── validators.py    # Input validation, period parsing
    ├── risk_models.py   # EGARCH VaR calculation (NEW)
    └── session.py       # HTTP session

tests/
├── test_simple.py           # Basic tests
├── test_var_validation.py   # VaR validation tests (NEW)
├── test_var_warning_output.py  # VaR warning output tests (NEW)
└── ...

memory-bank/             # Detailed documentation (history)
```

## Quick Commands

```bash
make test-simple    # Run tests
make server-stdio   # For Windsurf/Claude
make server-http    # For Google ADK
```

## Google ADK Usage

To test the MCP server through Google ADK Web UI:

```bash
# 1. Run HTTP server (Terminal 1)
make server-http    # Start MCP server at localhost:5000

# 2. Run ADK Web UI (Terminal 2)
make web-ui         # Start ADK Web UI at localhost:8000
```

Open `http://localhost:8000` in your browser to test MCP tools in the ADK Web UI.

**Note**: ADK-related dependencies are required (`make install` or `uv sync --extra agent`)

## Recent Changes (2025-11-24)

### Phase 3 Improvements (This Update)

1. **`get_asset_stats` new tool**:
   - Per-asset statistics (price, return, volatility, Sharpe, market cap)
   - Includes VaR 95% and 95th percentile (EGARCH-based)
   - Provides correlation matrix, covariance matrix
   - `calculate_var_egarch` tool integrated and removed

2. **`backtest_portfolio` extensions**:
   - `timeseries`: Monthly sampled portfolio values
   - `drawdown_details`: Max drawdown start/end/recovery dates
   - `compare_strategies`: Compare all strategies at once
   - `include_equal_weight`: Compare equal-weight portfolio

3. **`optimize_portfolio_bl` extensions**:
   - `sensitivity_range`: Sensitivity analysis by confidence level
   - e.g., `[0.3, 0.5, 0.9]` -> Results at each confidence level

4. **`upload_price_data` integration**:
   - `upload_price_data_from_file` functionality integrated
   - Choose either `prices` or `file_path`

5. **Tool count optimization**: Maintained at 5 (functionality extended)

### Previous Updates (2025-11-23)

- VaR warning system, automatic market cap loading, Parquet caching, etc.

## Custom Data Support

### Usage Scenarios

| Case | Method | Example |
|------|--------|---------|
| Small data (< 100 rows) | `upload_price_data(prices=...)` | LLM passes data |
| Large data / Files | `upload_price_data(file_path=...)` | CSV/Parquet path |
| External MCP integration | Pass file path | Other MCP saves file -> bl-mcp loads |

### Upload Examples

```python
# 1. Direct upload (small data) - prices parameter
upload_price_data(
    ticker="005930.KS",  # Samsung Electronics
    prices=[
        {"date": "2024-01-02", "close": 78000.0},
        {"date": "2024-01-03", "close": 78500.0},
        ...
    ],
    source="pykrx"
)

# 2. Load from file (large data) - file_path parameter
upload_price_data(
    ticker="KOSPI",
    file_path="/path/to/kospi.csv",
    date_column="Date",
    close_column="Close"
)

# 3. Optimize after upload
optimize_portfolio_bl(
    tickers=["005930.KS", "AAPL"],  # Mix custom + existing tickers
    period="1Y"
)
```

### External MCP Integration Pattern

```
[External MCP: pykrx-mcp]          [bl-mcp]
get_korean_stock_prices()  ->  upload_price_data(file_path=...)
  └── /tmp/005930.parquet        └── Copy to internal cache

optimize_portfolio_bl(["005930.KS", "AAPL"])
```

### Data Requirements

- Minimum 10 data points (recommended: 60+ days)
- Date format: "YYYY-MM-DD"
- Close price field required
- Custom tickers tracked in `data/custom_tickers.json`

## Known Issues

- Risk aversion calculation falls back to 2.5 when price data is insufficient

## Phase 2 Plan (Decided 2025-11-23)

### Project Separation Decision

**bl-mcp (this project)**: MCP Tools only (pure library)
**bl-orchestrator (separate project)**: Multi-agent view generation (CrewAI)

### Phase 2 Scope (Reduced)

| Tool | Status | Description |
|------|--------|-------------|
| `optimize_portfolio_bl` | Existing | BL optimization |
| `backtest_portfolio` | Complete | Portfolio backtesting |
| `calculate_hrp_weights` | NEW Optional | HRP optimization (BL alternative) |

**Excluded features** (moved to bl-orchestrator):
- ~~`generate_views_from_technicals`~~
- ~~`generate_views_from_fundamentals`~~
- ~~`generate_views_from_sentiment`~~

### View Generation Strategy

**Decision**: Generate views through multi-agent debate

```
Previous plan (complex):
  Technical/Fundamental -> Rule-based logic -> P, Q, confidence
                          ^ Arbitrary, hard to justify

New approach (simple + powerful):
  Multi-agent debate -> LLM reasoning -> P, Q, confidence
                        ^ LLM makes direct judgment
```

**Reasons**:
1. Absolute views ("AAPL will rise 10%") are nearly impossible to predict
2. Relative views ("AAPL will outperform MSFT") can be justified through debate
3. LLM reviews data and debates directly -> More flexible and explainable

### Expected Workflow (bl-orchestrator)

```
1. Data Collection: AAPL, MSFT fundamentals/technicals/news

2. Agent Debate:
   Bull: "AAPL has low P/E and strong momentum, will outperform MSFT by 15%"
   Bear: "AAPL growth slowing, MSFT cloud strength, 5% is realistic"
   Moderator: "Consensus: AAPL > MSFT by 8%, confidence 65%"

3. Output:
   {"P": [{"AAPL": 1, "MSFT": -1}], "Q": [0.08], "confidence": [0.65]}

4. Call bl-mcp:
   optimize_portfolio_bl(tickers, views=output)
   backtest_portfolio(tickers, weights=result)
```

## Reference

See `memory-bank/` for detailed documentation:
- `activeContext.md` - Recent changes
- `systemPatterns.md` - Design patterns
- `progress.md` - Overall progress
