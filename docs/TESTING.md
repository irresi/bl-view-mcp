# Testing Guide

## Quick Start

```bash
# 1. Download data (auto-download from GitHub Release)
make download-data

# 2. Run tests
make test-simple
```

---

## Test Methods

### Method 1: Direct Test (Fastest)

Call tools directly without MCP server.

```bash
make test-simple
# or
uv run python tests/test_simple.py
```

**Test Scenarios:**
1. Basic Optimization (No Views)
2. Absolute View (AAPL +10%)
3. Relative View (NVDA > AAPL by 20%)
4. NumPy P Format
5. Investment Styles
6. Multiple Views with Per-View Confidence

**Direct Call Example:**
```python
from bl_mcp.tools import optimize_portfolio_bl

# Absolute View
result = optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="1Y",
    views={"P": [{"AAPL": 1}], "Q": [0.10]},
    confidence=0.7
)

# Relative View
result = optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    period="1Y",
    views={"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]},
    confidence=0.85
)
```

---

### Method 2: ADK Agent Test

```bash
# Terminal 1: Start MCP server
make server-http

# Terminal 2: Run agent test
make test-agent
```

---

### Method 3: Web UI Test

```bash
# Terminal 1: Start MCP server
make server-http

# Terminal 2: Start Web UI
make web-ui
```

Open http://localhost:8000 in browser

---

## Expected Output

### On Success:
```
✅ Success!

📊 Portfolio Weights:
  AAPL: 33.33%
  MSFT: 33.33%
  GOOGL: 33.33%

📈 Performance:
  Expected Return: 13.46%
  Volatility: 23.20%
  Sharpe Ratio: 0.58
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Data file not found" | `make download-data` |
| "Module not found" | `uv sync` |
| "Connection refused" | Check MCP server is running |

### Server Connection Failed:
```bash
# Check ports
lsof -i :5000
lsof -i :8000

# Restart server
make server-http
```
