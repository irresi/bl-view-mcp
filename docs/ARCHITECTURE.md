# Architecture

Technical architecture documentation for Black-Litterman MCP Server.

## Core Philosophy

**Prior (Market Equilibrium) + Views (AI Opinions) = Posterior (Optimal Portfolio)**

The Black-Litterman model is based on Bayesian statistics:
- **Prior**: Market-cap weighted portfolio (market equilibrium state)
- **Likelihood**: Investor views (expected returns input by AI)
- **Posterior**: Optimal portfolio weights

---

## MCP Tool Structure

```
server.py (@mcp.tool)
    ├── optimize_portfolio_bl()
    │       └── tools.py (business logic)
    │               ├── _parse_views()
    │               ├── _normalize_confidence()
    │               ├── _validate_views_optimism()  # VaR warning
    │               └── BlackLittermanModel(omega="idzorek")
    ├── backtest_portfolio()
    │       └── tools.py
    │               ├── _simulate_portfolio()
    │               ├── _calculate_returns_metrics()
    │               └── _calculate_benchmark_metrics()
    ├── get_asset_stats()                    # Asset statistics
    │       └── tools.py
    │               └── calculate_var_egarch()
    ├── upload_price_data()                  # prices + file_path unified
    │       └── data_loader.save_custom_price_data()
    └── list_available_tickers()
            └── data_loader.list_tickers()
```

### Design Principles

**Single Tool Design**: Minimal tools to prevent LLMs from making unnecessary intermediate calls.

Previously separate tools:
- ~~calculate_expected_returns~~
- ~~calculate_covariance_matrix~~
- ~~create_investor_view~~

→ All merged into `optimize_portfolio_bl` (improved token efficiency)

---

## Transport Modes

### stdio Mode

- **Use case**: Claude Desktop, Windsurf, Cline, and other MCP-compatible IDEs
- **Advantages**: Easy setup, fast development/testing

```
Tools → FastMCP Server (stdio) → Windsurf/Claude Desktop
```

### HTTP Mode

- **Use case**: Google ADK Agent, web service integration
- **Advantages**: Network access, multi-client support, easier debugging

```
Tools → FastMCP Server (HTTP) → ADK Agent (Gemini)
```

---

## Parameter Details

### optimize_portfolio_bl

```python
optimize_portfolio_bl(
    tickers: list[str],           # ["AAPL", "MSFT", "GOOGL"]
    period: str = "1Y",           # "1Y", "6M", "3M" (recommended)
    start_date: str = None,       # "2023-01-01" (alternative to period)
    views: dict = None,           # P, Q format only
    confidence: float | list = None,  # 0.0-1.0 or list
    investment_style: str = "balanced",  # aggressive/balanced/conservative
    risk_aversion: float = None,  # Advanced (not recommended)
    sensitivity_range: list[float] = None  # [0.3, 0.5, 0.9] confidence sensitivity
)
```

#### Views Format (P, Q Only)

```python
# Absolute view: "AAPL will return 10%"
views = {"P": [{"AAPL": 1}], "Q": [0.10]}

# Relative view: "NVDA will outperform AAPL by 20%"
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}

# Multiple views
views = {
    "P": [{"NVDA": 1, "AAPL": -1}, {"GOOGL": 1}],
    "Q": [0.25, 0.12]
}
confidence = [0.9, 0.6]  # Per-view confidence

# NumPy format (for CSV/Excel data)
views = {"P": [[1, -1, 0]], "Q": [0.20]}
```

#### Confidence Format

```python
confidence = 0.7        # Same for all views
confidence = [0.9, 0.8] # Per-view
confidence = None       # Default 0.5
```

### backtest_portfolio

```python
backtest_portfolio(
    tickers: list[str],           # ["AAPL", "MSFT", "GOOGL"]
    weights: dict[str, float],    # {"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25}
    period: str = "1Y",           # "1Y", "3Y", "5Y" (recommended)
    start_date: str = None,       # "2020-01-01" (alternative to period)
    strategy: str = "passive_rebalance",
    benchmark: str = "SPY",
    initial_capital: float = 10000.0,
    custom_config: dict = None,
    compare_strategies: bool = False,    # Compare all strategies
    include_equal_weight: bool = False,  # Compare equal-weight portfolio
    timeseries_freq: str = "monthly"     # daily/weekly/monthly
)
```

### get_asset_stats

```python
get_asset_stats(
    tickers: list[str],           # ["AAPL", "MSFT", "GOOGL"]
    period: str = "1Y",           # "1Y", "6M", "3M" (recommended)
    include_var: bool = True      # False for faster response (skip EGARCH VaR)
)
# Returns: assets, correlation_matrix, covariance_matrix, period
```

#### Strategy Presets

| Strategy | Description | Rebalancing | Stop-Loss | MDD Limit |
|----------|-------------|-------------|-----------|-----------|
| `buy_and_hold` | Buy and hold | None | None | None |
| `passive_rebalance` | Passive investing (DEFAULT) | Monthly | None | None |
| `risk_managed` | Risk management | Monthly | 10% | 20% |

#### Custom Config Options

```python
custom_config = {
    "rebalance_frequency": "quarterly",  # none/weekly/monthly/quarterly/semi-annual/annual
    "fees": 0.002,           # Trading fees (0.2%)
    "slippage": 0.001,       # Slippage (0.1%)
    "stop_loss": 0.10,       # Stop loss (10%)
    "take_profit": 0.30,     # Take profit (30%)
    "trailing_stop": True,   # Trailing stop
    "max_drawdown_limit": 0.20  # MDD limit (20%)
}
```

---

## Output Format

### optimize_portfolio_bl Output

```json
{
  "weights": {"AAPL": 0.33, "MSFT": 0.33, "GOOGL": 0.33},
  "expected_return": 0.12,
  "volatility": 0.23,
  "sharpe_ratio": 0.52,
  "posterior_returns": {"AAPL": 0.15, "MSFT": 0.12, "GOOGL": 0.11},
  "prior_returns": {"AAPL": 0.14, "MSFT": 0.13, "GOOGL": 0.12},
  "risk_aversion": 2.5,
  "has_views": true,
  "period": {"start": "2024-01-01", "end": "2025-01-01", "days": 252},
  "warnings": ["VaR Warning: ..."],  // (optional) VaR warnings for optimistic views
  "sensitivity": [                    // (optional) when sensitivity_range is used
    {"confidence": 0.3, "weights": {...}, "expected_return": 0.10, ...},
    {"confidence": 0.9, "weights": {...}, "expected_return": 0.14, ...}
  ],
  "_visualization_hint": {...}        // LLM dashboard generation guide
}
```

### backtest_portfolio Output

```json
{
  "total_return": 0.25,
  "cagr": 0.12,
  "volatility": 0.18,
  "sharpe_ratio": 0.67,
  "sortino_ratio": 0.85,
  "max_drawdown": -0.15,
  "calmar_ratio": 0.80,
  "initial_capital": 10000.0,
  "final_value": 12500.0,
  "total_fees_paid": 45.0,
  "num_rebalances": 12,
  "turnover": 0.85,
  "benchmark_return": 0.20,
  "excess_return": 0.05,
  "alpha": 0.03,
  "beta": 0.95,
  "information_ratio": 0.35,
  "holding_periods": {"AAPL": {"days": 730, "is_long_term": true}},
  "timeseries": [                         // Frequency controlled by timeseries_freq
    {"date": "2023-01", "value": 10250, "benchmark": 10100, "drawdown": -0.02}
  ],
  "drawdown_details": {                   // MDD details
    "max_drawdown": -0.15,
    "max_drawdown_start": "2023-03-01",
    "max_drawdown_end": "2023-04-15",
    "recovery_date": "2023-06-01",
    "recovery_days": 47
  },
  "comparisons": {...},                   // (optional) compare_strategies=True
  "equal_weight": {...},                  // (optional) include_equal_weight=True
  "_visualization_hint": {...}            // LLM dashboard generation guide
}
```

### get_asset_stats Output

```json
{
  "assets": {
    "AAPL": {
      "current_price": 180.50,
      "annual_return": 0.15,
      "volatility": 0.25,
      "sharpe_ratio": 0.52,
      "max_drawdown": -0.18,
      "market_cap": 2800000000000,
      "var_95": 0.35,
      "percentile_95": 0.75
    }
  },
  "correlation_matrix": {"AAPL": {"AAPL": 1.0, "MSFT": 0.75}},
  "covariance_matrix": {"AAPL": {"AAPL": 0.0625, "MSFT": 0.045}},
  "period": {"start": "2024-01-01", "end": "2025-01-01", "trading_days": 252},
  "_visualization_hint": {...}
}
```

---

## Internal Behavior

### Ticker Order Preserved

User input order is preserved (no sorting)
- Ensures index consistency in NumPy P format
- `load_prices()` generates DataFrame columns in input order

### Risk Aversion Calculation

1. Auto-calculated via `market_implied_risk_aversion()` using SPY data
2. `investment_style` multiplier applied:
   - aggressive: δ × 0.5
   - balanced: δ × 1.0
   - conservative: δ × 2.0
3. Fallback to 2.5 if SPY unavailable

### Market Caps (Auto-loaded)

```python
# data_loader.py
get_market_caps(tickers)
# 1. Check Parquet cache (data/market_caps.parquet)
# 2. Download from yfinance if not cached
# 3. Cache to Parquet on success
# 4. Fallback to equal weight on failure
```

### Prior Calculation

`market_implied_prior_returns(mcaps, δ, Σ)` → π = δΣw_mkt

---

## Project Structure

```
bl_mcp/                     # MCP Server Package
├── server.py               # FastMCP Server (@mcp.tool)
├── tools.py                # Core Logic
└── utils/
    ├── data_loader.py      # Parquet → DataFrame
    ├── validators.py       # Input Validation
    ├── risk_models.py      # EGARCH VaR Calculation
    └── session.py          # HTTP Session

bl_agent/                   # ADK Agent Package
├── agent.py                # Google ADK Agent
└── prompt.py               # Agent Prompt

scripts/                    # Data Download Scripts
├── download_data.py
├── download_sp500.py
└── ...

tests/
├── test_simple.py          # Basic Tests
└── ...

data/                       # Parquet Data
├── *.parquet               # Individual Stocks
├── market_caps.parquet     # Market Cap Cache
└── custom_tickers.json     # Custom Ticker List
```

---

## Tech Stack

### Data

- **Stocks/ETF**: yfinance
- **Crypto**: ccxt
- **Caching**: Parquet

### Models

- **Black-Litterman**: PyPortfolioOpt.black_litterman
- **Expected Returns**: PyPortfolioOpt.expected_returns
- **Covariance**: PyPortfolioOpt.risk_models

### MCP Framework

- **Server**: FastMCP 2.13.0.1
- **Agent**: Google ADK 1.14.1 (optional)

---

## Related Documentation

- [CONFIDENCE_SCALE.md](CONFIDENCE_SCALE.md) - Confidence scale guide
- [IDZOREK_VERIFICATION.md](IDZOREK_VERIFICATION.md) - Idzorek method implementation
- [RELATIVE_VIEWS_IMPLEMENTATION.md](RELATIVE_VIEWS_IMPLEMENTATION.md) - Relative view support
