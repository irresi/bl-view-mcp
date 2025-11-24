# Confidence Scale Guide

## Overview

In the Black-Litterman model, confidence determines **how much your views influence the portfolio**.

### Confidence Scale (0.5 = Neutral Pivot)

```
100% ■■■■■■■■■■ Absolute Certainty
 95% ■■■■■■■■■□ Very Confident ← Almost certain
 85% ■■■■■■■■□□ Confident ← High reliability
 75% ■■■■■■■□□□ Quite Confident
 60% ■■■■■■□□□□ Somewhat Confident
────────────────────────────────────────────
 50% ■■■■■□□□□□ Neutral ← Pivot Point (Default)
────────────────────────────────────────────
 40% ■■■■□□□□□□ Somewhat Uncertain
 30% ■■■□□□□□□□ Uncertain
 10% ■□□□□□□□□□ Very Uncertain ← Almost meaningless
  0% □□□□□□□□□□ No Information
```

### Key Points

1. **50% is Neutral**
   - You have a view but no strong conviction
   - Minimal impact on portfolio
   - Default value when not specified

2. **60%+ : Strong Views**
   - Views actually influence the portfolio
   - 60%: Slight influence
   - 75%: Moderate influence
   - 85%: Strong influence
   - 95%+: Very strong influence

3. **40% and below: Weak Views**
   - Views are mostly ignored
   - Information is uncertain or unreliable
   - 30% or below is practically meaningless

## Natural Language → Number Conversion

| Expression | Confidence | Description |
|------------|------------|-------------|
| Absolute certainty, Definitely | 100% (1.0) | Completely certain |
| Very confident, Certain | 95% (0.95) | Almost certain |
| Confident, Sure | 85% (0.85) | High confidence |
| Quite confident, Fairly sure | 75% (0.75) | Moderately high |
| Somewhat confident, Slightly sure | 60% (0.6) | Slightly above neutral |
| Neutral, Don't know, 50-50 | 50% (0.5) | **Neutral (Default)** |
| Somewhat uncertain, Not very sure | 40% (0.4) | Slightly below neutral |
| Uncertain, Not sure | 30% (0.3) | Low confidence |
| Very uncertain, No confidence | 10% (0.1) | Almost meaningless |

## Input Formats (All Supported)

### 1. Percentage (0-100)

```python
confidence=95   # 95%
confidence=85   # 85%
confidence=50   # 50% (neutral)
```

### 2. Decimal (0.0-1.0)

```python
confidence=0.95  # 95%
confidence=0.85  # 85%
confidence=0.5   # 50% (neutral)
```

### 3. Per-View Confidence (List)

```python
# Different confidence for each view
confidence=[0.9, 0.6]  # First view: 90%, Second view: 60%
```

**All formats work identically!**
- `70` = `0.7` → Both treated as 70%
- `95` = `0.95` → Both treated as 95%

## Usage Examples

### Example 1: Strong View

```python
# "I'm very confident AAPL will return 30%"
optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    views={"P": [{"AAPL": 1}], "Q": [0.30]},
    confidence=0.95  # "Very confident" → 95%
)
# Result: AAPL weight significantly increases
```

### Example 2: Relative View

```python
# "I'm quite confident NVDA will outperform AAPL by 20%"
optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    views={"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]},
    confidence=0.75  # "Quite confident" → 75%
)
# Result: NVDA weight increases, AAPL weight decreases
```

### Example 3: Neutral View

```python
# "I think MSFT might return 10%, but I'm not sure"
optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    views={"P": [{"MSFT": 1}], "Q": [0.10]},
    confidence=0.5  # "Not sure" → 50% (neutral)
)
# Result: View has minimal impact
```

## Best Practices

### DO ✅

- Use percentage or decimal: `70`, `0.7`
- Use list for per-view confidence: `[0.9, 0.6]`
- Understand 50% as neutral state
- Higher confidence = stronger view influence

### DON'T ❌

- Use ambiguous values (1-5): `confidence=2`
- Exceed 100%: `confidence=150`
- Use negative values: `confidence=-10`

## Technical Background

### Omega Matrix

Confidence is used to calculate the **Omega matrix** (view uncertainty) in Black-Litterman:

- **High confidence (85-95%)**: Small Omega → View strongly reflected
- **Neutral confidence (50%)**: Medium Omega → View weakly reflected
- **Low confidence (10-30%)**: Large Omega → View mostly ignored

### Idzorek Method

This project uses the Idzorek (2005) method to convert confidence to Omega:
- Intuitive confidence input (0-100%)
- Automatic optimal Omega calculation
- `omega="idzorek"` in BlackLittermanModel

---

**Version**: 3.0 (English, Updated for v0.3.x)
**Last Updated**: 2025-11-25
