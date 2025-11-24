# Relative View Support

## Overview

Unified view interface for Black-Litterman model with dict-based P matrix support, enabling relative views while maintaining full backward compatibility.

**Status**: ✅ Implemented and Tested

## View Formats

### 1. Dict-based P Matrix (Recommended)

```python
# Relative View: NVDA will outperform AAPL by 20%
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
→ P = [[1, -1, 0]], Q = [0.20]

# Absolute View: AAPL expected to return 10%
views = {"P": [{"AAPL": 1}], "Q": [0.10]}
→ P = [[1, 0, 0]], Q = [0.10]
```

**Features**:
- ✅ Order-independent ticker names (LLM-friendly)
- ✅ Validates unknown tickers
- ✅ Validates P, Q dimensions match

### 2. NumPy P Matrix (Advanced)

```python
# Index-based: NVDA=0, AAPL=1, MSFT=2
views = {"P": [[1, -1, 0]], "Q": [0.20]}
→ P = [[1, -1, 0]], Q = [0.20]
```

## Core Functions

### `_parse_views(views, tickers) -> (P, Q)`

Converts view formats to P, Q matrices.

### `_normalize_confidence(confidence, views, tickers) -> list`

Unifies all confidence formats to list:

```python
None → [0.5, 0.5, ...]           # Default
0.7 → [0.7, 0.7, ...]            # Float (same for all views)
[0.9, 0.8] → [0.9, 0.8]          # List (per-view confidence)
```

## Usage Examples

### Relative View: NVDA vs AAPL

```python
result = optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    period="1Y",
    views={
        "P": [{"NVDA": 1, "AAPL": -1}],
        "Q": [0.20]  # NVDA outperforms by 20%
    },
    confidence=0.9
)
```

### Multiple Relative Views

```python
result = optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    period="1Y",
    views={
        "P": [
            {"NVDA": 1, "AAPL": -1},     # NVDA vs AAPL
            {"NVDA": 1, "MSFT": -1},     # NVDA vs MSFT
            {"AAPL": 1, "MSFT": -1}      # AAPL vs MSFT
        ],
        "Q": [0.20, 0.15, 0.05]
    },
    confidence=[0.9, 0.8, 0.7]
)
```

### Mixed: Absolute + Relative

```python
views = {
    "P": [
        {"NVDA": 1},                     # Absolute: NVDA 30%
        {"AAPL": 1, "MSFT": -1}          # Relative: AAPL vs MSFT
    ],
    "Q": [0.30, 0.05]
}
```

## Validation Errors

The implementation catches these errors:
- Unknown ticker in dict-based P
- Confidence length mismatch
- Missing Q with P
- P/Q dimension mismatch
- NumPy P column count mismatch

## Design Decisions

1. **P, Q Everywhere**: Internally always use P, Q matrices
   - Simplifies BlackLittermanModel usage
   - Unifies code paths

2. **Confidence as List**: Normalize all confidence types to list internally
   - Consistent interface with PyPortfolioOpt
   - Clear per-view confidence

3. **Validation First**: Catch errors early with clear messages

## Impact

### For Users
- Express relative views naturally
- Dict-based P is human-readable
- All existing code continues to work

### For LLMs
- Easy to generate dict-based P from natural language
- "NVDA will outperform AAPL by 20%" → `{"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}`
- Order-independent ticker names

---

**Version**: 3.0 (Updated for v0.3.x)
**Last Updated**: 2025-11-25
