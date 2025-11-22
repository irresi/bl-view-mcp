# Feature Request: Unified View Interface with Dict-based P Matrix Support

## 💡 Problem Statement

**Current Limitation**: Only absolute views are supported through dict syntax
**Missing Feature**: Relative views (e.g., "NVDA will outperform AAPL by 20%") are not possible

**Root Cause**: We artificially separate absolute and relative views, but they're mathematically identical (both are P, Q matrices under the hood).

## 🎯 Proposed Solution

### Unified API with Dict-based P Matrix

Support P, Q matrices with ticker-based dict syntax while maintaining backward compatibility:

```python
# Method 1: Absolute views (current - keep as-is)
optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    views={"AAPL": 0.10, "MSFT": 0.05},
    confidence=0.7  # Single float, dict, or list
)

# Method 2: Dict-based P (NEW - relative views!)
optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    views={
        "P": [
            {"NVDA": 1, "AAPL": -1},    # NVDA - AAPL
            {"NVDA": 1, "MSFT": -1}     # NVDA - MSFT
        ],
        "Q": [0.20, 0.15]
    },
    confidence=[0.9, 0.8]
)

# Method 3: NumPy P (for advanced users)
optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    views={
        "P": [[1, -1, 0], [1, 0, -1]],
        "Q": [0.20, 0.15]
    },
    confidence=[0.9, 0.8]
)
```

## 🔑 Key Features

### 1. Dict-based P Matrix
- **Ticker names instead of indices**: `{"NVDA": 1, "AAPL": -1}` instead of `[1, -1, 0]`
- **Order-independent**: No need to know ticker positions
- **LLM-friendly**: Can generate from natural language
- **Human-readable**: Self-documenting code

### 2. Unified Confidence Handling

**Backward Compatible**:
```python
# All existing formats still work
confidence = 0.7                          # Float → [0.7, 0.7, ...]
confidence = {"AAPL": 0.9, "MSFT": 0.6}  # Dict → [0.9, 0.6]
confidence = [0.9, 0.6]                   # List (recommended)
```

**Internal Normalization**:
- Always convert to list internally
- Length must match number of views (Q length)
- Default value: 0.5 if not provided

### 3. Comprehensive Validation

```python
# ✅ Valid cases
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
confidence = [0.8]  # Length matches Q

# ❌ Invalid cases with clear error messages
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
confidence = [0.8, 0.7]  # Error: Length mismatch

views = {"P": [{"UNKNOWN": 1, "AAPL": -1}], "Q": [0.20]}
# Error: Ticker 'UNKNOWN' not in tickers list

views = {"P": [{"NVDA": 1}]}  # Error: Q is required when P is provided
```

## 💻 Implementation Plan

### 1. Parse Views Function

```python
def _parse_views(views: dict, tickers: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert various view formats to P, Q matrices.
    
    Supports:
    1. Dict (absolute): {"AAPL": 0.10, "MSFT": 0.05}
    2. Dict-based P: {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
    3. NumPy P: {"P": [[1, -1, 0]], "Q": [0.20]}
    """
    if "P" in views and "Q" in views:
        P_input = views["P"]
        Q = np.array(views["Q"])
        
        if isinstance(P_input[0], dict):
            # Dict-based P: convert to NumPy
            P = np.zeros((len(P_input), len(tickers)))
            for i, view_dict in enumerate(P_input):
                for ticker, weight in view_dict.items():
                    if ticker not in tickers:
                        raise ValueError(f"Ticker '{ticker}' not in tickers list")
                    j = tickers.index(ticker)
                    P[i, j] = weight
        else:
            # NumPy P: use directly
            P = np.array(P_input)
            
        return P, Q
    
    else:
        # Absolute views dict: convert to P, Q
        P = np.zeros((len(views), len(tickers)))
        Q = np.zeros(len(views))
        
        for i, (ticker, expected_return) in enumerate(views.items()):
            if ticker not in tickers:
                raise ValueError(f"Ticker '{ticker}' not in tickers list")
            j = tickers.index(ticker)
            P[i, j] = 1
            Q[i] = expected_return
        
        return P, Q
```

### 2. Normalize Confidence Function

```python
def _normalize_confidence(
    confidence: float | dict | list | None,
    views: dict,
    tickers: list[str]
) -> list[float]:
    """
    Normalize confidence to list format.
    
    Handles:
    - None → [0.5, 0.5, ...]
    - Float → [value, value, ...]
    - Dict → [dict[ticker1], dict[ticker2], ...]
    - List → validate and return
    """
    # Determine number of views
    if "P" in views and "Q" in views:
        num_views = len(views["Q"])
    else:
        num_views = len(views)
    
    # Normalize to list
    if confidence is None:
        return [0.5] * num_views
    
    elif isinstance(confidence, (int, float)):
        return [float(confidence)] * num_views
    
    elif isinstance(confidence, dict):
        # Dict confidence only valid for absolute views
        if "P" in views:
            raise ValueError(
                "Dict confidence not supported for P, Q views. Use list instead."
            )
        return [confidence[ticker] for ticker in views.keys()]
    
    elif isinstance(confidence, list):
        if len(confidence) != num_views:
            raise ValueError(
                f"Confidence length ({len(confidence)}) must match "
                f"number of views ({num_views})"
            )
        return confidence
    
    else:
        raise TypeError(f"Invalid confidence type: {type(confidence)}")
```

### 3. Updated optimize_portfolio_bl

```python
def optimize_portfolio_bl(
    tickers: list[str],
    views: dict | None = None,
    confidence: float | dict | list | None = None,
    ...
) -> dict:
    """
    Optimize portfolio using Black-Litterman model.
    
    Args:
        tickers: List of ticker symbols
        views: Views in one of three formats:
            1. Dict (absolute): {"AAPL": 0.10, "MSFT": 0.05}
            2. Dict-based P: {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
            3. NumPy P: {"P": [[1, -1, 0]], "Q": [0.20]}
        confidence: Confidence in views:
            - Float: Same confidence for all views
            - Dict: Per-ticker confidence (absolute views only)
            - List: Per-view confidence (recommended)
            - None: Defaults to 0.5
    
    Examples:
        # Absolute views
        >>> optimize_portfolio_bl(
        ...     tickers=["AAPL", "MSFT"],
        ...     views={"AAPL": 0.10},
        ...     confidence=0.7
        ... )
        
        # Relative views
        >>> optimize_portfolio_bl(
        ...     tickers=["NVDA", "AAPL", "MSFT"],
        ...     views={
        ...         "P": [{"NVDA": 1, "AAPL": -1}],
        ...         "Q": [0.20]
        ...     },
        ...     confidence=[0.9]
        ... )
    """
    # Validate and parse views
    if views:
        P, Q = _parse_views(views, tickers)
        conf_list = _normalize_confidence(confidence, views, tickers)
        
        # Use BlackLittermanModel with P, Q
        bl = BlackLittermanModel(
            S,
            pi=market_prior,
            P=P,
            Q=Q,
            omega="idzorek",
            view_confidences=conf_list
        )
        ...
```

## ✅ Benefits

1. **Unified Interface**: One API for all view types
2. **LLM-Friendly**: Dict-based P is easy to generate from natural language
3. **Backward Compatible**: All existing code continues to work
4. **Flexible**: Supports absolute, relative, and custom views
5. **Type-Safe**: Comprehensive validation with clear error messages
6. **Self-Documenting**: Ticker names make code readable

## 🧪 Testing Strategy

### Test Cases

```python
def test_absolute_views_dict():
    """Test existing dict format still works."""
    result = optimize_portfolio_bl(
        tickers=["AAPL", "MSFT"],
        views={"AAPL": 0.10},
        confidence=0.7
    )
    assert result["success"]

def test_dict_based_p_relative():
    """Test new dict-based P format for relative views."""
    result = optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        views={
            "P": [{"NVDA": 1, "AAPL": -1}],
            "Q": [0.20]
        },
        confidence=[0.9]
    )
    assert result["success"]

def test_numpy_p():
    """Test NumPy array P format."""
    result = optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        views={
            "P": [[1, -1, 0]],
            "Q": [0.20]
        },
        confidence=[0.9]
    )
    assert result["success"]

def test_confidence_normalization():
    """Test all confidence formats."""
    views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
    
    # Float
    result = optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        views=views,
        confidence=0.8
    )
    assert result["success"]
    
    # List
    result = optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        views=views,
        confidence=[0.8]
    )
    assert result["success"]
    
    # None (default)
    result = optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        views=views,
        confidence=None
    )
    assert result["success"]

def test_validation_errors():
    """Test validation catches errors."""
    
    # Unknown ticker
    with pytest.raises(ValueError, match="not in tickers list"):
        optimize_portfolio_bl(
            tickers=["AAPL", "MSFT"],
            views={"P": [{"UNKNOWN": 1}], "Q": [0.20]},
            confidence=[0.8]
        )
    
    # Confidence length mismatch
    with pytest.raises(ValueError, match="must match number of views"):
        optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            views={"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]},
            confidence=[0.8, 0.9]  # 2 values for 1 view
        )
    
    # Missing Q
    with pytest.raises(ValueError, match="Q is required"):
        optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            views={"P": [{"NVDA": 1, "AAPL": -1}]},
            confidence=[0.8]
        )

def test_backward_compatibility():
    """Ensure existing code still works."""
    
    # Dict confidence with absolute views
    result = optimize_portfolio_bl(
        tickers=["AAPL", "MSFT"],
        views={"AAPL": 0.10, "MSFT": 0.05},
        confidence={"AAPL": 0.9, "MSFT": 0.6}
    )
    assert result["success"]
```

## 📚 Documentation Updates

### 1. README Examples

Add relative view examples:

```markdown
### Relative Views

Express views as comparisons between assets:

```python
# "NVDA will outperform AAPL by 20% annually"
result = optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    views={
        "P": [{"NVDA": 1, "AAPL": -1}],
        "Q": [0.20]
    },
    confidence=[0.9]
)
```

### 2. Update Tool Docstrings

Add examples for all three formats in MCP tool description.

### 3. Add Migration Guide

For users who want to use the new format.

## 🎯 Acceptance Criteria

- [ ] Support dict-based P matrix format
- [ ] Support NumPy P matrix format (already works with PyPortfolioOpt)
- [ ] Maintain backward compatibility with absolute views dict
- [ ] Normalize confidence to list internally
- [ ] Support float, dict, list, and None confidence inputs
- [ ] Validate P matrix tickers exist in tickers list
- [ ] Validate confidence length matches Q length
- [ ] Validate Q is provided when P is provided
- [ ] Add comprehensive tests (10+ test cases)
- [ ] Update documentation with examples
- [ ] Update agent prompt with relative view examples
- [ ] No breaking changes to existing API

## 🏷️ Labels

- `enhancement`
- `api-design`
- `backward-compatible`
- `high-priority`

## 📊 Impact

**Users**: Can now express relative views naturally
**LLMs**: Can generate dict-based P from natural language
**Code**: More flexible and powerful API
**Maintenance**: Single unified interface (less complexity)

## 🚀 Implementation Timeline

**Phase 1 (Core)**:
- [ ] Implement `_parse_views()` function
- [ ] Implement `_normalize_confidence()` function
- [ ] Update `optimize_portfolio_bl()` to use new functions
- [ ] Add basic validation

**Phase 2 (Testing)**:
- [ ] Write unit tests for all formats
- [ ] Write validation error tests
- [ ] Write backward compatibility tests
- [ ] Manual testing with real data

**Phase 3 (Documentation)**:
- [ ] Update README with examples
- [ ] Update tool docstrings
- [ ] Update agent prompt
- [ ] Add migration guide

**Phase 4 (Polish)**:
- [ ] Code review
- [ ] Performance testing
- [ ] Final validation

## 💭 Open Questions

None - design is finalized and ready for implementation.

## 📎 References

- PyPortfolioOpt BlackLittermanModel: https://pyportfolioopt.readthedocs.io/en/latest/BlackLitterman.html
- Idzorek Paper: `reference/Idzorek_onBL.pdf`
- Current Implementation: `bl_mcp/tools.py:optimize_portfolio_bl`
- Verification Report: `docs/IDZOREK_VERIFICATION.md`
