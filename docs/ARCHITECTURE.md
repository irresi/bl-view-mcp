# Architecture

Black-Litterman MCP Server의 기술 아키텍처 문서입니다.

## 핵심 철학

**Prior (시장 균형) + Views (AI 견해) = Posterior (최적 포트폴리오)**

Black-Litterman 모델은 베이지안 통계를 기반으로:
- **Prior**: 시가총액 가중 포트폴리오 (시장의 균형 상태)
- **Likelihood**: 투자자 견해 (AI가 입력하는 기대수익률)
- **Posterior**: 최적 포트폴리오 비중

---

## MCP 도구 구조

```
server.py (@mcp.tool)
    ├── optimize_portfolio_bl()
    │       └── tools.py (business logic)
    │               ├── _parse_views()
    │               ├── _normalize_confidence()
    │               └── BlackLittermanModel(omega="idzorek")
    ├── backtest_portfolio()
    │       └── tools.py
    │               ├── _simulate_portfolio()
    │               ├── _calculate_returns_metrics()
    │               └── _calculate_benchmark_metrics()
    ├── upload_price_data()
    │       └── data_loader.save_custom_price_data()
    ├── upload_price_data_from_file()
    │       └── data_loader.load_and_save_from_file()
    └── list_available_tickers()
            └── data_loader.list_tickers()
```

### 설계 원칙

**Single Tool 설계**: LLM이 불필요하게 중간 단계를 호출하지 않도록 최소한의 Tool로 구성

이전에 분리되어 있던 도구들:
- ~~calculate_expected_returns~~
- ~~calculate_covariance_matrix~~
- ~~create_investor_view~~

→ 모두 `optimize_portfolio_bl` 하나로 통합 (토큰 효율성 향상)

---

## 전송 방식 (Transport Modes)

### stdio 모드

- **용도**: Claude Desktop, Windsurf, Cline 등 MCP 지원 IDE
- **장점**: 간편한 설정, 빠른 개발/테스트

```
Tools → FastMCP Server (stdio) → Windsurf/Claude Desktop
```

### HTTP 모드

- **용도**: Google ADK Agent, 웹 서비스 통합
- **장점**: 네트워크 접근, 멀티 클라이언트, 디버깅 용이

```
Tools → FastMCP Server (HTTP) → ADK Agent (Gemini)
```

---

## 파라미터 상세

### optimize_portfolio_bl

```python
optimize_portfolio_bl(
    tickers: list[str],           # ["AAPL", "MSFT", "GOOGL"]
    period: str = "1Y",           # "1Y", "6M", "3M" (권장)
    start_date: str = None,       # "2023-01-01" (period와 택1)
    views: dict = None,           # P, Q 형식만 지원
    confidence: float | list = None,  # 0.0-1.0 또는 리스트
    investment_style: str = "balanced",  # aggressive/balanced/conservative
    risk_aversion: float = None   # 고급 사용자용 (사용 비권장)
)
```

#### Views Format (P, Q Only)

```python
# Absolute view: "AAPL will return 10%"
views = {"P": [{"AAPL": 1}], "Q": [0.10]}

# Relative view: "NVDA will outperform AAPL by 20%"
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}

# Multiple views
views = {
    "P": [{"NVDA": 1, "AAPL": -1}, {"GOOGL": 1}],
    "Q": [0.25, 0.12]
}
confidence = [0.9, 0.6]  # 뷰별 confidence

# NumPy format (CSV/엑셀 데이터용)
views = {"P": [[1, -1, 0]], "Q": [0.20]}
```

#### Confidence Format

```python
confidence = 0.7        # 모든 뷰에 동일
confidence = [0.9, 0.8] # 뷰별 다르게
confidence = None       # 기본값 0.5
```

### backtest_portfolio

```python
backtest_portfolio(
    tickers: list[str],           # ["AAPL", "MSFT", "GOOGL"]
    weights: dict[str, float],    # {"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25}
    period: str = "1Y",           # "1Y", "3Y", "5Y" (권장)
    start_date: str = None,       # "2020-01-01" (period와 택1)
    strategy: str = "passive_rebalance",
    benchmark: str = "SPY",
    initial_capital: float = 10000.0,
    custom_config: dict = None
)
```

#### Strategy Presets

| Strategy | 설명 | 리밸런싱 | Stop-Loss | MDD Limit |
|----------|------|---------|-----------|-----------|
| `buy_and_hold` | 매입 후 보유 | 없음 | 없음 | 없음 |
| `passive_rebalance` | 패시브 투자 (DEFAULT) | 월별 | 없음 | 없음 |
| `risk_managed` | 리스크 관리 | 월별 | 10% | 20% |

#### Custom Config Options

```python
custom_config = {
    "rebalance_frequency": "quarterly",  # none/weekly/monthly/quarterly/semi-annual/annual
    "fees": 0.002,           # 수수료 (0.2%)
    "slippage": 0.001,       # 슬리피지 (0.1%)
    "stop_loss": 0.10,       # 손절매 (10%)
    "take_profit": 0.30,     # 익절매 (30%)
    "trailing_stop": True,   # 트레일링 스탑
    "max_drawdown_limit": 0.20  # MDD 한도 (20%)
}
```

---

## 출력 형식

### optimize_portfolio_bl 출력

```json
{
  "weights": {"AAPL": 0.33, "MSFT": 0.33, "GOOGL": 0.33},
  "expected_return": 0.12,
  "volatility": 0.23,
  "sharpe_ratio": 0.52,
  "posterior_returns": {"AAPL": 0.15, "MSFT": 0.12, "GOOGL": 0.11},
  "prior_returns": {"AAPL": 0.14, "MSFT": 0.13, "GOOGL": 0.12},
  "risk_aversion": 2.5,
  "has_views": true,
  "period": {"start": "2024-01-01", "end": "2025-01-01", "days": 252}
}
```

### backtest_portfolio 출력

```json
{
  "total_return": 0.25,
  "cagr": 0.12,
  "volatility": 0.18,
  "sharpe_ratio": 0.67,
  "sortino_ratio": 0.85,
  "max_drawdown": -0.15,
  "calmar_ratio": 0.80,
  "initial_capital": 10000.0,
  "final_value": 12500.0,
  "total_fees_paid": 45.0,
  "num_rebalances": 12,
  "turnover": 0.85,
  "benchmark_return": 0.20,
  "excess_return": 0.05,
  "alpha": 0.03,
  "beta": 0.95,
  "information_ratio": 0.35,
  "holding_periods": {
    "AAPL": {"days": 730, "is_long_term": true}
  }
}
```

---

## 내부 동작

### Ticker Order Preserved

사용자 입력 순서 유지 (정렬 안 함)
- NumPy P format에서 인덱스 정합성 보장
- `load_prices()`가 입력 순서대로 DataFrame 컬럼 생성

### Risk Aversion Calculation

1. SPY 데이터로 `market_implied_risk_aversion()` 자동 계산
2. `investment_style` 배수 적용:
   - aggressive: δ × 0.5
   - balanced: δ × 1.0
   - conservative: δ × 2.0
3. SPY 없으면 fallback 2.5

### Market Caps (자동 로드)

```python
# data_loader.py
get_market_caps(tickers)
# 1. Parquet 캐시 확인 (data/market_caps.parquet)
# 2. 없으면 yfinance에서 다운로드
# 3. 성공 시 Parquet에 캐싱
# 4. 실패 시 equal weight fallback
```

### Prior Calculation

`market_implied_prior_returns(mcaps, δ, Σ)` → π = δΣw_mkt

---

## 프로젝트 구조

```
bl_mcp/                     # MCP 서버 패키지
├── server.py               # FastMCP 서버 (@mcp.tool)
├── tools.py                # 핵심 로직
└── utils/
    ├── data_loader.py      # Parquet → DataFrame
    ├── validators.py       # 입력 검증
    └── session.py          # HTTP 세션

bl_agent/                   # ADK Agent 패키지
├── agent.py                # Google ADK Agent
└── prompt.py               # Agent 프롬프트

scripts/                    # 데이터 다운로드 스크립트
├── download_data.py
├── download_sp500.py
└── ...

tests/
├── test_simple.py          # 기본 테스트
└── ...

data/                       # Parquet 데이터
├── *.parquet               # 개별 종목
├── market_caps.parquet     # 시가총액 캐시
└── custom_tickers.json     # 커스텀 티커 목록
```

---

## 기술 스택

### 데이터

- **주식/ETF**: yfinance
- **암호화폐**: ccxt
- **캐싱**: Parquet

### 모델

- **Black-Litterman**: PyPortfolioOpt.black_litterman
- **기대수익률**: PyPortfolioOpt.expected_returns
- **공분산**: PyPortfolioOpt.risk_models

### MCP 프레임워크

- **서버**: FastMCP 2.13.0.1
- **Agent**: Google ADK 1.14.1 (선택)

---

## 관련 문서

- [CONFIDENCE_SCALE.md](CONFIDENCE_SCALE.md) - Confidence 스케일 설명
- [IDZOREK_VERIFICATION.md](IDZOREK_VERIFICATION.md) - Idzorek 방법 검증
- [RELATIVE_VIEWS_IMPLEMENTATION.md](RELATIVE_VIEWS_IMPLEMENTATION.md) - 상대 견해 구현
