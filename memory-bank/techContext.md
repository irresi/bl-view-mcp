# Technical Context

## Technology Stack

### Core Frameworks

#### FastMCP 2.13.0.1

**Role**: MCP Server Framework

**Selection Reasons**:
- Concise implementation with `@mcp.tool` decorator
- stdio/HTTP dual transport modes
- Automatic Python type hints conversion
- Minimal boilerplate

**Usage Pattern**:
```python
from fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool
def my_tool(param: str) -> dict:
    """Tool description"""
    return {"result": "success"}

# stdio mode
mcp.run(transport="stdio")

# HTTP mode
mcp.run(transport="http", host="localhost", port=5000)
```

#### PyPortfolioOpt 1.5.5+

**Role**: Core portfolio optimization library

**Key Modules**:
- `expected_returns`: Expected returns calculation
  - `mean_historical_return()`: Historical mean
  - `ema_historical_return()`: Exponential moving average
  - `capm_return()`: CAPM model

- `risk_models`: Covariance matrix calculation
  - `sample_cov()`: Sample covariance
  - `ledoit_wolf()`: Ledoit-Wolf shrinkage estimation
  - `exp_cov()`: Exponentially weighted covariance

- `black_litterman.BlackLittermanModel`: Black-Litterman optimization
  - Define views with P, Q matrices
  - Use `omega="idzorek"` + `view_confidences`
  - `bl_weights()`: Calculate optimal weights
  - `bl_returns()`: Posterior expected returns

- `hierarchical_portfolio.HRPOpt`: Hierarchical Risk Parity
  - `optimize()`: Calculate HRP weights

**Documentation**: https://pyportfolioopt.readthedocs.io/

### Data Processing

#### Pandas 2.0.0+

**Role**: Data manipulation and analysis

**Main Usage**:
- Time series data processing
- Missing value handling (`fillna`, `dropna`)
- Resampling (`resample`)
- Returns calculation (`pct_change`)

#### NumPy 1.24.0+

**Role**: Numerical computation

**Main Usage**:
- Matrix operations (covariance, inverse)
- Statistical functions (mean, standard deviation)
- Linear algebra (`np.linalg`)

#### yfinance 0.2.0+

**Role**: Market data collection

**Usage Pattern**:
```python
import yfinance as yf

# Price data
ticker = yf.Ticker("AAPL")
hist = ticker.history(start="2023-01-01", end="2024-01-01")

# Fundamental data
info = ticker.info  # Market cap, PE ratio, etc.

# Save to Parquet
hist.to_parquet(f"data/prices/{ticker}.parquet")
```

### Backtesting (Phase 2)

#### empyrical (Recommended)

**Role**: Performance metrics calculation

**Key Functions**:
- `annual_return()`: Annual return
- `sharpe_ratio()`: Sharpe ratio
- `max_drawdown()`: Maximum drawdown
- `sortino_ratio()`: Sortino ratio
- `alpha_beta()`: Alpha, Beta

#### VectorBT (Optional)

**Role**: Portfolio backtesting

**Advantages**:
- Fast performance with vectorized operations
- Built-in rebalancing
- Multi-asset portfolio support

### Optional Dependencies

#### Google ADK 1.14.1 (Phase 4)

**Role**: AI Agent framework

**Installation**: `pip install -e ".[agent]"`

**Usage Pattern**:
```python
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

agent = Agent(
    model="gemini-2.5-flash",
    tools=[MCPToolset(connection_params=...)]
)
```

#### ccxt (Phase 3 - Cryptocurrency)

**Role**: Cryptocurrency exchange data

**Supported Exchanges**: Binance, Upbit, Coinbase, etc.

#### pykrx (Phase 3 - Korean Stocks)

**Role**: Korean securities market data

**Key Features**:
- KRX stock data
- Market cap, trading volume
- Sector classification

## Development Environment

### Python Version

- **Requirement**: Python 3.11+
- **Reasons**:
  - Modern type hints (`str | None`)
  - Improved performance
  - FastMCP compatibility

### Package Manager

#### uv (Recommended)

```bash
# Project initialization
uv init

# Install dependencies
uv sync

# Add dependencies
uv add fastmcp pypfopt pandas numpy yfinance
```

**Advantages**:
- Rust-based fast installation
- Native `pyproject.toml` support
- Automatic virtual environment management

#### pip (Alternative)

```bash
pip install -e .
pip install -e ".[agent]"  # Include ADK Agent
```

### pyproject.toml Structure

```toml
[project]
name = "black-litterman-mcp"
version = "0.1.0"
description = "Black-Litterman Portfolio Optimization MCP Server"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastmcp==2.13.0.1",
    "PyPortfolioOpt>=1.5.5",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "yfinance>=0.2.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
agent = [
    "google-adk[a2a]==1.14.1",
    "google-genai>=1.38.0",
]
dev = [
    "pytest>=7.4.0",
    "mypy>=1.5.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
backtest = [
    "empyrical>=0.5.5",
    "vectorbt>=0.25.0",
]
```

## Development Tools

### Code Quality

#### mypy (Type Checker)

```bash
mypy bl_mcp/ --strict
```

**Configuration** (pyproject.toml):
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

#### ruff (Linter + Formatter)

```bash
ruff check bl_mcp/
ruff format bl_mcp/
```

**Advantages**: Replaces Black + isort + flake8, very fast

### Testing

#### pytest

```bash
pytest tests/ -v
```

**Structure**:
```
tests/
├── test_tools.py           # Unit tests
├── test_validators.py      # Validation logic
├── test_data_loader.py     # Data loading
└── test_integration.py     # End-to-end
```

## Data Storage

### Parquet File Structure

```
data/
├── prices/                 # OHLCV data
│   ├── AAPL.parquet       # Columns: Date, Open, High, Low, Close, Volume
│   ├── MSFT.parquet
│   └── ...
├── fundamentals/           # Fundamental data
│   └── market_cap.parquet # Columns: Date, Ticker, MarketCap
└── metadata.json           # Metadata (update time, etc.)
```

### Data Update Script

```python
# scripts/update_data.py
import yfinance as yf
from pathlib import Path

def update_ticker_data(ticker: str, start_date: str):
    data = yf.Ticker(ticker).history(start=start_date)
    output_path = Path(f"data/prices/{ticker}.parquet")
    data.to_parquet(output_path)
```

## Environment Variables

### .env File

```bash
# API Keys (optional)
ALPHA_VANTAGE_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here

# Data path
DATA_PATH=./data

# Cache settings
CACHE_ENABLED=true
CACHE_TTL=3600

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bl_mcp.log
```

### python-dotenv Usage

```python
from dotenv import load_dotenv
import os

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH", "./data")
```

## Communication Protocol

### MCP (Model Context Protocol)

**Concept**: Standard protocol between AI and tools

**Message Format**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "calculate_expected_returns",
    "arguments": {
      "tickers": ["AAPL", "MSFT"],
      "start_date": "2023-01-01",
      "method": "historical_mean"
    }
  }
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "tickers": ["AAPL", "MSFT"],
    "expected_returns": {
      "AAPL": 0.12,
      "MSFT": 0.15
    }
  }
}
```

### stdio vs HTTP

| Feature | stdio | HTTP |
|---------|-------|------|
| Use Case | IDE integration | Production, Web |
| Setup | MCP config | URL |
| Debugging | Difficult | Easy (curl, Postman) |
| Multi-client | Not possible | Possible |
| Security | Local only | Authentication required |

## Constraints

### Performance

- **Target**: Each Tool call < 10 seconds
- **Bottleneck**: Data I/O, matrix operations
- **Optimization**: Caching, parallel processing

### Memory

- **Limit**: Process within local memory
- **Large Data**: Chunking, streaming

### Data Quality

- **yfinance Constraints**:
  - Free API, rate limited
  - Possible data gaps
  - Limited fundamental data

## Future Technical Considerations

### Phase 3

- **Korean Stocks**: pykrx, FinanceDataReader
- **Cryptocurrency**: ccxt
- **Real-time Data**: WebSocket, paid APIs

### Phase 4

- **ADK Agent**: Gemini-based automation
- **Multi-agent**: Separate data collection, analysis, optimization
- **Web UI**: FastAPI + React (optional)

### Scalability

- **Docker Deployment**: Consistent environment
- **Cloud Deployment**: AWS Lambda, Cloud Run
- **Scaling**: Redis caching, distributed processing
