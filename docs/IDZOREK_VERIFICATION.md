# Idzorek Black-Litterman Implementation

## Overview

This document describes the Idzorek method implementation for the Black-Litterman model.

**Status**: ✅ Verified and Production Ready

## Implementation

### Core Pattern

```python
bl = BlackLittermanModel(
    S,
    pi=market_prior,
    P=P,                               # Pick matrix
    Q=Q,                               # View returns
    omega="idzorek",                   # Omega back-calculated!
    view_confidences=conf_list         # [0.7, 0.8, ...]
)
```

**Key Principle**:
- User provides: `views` (P, Q format), `confidence` (float or list)
- Idzorek algorithm back-calculates: Ω (uncertainty matrix)

## Supported Formats

### P, Q Format

```python
# Absolute View
views = {"P": [{"AAPL": 1}], "Q": [0.10]}
confidence = 0.7

# Relative View
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
confidence = 0.85
```

### Per-View Confidence

```python
views = {
    "P": [{"NVDA": 1, "AAPL": -1}, {"GOOGL": 1}],
    "Q": [0.25, 0.12]
}
confidence = [0.9, 0.6]  # Different confidence per view
```

## Current Function Signature

```python
# bl_mcp/tools.py
def optimize_portfolio_bl(
    tickers: list[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    views: Optional[dict] = None,
    confidence: Optional[float | list] = None,
    investment_style: str = "balanced",
    risk_aversion: Optional[float] = None,
    sensitivity_range: Optional[list[float]] = None  # NEW in v0.3.x
) -> dict:
```

### Parameter Notes

- `market_caps`: Removed (auto-loaded from yfinance)
- `sensitivity_range`: Added in v0.3.x for confidence sensitivity analysis

## Validation Logic

- ✅ P, Q format validation
- ✅ Confidence type (float or list)
- ✅ Confidence length matches Q length
- ✅ Percentage input support (70 → 0.7)
- ✅ Unknown ticker detection

## Usage Examples

### Simple Case

```python
optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="1Y",
    views={"P": [{"AAPL": 1}], "Q": [0.10]},
    confidence=0.85
)
```

### Advanced Case (Per-View Confidence)

```python
optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="1Y",
    views={"P": [{"AAPL": 1}, {"MSFT": 1}], "Q": [0.10, 0.05]},
    confidence=[0.9, 0.6]
)
```

### Sensitivity Analysis (v0.3.x)

```python
optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="1Y",
    views={"P": [{"AAPL": 1}], "Q": [0.15]},
    confidence=0.7,
    sensitivity_range=[0.3, 0.5, 0.7, 0.9]  # Test multiple confidence levels
)
```

## Recommended Usage

```python
# Absolute View
views = {"P": [{"AAPL": 1}], "Q": [0.10]}
confidence = 0.7

# Relative View
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
confidence = 0.85

# Multiple Views + Per-View Confidence
views = {"P": [{"AAPL": 1}, {"MSFT": 1}], "Q": [0.10, 0.05]}
confidence = [0.9, 0.6]
```

## References

- Idzorek, T. (2005). "A Step-by-Step Guide to the Black-Litterman Model"
- PyPortfolioOpt: `omega="idzorek"` implementation

---

**Version**: 3.0 (English, Updated for v0.3.x)
**Last Updated**: 2025-11-25
