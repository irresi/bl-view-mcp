# Product Context

## Why This Project is Needed

### Problem Definition

1. **Limitations of Traditional Portfolio Optimization**
   - Mean-Variance optimization is sensitive to inputs and unstable
   - Tends to suggest extreme positions
   - Difficult to incorporate investor views

2. **Gap Between AI and Financial Analysis**
   - AI needs to handle complex libraries directly to perform financial analysis
   - Inconvenience of writing code for each step
   - Lack of reusable modules

### Advantages of the Black-Litterman Model

1. **Bayesian Approach**: Prior (market equilibrium) + investor views = stable portfolio
2. **View Integration**: Quantifies confidence to reflect views quantitatively
3. **Market Neutral**: Without views, reverts to market-cap weighted portfolio

### Value of MCP Protocol

- AI performs financial analysis as a **tool**
- Server handles complex calculations, AI focuses on decision-making
- Reusable and extensible architecture

## User Experience Goals

### Primary User: AI Agent (Windsurf, Claude)

**Workflow:**

1. User: "Optimize a portfolio with AAPL, MSFT, GOOGL. I think AAPL will return 10%."
2. AI automatically calls `optimize_portfolio_bl` Tool:
   ```python
   optimize_portfolio_bl(
       tickers=["AAPL", "MSFT", "GOOGL"],
       period="1Y",
       views={"P": [{"AAPL": 1}], "Q": [0.10]},
       confidence=0.7
   )
   ```
3. Data collection -> Expected returns -> Covariance -> Optimization performed automatically
4. Result explanation and visualization

**Expected Benefits:**
- Users only need financial knowledge (no coding required)
- **Single Tool** performs complex analysis in one call
- Repeatable analysis workflow

### Secondary User: Developers (ADK Agent)

**Workflow:**

1. Run HTTP server
2. Build automation systems with ADK Agent
3. Production workflows like periodic rebalancing, alerts

## Core Features

### Essential Features (Phase 1) - ✅ Complete

- [x] Data collection (yfinance -> Parquet)
- [x] `optimize_portfolio_bl` integrated Tool implementation
  - Expected returns calculation (historical)
  - Covariance matrix calculation (Ledoit-Wolf)
  - Investor views (P, Q format - Absolute/Relative support)
  - Idzorek Confidence for Omega inversion
  - Black-Litterman optimization

### Important Features (Phase 2)

- [ ] Backtesting (rebalancing, performance metrics)
- [ ] Factor scoring (value, growth, momentum, etc.)
- [ ] HRP weight calculation
- [ ] Additional Tool separation (if needed)

### Optional Features (Phase 3-4)

- [ ] Korean stock support (pykrx)
- [ ] Cryptocurrency support (ccxt)
- [ ] ADK Agent integration
- [ ] Multi-agent system

## Usage Scenarios

### Scenario 1: Basic Absolute View

```
User: "Optimize a portfolio with AAPL, MSFT, GOOGL.
      I think AAPL will return 10%. I'm fairly confident."

AI call:
optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="1Y",
    views={"P": [{"AAPL": 1}], "Q": [0.10]},
    confidence=0.75
)

Result: Optimal weights + expected return + Sharpe ratio
```

### Scenario 2: Relative View

```
User: "I think NVDA will outperform AAPL by 20%. Very confident!"

AI call:
optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    period="1Y",
    views={"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]},
    confidence=0.95
)

Result: NVDA weight increased, AAPL weight decreased
```

### Scenario 3: Multiple Views

```
User: "NVDA will return 30%, and AAPL will outperform MSFT by 5%."

AI call:
optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    period="1Y",
    views={
        "P": [{"NVDA": 1}, {"AAPL": 1, "MSFT": -1}],
        "Q": [0.30, 0.05]
    },
    confidence=[0.9, 0.7]
)

Result: Portfolio reflecting both Absolute + Relative views
```

## Product Philosophy

1. **Transparency**: Return all intermediate results clearly
2. **Modularity**: Each tool can be used independently
3. **Flexibility**: Support both stdio and HTTP
4. **Stability**: Thorough input validation and error handling
5. **Extensibility**: Easy to add new asset classes and models

## Success Metrics

1. **Functional**: All scenarios work
2. **Performance**: Each Tool responds within 10 seconds
3. **Usability**: AI performs complex analysis with natural language
4. **Reliability**: Clear error messages on failure
