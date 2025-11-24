# System Patterns

## Current Architecture (2025-11-23)

```
┌─────────────────┐
│   AI Client     │  (Claude, Windsurf, ADK)
└────────┬────────┘
         │ MCP Protocol
┌────────▼────────┐
│  server.py      │  @mcp.tool (only 1)
│  optimize_      │
│  portfolio_bl   │
└────────┬────────┘
         │
┌────────▼────────┐
│  tools.py       │  Business Logic
│  ├─ _parse_views()
│  └─ _normalize_confidence()
└────────┬────────┘
         │
┌────────▼────────┐
│ PyPortfolioOpt  │  BlackLittermanModel
└────────┬────────┘
         │
┌────────▼────────┐
│ data/*.parquet  │  503 tickers
└─────────────────┘
```

---

## Key Design Decisions

### 1. Single Tool Design

**Reason**: Prevent LLM from unnecessarily calling intermediate steps

```python
# Before: Required 4 Tool chaining
returns = calculate_expected_returns(...)
cov = calculate_covariance_matrix(...)
view = create_investor_view(...)
portfolio = optimize_portfolio_bl(returns, cov, view)

# Now: Complete with 1 Tool
portfolio = optimize_portfolio_bl(tickers, views, confidence)
```

### 2. P, Q Format Only

**Reason**: Prevent LLM confusion, API consistency

```python
# ❌ Removed
views = {"AAPL": 0.10}

# ✅ Only format
views = {"P": [{"AAPL": 1}], "Q": [0.10]}           # Absolute
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}  # Relative
views = {"P": [[1, -1, 0]], "Q": [0.20]}            # NumPy
```

### 3. Preserve Ticker Order

**Reason**: NumPy P format index consistency

```python
# Preserve user input order as-is
tickers = ["NVDA", "AAPL", "MSFT"]  # No sorting
```

---

## Key Patterns

### Views Parsing

```python
def _parse_views(views: dict, tickers: list[str]):
    P_input = views["P"]
    Q = np.array(views["Q"])

    if isinstance(P_input[0], dict):
        # Dict-based P: [{"NVDA": 1, "AAPL": -1}]
        P = np.zeros((len(P_input), len(tickers)))
        for i, view_dict in enumerate(P_input):
            for ticker, weight in view_dict.items():
                j = tickers.index(ticker)
                P[i, j] = weight
    else:
        # NumPy P: [[1, -1, 0]]
        P = np.array(P_input)

    return P, Q
```

### Confidence Normalization

```python
def _normalize_confidence(confidence, views, tickers):
    num_views = len(views["Q"])

    if confidence is None:
        return [0.5] * num_views      # Default
    elif isinstance(confidence, (int, float)):
        return [confidence] * num_views  # Same for all views
    elif isinstance(confidence, list):
        return confidence              # Different per view
```

### Risk Aversion Calculation

```python
# Calculate market-implied delta using SPY
base_delta = market_implied_risk_aversion(spy_prices)

# Apply investment_style multiplier
multipliers = {
    "aggressive": 0.5,
    "balanced": 1.0,
    "conservative": 2.0
}
risk_aversion = base_delta * multipliers[style]
```

---

## Error Handling

```python
# Clear error for old format usage
if "P" not in views or "Q" not in views:
    raise ValueError(
        "Views must use P, Q format. "
        "Example: {'P': [{'AAPL': 1}], 'Q': [0.10]}"
    )
```

---

## Test Patterns

```python
# 6 core scenarios
def test_optimize_basic()              # No views
def test_optimize_with_absolute_view() # P, Q absolute
def test_optimize_with_relative_view() # P, Q relative
def test_optimize_with_numpy_p()       # NumPy format
def test_investment_styles()           # aggressive/balanced/conservative
def test_multiple_views()              # Per-view confidence
```

---

---

## Project Separation Architecture (2025-11-23)

```
┌─────────────────────────────────────────────────────────┐
│  bl-orchestrator (separate project)                     │
│  ├── CrewAI Multi-agent                                 │
│  │   ├── Bull Agent (optimistic view)                   │
│  │   ├── Bear Agent (pessimistic view)                  │
│  │   └── Moderator Agent (consensus building)           │
│  └── Output: {"P": [...], "Q": [...], "confidence": [...]}│
└──────────────────────┬──────────────────────────────────┘
                       │ MCP Protocol
┌──────────────────────▼──────────────────────────────────┐
│  bl-mcp (this project)                                  │
│  ├── optimize_portfolio_bl (existing)                   │
│  ├── backtest_portfolio (Phase 2)                       │
│  └── calculate_hrp_weights (Phase 2, optional)          │
└─────────────────────────────────────────────────────────┘
```

### View Generation Strategy Change

**Previous Plan (abandoned)**:
```python
# Rule-based - arbitrary
if rsi < 30:
    Q = 0.05  # Why 5%?
    confidence = 0.6  # Why 60%?
```

**New Approach (adopted)**:
```
Multi-agent debate:
  Bull: "AAPL has low P/E and strong momentum, 15% outperformance"
  Bear: "Growth slowing, 5% is realistic"
  Moderator: "Consensus: 8%, confidence 65%"
```

**Reasons**:
1. Absolute views are unpredictable (who knows if AAPL will rise exactly 10%?)
2. Relative views can be justified through debate ("A will outperform B")
3. LLM reasoning directly from data is more flexible than rules

---

## Reference

Detailed context: `CLAUDE.md` (auto-loaded by Claude Code)
