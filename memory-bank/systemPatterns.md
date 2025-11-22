# System Patterns

## 현재 아키텍처 (2025-11-23)

```
┌─────────────────┐
│   AI Client     │  (Claude, Windsurf, ADK)
└────────┬────────┘
         │ MCP Protocol
┌────────▼────────┐
│  server.py      │  @mcp.tool (1개만)
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
│ data/*.parquet  │  503개 종목
└─────────────────┘
```

---

## 핵심 설계 결정

### 1. Single Tool 설계

**이유**: LLM이 불필요하게 중간 단계 호출 방지

```python
# 이전: 4개 Tool 체이닝 필요
returns = calculate_expected_returns(...)
cov = calculate_covariance_matrix(...)
view = create_investor_view(...)
portfolio = optimize_portfolio_bl(returns, cov, view)

# 현재: 1개 Tool로 완료
portfolio = optimize_portfolio_bl(tickers, views, confidence)
```

### 2. P, Q 형식만 지원

**이유**: LLM 혼동 방지, API 일관성

```python
# ❌ 제거됨
views = {"AAPL": 0.10}

# ✅ 유일한 형식
views = {"P": [{"AAPL": 1}], "Q": [0.10]}           # Absolute
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}  # Relative
views = {"P": [[1, -1, 0]], "Q": [0.20]}            # NumPy
```

### 3. Ticker 순서 유지

**이유**: NumPy P format 인덱스 정합성

```python
# 사용자 입력 순서 그대로 유지
tickers = ["NVDA", "AAPL", "MSFT"]  # 정렬 안 함
```

---

## 주요 패턴

### Views 파싱

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

### Confidence 정규화

```python
def _normalize_confidence(confidence, views, tickers):
    num_views = len(views["Q"])

    if confidence is None:
        return [0.5] * num_views      # 기본값
    elif isinstance(confidence, (int, float)):
        return [confidence] * num_views  # 모든 뷰에 동일
    elif isinstance(confidence, list):
        return confidence              # 뷰별 다르게
```

### Risk Aversion 계산

```python
# SPY로 market-implied δ 계산
base_delta = market_implied_risk_aversion(spy_prices)

# investment_style 배수 적용
multipliers = {
    "aggressive": 0.5,
    "balanced": 1.0,
    "conservative": 2.0
}
risk_aversion = base_delta * multipliers[style]
```

---

## 에러 처리

```python
# 이전 형식 사용 시 명확한 에러
if "P" not in views or "Q" not in views:
    raise ValueError(
        "Views must use P, Q format. "
        "Example: {'P': [{'AAPL': 1}], 'Q': [0.10]}"
    )
```

---

## 테스트 패턴

```python
# 6개 핵심 시나리오
def test_optimize_basic()              # No views
def test_optimize_with_absolute_view() # P, Q absolute
def test_optimize_with_relative_view() # P, Q relative
def test_optimize_with_numpy_p()       # NumPy format
def test_investment_styles()           # aggressive/balanced/conservative
def test_multiple_views()              # Per-view confidence
```

---

## 참고

상세 컨텍스트: `CLAUDE.md` (Claude Code 자동 로드)
