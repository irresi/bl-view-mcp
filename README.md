# Black-Litterman Portfolio Optimization MCP Server

[![PyPI](https://img.shields.io/pypi/v/black-litterman-mcp)](https://pypi.org/project/black-litterman-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/black-litterman-mcp)](https://pypi.org/project/black-litterman-mcp/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Black-Litterman portfolio optimization** MCP server for AI agents

Works with Claude Desktop, Windsurf IDE, Google ADK, and any MCP-compatible AI

## Features

- **Portfolio Optimization** - Black-Litterman model with sensitivity analysis
- **Investor Views** - Absolute/relative views with confidence levels
- **Backtesting** - Strategy comparison, drawdown analysis, timeseries
- **Asset Analysis** - Correlation matrix, VaR, per-asset statistics
- **Dashboard Generation** - Visualization hints for AI-generated charts
- **Multiple Assets** - S&P 500, NASDAQ 100, ETF, Crypto, custom data

---

## Quick Start (Claude Desktop)

### Step 1: Find uvx path

Run in terminal:
```bash
which uvx
# Example output: /Users/USERNAME/.local/bin/uvx
```

> If uvx is not installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Step 2: Configure Claude Desktop

Config file location:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

File content (replace with your uvx path):

```json
{
  "mcpServers": {
    "black-litterman": {
      "command": "/Users/USERNAME/.local/bin/uvx",
      "args": ["black-litterman-mcp"]
    }
  }
}
```

### Step 3: Restart Claude Desktop

**Cmd+Q** (macOS) or fully quit and restart

### Step 4: Use

Ask Claude:

> "Optimize a portfolio with AAPL, MSFT, GOOGL. I think AAPL will return 10%."

> **First run**: S&P 500 data auto-downloads (~30 seconds)

> **Tip**: Want charts or dashboards? Just ask: "Show me a dashboard with the results" or "Create a visualization of the portfolio weights"

### Example Use Cases

Try these prompts with Claude:

> **Note**: Default period is **1 year** for all tools. All returns are **annualized** - when you say "outperform by 40%", it means 40% annual return expectation.

**Basic Optimization + Visualization**
> Optimize a portfolio with AAPL, MSFT, GOOGL, NVDA. I am confident that NVDA will outperform others by 40%. Show me a dashboard.

**Backtesting with Benchmark**
> Backtest the above optimized portfolio for 3 years and compare with SPY.

**Strategy Comparison**
> Compare buy_and_hold, passive_rebalance, and risk_managed strategies for this portfolio.

**Correlation Analysis**
> Analyze the correlation between NVDA, AMD, and INTC.

**Sensitivity Analysis**
> Create a portfolio with AAPL and MSFT. I expect AAPL to return 15%. Run sensitivity analysis with confidence levels 0.3, 0.5, 0.7, 0.9.

### Demo Dashboards

Generated using the example prompts above with Claude Desktop:

<ins>Click images</ins> to view interactive HTML dashboards:

| Optimization | Backtest | Strategy |
|:---:|:---:|:---:|
| [![Optimization](https://raw.githubusercontent.com/irresi/bl-view-mcp/main/examples/screenshots/demo_optimization.png)](https://irresi.github.io/bl-view-mcp/examples/dashboards/demo_optimization.html) | [![Backtest](https://raw.githubusercontent.com/irresi/bl-view-mcp/main/examples/screenshots/demo_backtest.png)](https://irresi.github.io/bl-view-mcp/examples/dashboards/demo_backtest.html) | [![Strategy](https://raw.githubusercontent.com/irresi/bl-view-mcp/main/examples/screenshots/demo_strategy.png)](https://irresi.github.io/bl-view-mcp/examples/dashboards/demo_strategy.html) |

| Correlation | Sensitivity |
|:---:|:---:|
| [![Correlation](https://raw.githubusercontent.com/irresi/bl-view-mcp/main/examples/screenshots/demo_correlation.png)](https://irresi.github.io/bl-view-mcp/examples/dashboards/demo_correlation.html) | [![Sensitivity](https://raw.githubusercontent.com/irresi/bl-view-mcp/main/examples/screenshots/demo_sensitivity.png)](https://irresi.github.io/bl-view-mcp/examples/dashboards/demo_sensitivity.html) |

---

## Other Installation Methods

### Windsurf IDE

`.windsurf/mcp_config.json`:
```json
{
  "mcpServers": {
    "black-litterman": {
      "command": "/Users/USERNAME/.local/bin/uvx",
      "args": ["black-litterman-mcp"]
    }
  }
}
```

### From Source (Developers)

```bash
git clone https://github.com/irresi/bl-view-mcp.git
cd bl-view-mcp
make install
make download-data  # S&P 500 data
make test-simple
```

### Docker

```bash
docker build -t bl-mcp .
docker run -p 5000:5000 -v $(pwd)/data:/app/data bl-mcp
```

### Google ADK Web UI

Test with [Google ADK](https://github.com/google/adk-python) (Agent Development Kit):

```bash
# Terminal 1: Start MCP HTTP server
make server-http  # localhost:5000

# Terminal 2: Start ADK Web UI
make web-ui       # localhost:8000
```

Open http://localhost:8000 in browser

> Requires `make install` (includes google-adk dependency)

---

## Supported Datasets

| Dataset | Tickers | Description |
|---------|---------|-------------|
| `snp500` | ~500 | S&P 500 constituents (default) |
| `nasdaq100` | ~100 | NASDAQ 100 constituents |
| `etf` | ~130 | Popular ETFs |
| `crypto` | ~100 | Cryptocurrencies |
| `custom` | - | User-uploaded data |

**PyPI install**: S&P 500 data auto-downloads on first run

**Source install**: Download additional datasets manually
```bash
make download-data       # S&P 500 (default)
make download-nasdaq100  # NASDAQ 100
make download-etf        # ETF
make download-crypto     # Crypto
```

---

## MCP Tools

### `optimize_portfolio_bl`

Calculate optimal portfolio weights using Black-Litterman model.

```python
optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="1Y",
    views={"P": [{"AAPL": 1}], "Q": [0.10]},  # AAPL expected 10% return
    confidence=0.7,
    investment_style="balanced"  # aggressive / balanced / conservative
)
```

**Views examples**:
```python
# Absolute view: "AAPL will return 10%"
views = {"P": [{"AAPL": 1}], "Q": [0.10]}

# Relative view: "NVDA will outperform AAPL by 20%"
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
```

**VaR Warning**: When predicted returns exceed 40%, EGARCH-based VaR analysis is automatically included in the `warnings` field.

### `backtest_portfolio`

Validate portfolio strategy with historical data.

```python
backtest_portfolio(
    tickers=["AAPL", "MSFT", "GOOGL"],
    weights={"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25},
    period="3Y",
    strategy="passive_rebalance",  # buy_and_hold / passive_rebalance / risk_managed
    benchmark="SPY"
)
```

### `get_asset_stats`

Get asset statistics including VaR, correlation matrix, and covariance matrix.

```python
get_asset_stats(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="1Y",
    include_var=True  # Set False for faster response (skips EGARCH VaR)
)
# Returns: assets (price, return, volatility, sharpe, var_95, percentile_95),
#          correlation_matrix, covariance_matrix
```

### `upload_price_data`

Upload external data (international stocks, custom assets, etc.).

```python
# Direct upload (small data)
upload_price_data(
    ticker="005930.KS",  # Samsung Electronics
    prices=[
        {"date": "2024-01-02", "close": 78000.0},
        {"date": "2024-01-03", "close": 78500.0},
        ...
    ],
    source="custom"
)

# Or load from file (large data)
upload_price_data(
    ticker="CUSTOM_INDEX",
    file_path="/path/to/data.csv",
    date_column="Date",
    close_column="Close"
)
```

### `list_available_tickers`

Query available tickers.

```python
list_available_tickers(search="AAPL")        # Search
list_available_tickers(dataset="snp500")     # S&P 500 only
list_available_tickers(dataset="custom")     # Custom data
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/TESTING.md](docs/TESTING.md) | Testing guide |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical architecture |

---

## Tech Stack

- **MCP Server**: [FastMCP](https://github.com/jlowin/fastmcp)
- **Optimization**: [PyPortfolioOpt](https://github.com/robertmartin8/PyPortfolioOpt)
- **Risk Model**: [arch](https://github.com/bashtage/arch) (EGARCH)
- **Data**: yfinance, ccxt (crypto)

---

## License

MIT License - [LICENSE](LICENSE)

---

## Troubleshooting

### "spawn uvx ENOENT" / "uv binary not found"

Claude Desktop may not recognize system PATH. Use **absolute path**:

```bash
which uvx
# Use the output path in config
```

### "Data file not found"

Source install:
```bash
make download-data
```

PyPI install: Auto-downloads on first run (~30 seconds).

### "uv: command not found"

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Need more help?

- [GitHub Issues](https://github.com/irresi/bl-view-mcp/issues)
