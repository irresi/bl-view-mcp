# Relative View Support - Implementation Summary

**Date**: 2025-11-22  
**Status**: ✅ Implemented and Tested  
**Issue**: [Feat: Relative view 지원](https://github.com/irresi/bl-view-mcp/issues/TBD)

## 📋 Overview

Implemented unified view interface for Black-Litterman model with dict-based P matrix support, enabling relative views while maintaining full backward compatibility.

## ✅ Implementation Complete

### 1. Core Functions (`bl_mcp/tools.py`)

#### `_parse_views(views, tickers) -> (P, Q)`
Converts all three view formats to P, Q matrices:

```python
# Format 1: Absolute views (backward compatible)
views = {"AAPL": 0.10, "MSFT": 0.05}
→ P = [[1, 0, 0], [0, 1, 0]], Q = [0.10, 0.05]

# Format 2: Dict-based P (NEW - relative views!)
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
→ P = [[1, -1, 0]], Q = [0.20]

# Format 3: NumPy P (advanced)
views = {"P": [[1, -1, 0]], "Q": [0.20]}
→ P = [[1, -1, 0]], Q = [0.20]
```

**Features**:
- ✅ Validates unknown tickers
- ✅ Validates P, Q dimensions match
- ✅ Handles missing P or Q with clear error messages
- ✅ Order-independent dict-based P (LLM-friendly)

#### `_normalize_confidence(confidence, views, tickers) -> list`
Unifies all confidence formats to list:

```python
None → [0.5, 0.5, ...]           # Default
0.7 → [0.7, 0.7, ...]             # Float
{"AAPL": 0.9} → [0.9]             # Dict (absolute views only)
[0.9, 0.8] → [0.9, 0.8]           # List (passthrough)
```

**Features**:
- ✅ Validates confidence length matches number of views
- ✅ Rejects dict confidence for P, Q views
- ✅ Percentage normalization (70 → 0.7)
- ✅ Per-view confidence validation

### 2. Updated `optimize_portfolio_bl()`

**Changes**:
- ✅ Uses `_parse_views()` instead of `validate_view_dict()`
- ✅ Uses `_normalize_confidence()` for all confidence types
- ✅ Always uses P, Q with `BlackLittermanModel` (no more `absolute_views`)
- ✅ Maintains parameter swap detection
- ✅ Backward compatible with existing code

**Updated Docstring**:
```python
views: Your investment views (optional). Supports three formats:
      
      1. Absolute views (dict):
         {"AAPL": 0.10, "MSFT": 0.05}
         - AAPL expected to return 10%, MSFT 5%
         
      2. Dict-based P matrix (relative views):
         {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
         - NVDA will outperform AAPL by 20%
         - Ticker names (order-independent, LLM-friendly)
         
      3. NumPy P matrix (advanced):
         {"P": [[1, -1, 0]], "Q": [0.20]}
         - Index-based (NVDA=0, AAPL=1, MSFT=2)

confidence: How confident you are in your views (0.0 to 1.0, default: 0.5).
           Can be:
           - Single float: Same confidence for all views
           - Dict: Per-ticker confidence (absolute views only)
           - List: Per-view confidence (P, Q views)
           - None: Defaults to 0.5 (neutral)
```

### 3. Comprehensive Tests

**File**: `tests/test_relative_views_simple.py`

**Test Coverage**:
- ✅ **Backward Compatibility**
  - Absolute views with single confidence
  - Absolute views with dict confidence
  - Default confidence (None)

- ✅ **Dict-based P Matrix**
  - Single relative view
  - Multiple relative views
  - Complex weights
  - Float confidence auto-conversion
  - Default confidence

- ✅ **NumPy P Matrix**
  - Single view
  - Multiple views
  - Absolute view (pick single asset)

- ✅ **Confidence Normalization**
  - None → list
  - Float → list
  - Dict → list (absolute views)
  - List passthrough
  - Percentage input

- ✅ **Validation Errors**
  - Unknown ticker in absolute views
  - Unknown ticker in dict-based P
  - Confidence length mismatch
  - Missing Q with P
  - P/Q dimension mismatch
  - NumPy P column count mismatch
  - Dict confidence with P, Q views
  - Missing confidence for ticker

- ✅ **Equivalence Testing**
  - Absolute view == dict-based P
  - Dict-based P == NumPy P

**Test Results**:
```bash
$ make test-relative
============================================================
🧪 RELATIVE VIEW SUPPORT TESTS
============================================================

✅ Testing absolute views (backward compatibility)...
  ✓ Single confidence works
  ✓ Dict confidence works

✅ Testing dict-based P matrix (relative views)...
  ✓ Single relative view works
  ✓ Multiple relative views work
  ✓ Float confidence auto-converts to list

✅ Testing NumPy P matrix...
  ✓ NumPy P matrix works

✅ Testing validation errors...
  ✓ Unknown ticker detected
  ✓ Confidence length mismatch detected
  ✓ Missing Q detected
  ✓ Dict confidence with P, Q rejected

✅ Testing equivalence...
  ✓ Absolute view == dict-based P
  ✓ Dict-based P == NumPy P

============================================================
✅ ALL TESTS PASSED!
============================================================
```

### 4. Makefile Integration

Added `test-relative` target:
```bash
make test-relative  # Run relative view tests
make help          # Shows test-relative in help menu
```

## 📊 Impact

### For Users
- Can now express relative views naturally
- Dict-based P is human-readable
- All existing code continues to work

### For LLMs
- Easy to generate dict-based P from natural language
- "NVDA will outperform AAPL by 20%" → `{"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}`
- Order-independent ticker names

### For Code
- Single unified interface (less complexity)
- Comprehensive validation
- Clear error messages

## 🔍 Key Design Decisions

1. **P, Q Everywhere**: Internally always use P, Q matrices (even for absolute views)
   - Simplifies BlackLittermanModel usage
   - Unifies code paths
   - Enables relative views naturally

2. **Confidence as List**: Normalize all confidence types to list internally
   - Consistent interface with PyPortfolioOpt
   - Easier validation
   - Clear per-view confidence

3. **Backward Compatible**: Old code must continue working
   - `{"AAPL": 0.10}` still works
   - Dict confidence still works for absolute views
   - Single float confidence still works

4. **Validation First**: Catch errors early with clear messages
   - Unknown tickers
   - Dimension mismatches
   - Missing P or Q
   - Confidence length errors

## 📝 Usage Examples

### Relative View: NVDA vs AAPL
```python
result = optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    period="1Y",
    views={
        "P": [{"NVDA": 1, "AAPL": -1}],
        "Q": [0.20]  # NVDA outperforms by 20%
    },
    confidence=[0.9]  # Very confident
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
# Use absolute for one asset, relative for comparison
views={
    "P": [
        {"NVDA": 1},                     # Absolute: NVDA 30%
        {"AAPL": 1, "MSFT": -1}         # Relative: AAPL vs MSFT
    ],
    "Q": [0.30, 0.05]
}
```

## 🎯 Acceptance Criteria (Completed)

- [x] Support dict-based P matrix format
- [x] Support NumPy P matrix format
- [x] Maintain backward compatibility with absolute views dict
- [x] Normalize confidence to list internally
- [x] Support float, dict, list, and None confidence inputs
- [x] Validate P matrix tickers exist in tickers list
- [x] Validate confidence length matches Q length
- [x] Validate Q is provided when P is provided
- [x] Add comprehensive tests (15+ test cases)
- [x] Update documentation with examples
- [x] No breaking changes to existing API

## 🚀 Next Steps

- [ ] 백테스팅 기능 추가
- [ ] 팩터 스코어링 Tool 추가
- [ ] HRP 가중치 Tool 추가

## 📚 References

- Implementation: `bl_mcp/tools.py` (_parse_views, _normalize_confidence, optimize_portfolio_bl)
- Tests: `tests/test_relative_views_simple.py`
- PyPortfolioOpt Docs: https://pyportfolioopt.readthedocs.io/en/latest/BlackLitterman.html
