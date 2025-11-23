# Black-Litterman MCP Server

## Project Summary

AI 에이전트(Claude, Windsurf, Google ADK)를 위한 Black-Litterman 포트폴리오 최적화 MCP 서버.

**핵심 철학**: Prior (시장 균형) + Views (AI 견해) = Posterior (최적 포트폴리오)

## Development Environment

### Prerequisites

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (패키지 매니저)

### Setup

```bash
# 1. uv 설치 (없을 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 의존성 설치
make install          # 기본 + agent extras
# 또는
uv sync               # 기본만
uv sync --extra agent # agent extras 포함

# 3. 데이터 다운로드 (중요: 서버 시작 전에 실행!)
make download-data      # S&P 500 (~500 종목, GitHub Release)
make download-nasdaq100 # NASDAQ 100 (~100 종목)
make download-etf       # ETF (~130 종목)
make download-crypto    # Crypto (100 심볼, --extra crypto 필요)

# 4. 테스트 실행
make test-simple
```

> ⚠️ **stdio 모드 주의**: 데이터 없이 서버 시작하면 자동 다운로드가 30초+ 걸릴 수 있음.
> LLM이 타임아웃으로 연결을 끊을 수 있으므로 **반드시 사전 다운로드 권장**.

### Optional Dependencies

```toml
[project.optional-dependencies]
agent = ["google-adk", "google-genai"]  # ADK Web UI용
dev = ["pytest", "mypy", "ruff"]        # 개발용
```

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make install` | 전체 의존성 설치 (`uv sync --extra agent`) |
| `make sync` | 기본 의존성만 (`uv sync`) |
| `make test-simple` | 기본 테스트 실행 |
| `make server-stdio` | Windsurf/Claude용 서버 |
| `make server-http` | Google ADK용 HTTP 서버 (port 5000) |
| `make web-ui` | ADK Web UI (port 8000) |
| `make quickstart` | install + sample + test 한번에 |
| `make check` | 환경 상태 확인 |

## Current Architecture (2025-11-23)

### Single Tool Design

**MCP Tool**: `optimize_portfolio_bl` 하나만 노출

```
server.py (@mcp.tool)
    └── tools.py (business logic)
            ├── _parse_views()      # P, Q 파싱
            ├── _normalize_confidence()  # float/list 정규화
            └── BlackLittermanModel(omega="idzorek")
```

**이전 구조에서 삭제됨**:
- ~~calculate_expected_returns~~
- ~~calculate_covariance_matrix~~
- ~~create_investor_view~~

**이유**: LLM이 불필요하게 중간 단계를 호출하는 것 방지, 토큰 효율성 향상

### Key Parameters

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

**삭제됨**: `market_caps` 파라미터 → 자동 로드

### Views Format (P, Q Only)

```python
# Absolute view: "AAPL will return 10%"
views = {"P": [{"AAPL": 1}], "Q": [0.10]}

# Relative view: "NVDA will outperform AAPL by 20%"
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}

# NumPy format (CSV/엑셀 데이터용)
views = {"P": [[1, -1, 0]], "Q": [0.20]}
```

**Breaking Change**: 이전 dict 형식 (`{"AAPL": 0.10}`) 더 이상 지원 안 함

### Confidence Format

```python
confidence = 0.7        # 모든 뷰에 동일
confidence = [0.9, 0.8] # 뷰별 다르게
confidence = None       # 기본값 0.5
```

**삭제됨**: dict 형식 (`{"AAPL": 0.9}`) 더 이상 지원 안 함

## Design Decisions

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

- 시가총액 자동 로드 (yfinance)
- 실패 시 equal weight fallback

## File Structure

```
bl_mcp/
├── server.py      # MCP interface (1 tool)
├── tools.py       # Business logic
└── utils/
    ├── data_loader.py   # Parquet 로드, 자동 다운로드
    ├── validators.py    # 입력 검증, period 파싱
    └── session.py       # HTTP 세션

tests/
├── test_simple.py       # 기본 테스트 (6개 시나리오)
└── ...

memory-bank/             # 상세 문서 (히스토리)
```

## Quick Commands

```bash
make test-simple    # 테스트 실행
make server-stdio   # Windsurf/Claude용
make server-http    # Google ADK용
```

## Google ADK 사용법

Google ADK Web UI를 통해 MCP 서버를 테스트하려면:

```bash
# 1. HTTP 서버 실행 (터미널 1)
make server-http    # localhost:5000에서 MCP 서버 시작

# 2. ADK Web UI 실행 (터미널 2)
make web-ui         # localhost:8000에서 ADK Web UI 시작
```

브라우저에서 `http://localhost:8000` 접속하면 ADK Web UI에서 MCP 도구를 테스트할 수 있습니다.

**참고**: ADK 관련 의존성이 필요합니다 (`make install` 또는 `uv sync --extra agent`)

## Recent Changes (2025-11-23)

1. **시가총액 자동 로드**: `market_caps` 파라미터 제거, yfinance에서 자동 다운로드
2. **Parquet 캐싱**: 한 번 가져온 시가총액은 `data/market_caps.parquet`에 저장
3. **Ticker 정렬 제거**: 사용자 입력 순서 유지
4. **Type hint 수정**: `confidence: float | list` (dict 제거)

## Known Issues

- SPY.parquet 없으면 `investment_style` 효과 없음 (fallback 2.5 사용)

## Phase 2 계획 (2025-11-23 결정)

### 프로젝트 분리 결정

**bl-mcp (이 프로젝트)**: MCP Tool만 제공 (순수 라이브러리)
**bl-orchestrator (별도 프로젝트)**: Multi-agent view generation (CrewAI)

### Phase 2 범위 (축소됨)

| Tool | 상태 | 설명 |
|------|------|------|
| `optimize_portfolio_bl` | ✅ 기존 | BL 최적화 |
| `backtest_portfolio` | 🆕 신규 | 포트폴리오 백테스팅 |
| `calculate_hrp_weights` | 🆕 선택 | HRP 최적화 (BL 대안) |

**제외된 기능** (bl-orchestrator로 이동):
- ~~`generate_views_from_technicals`~~
- ~~`generate_views_from_fundamentals`~~
- ~~`generate_views_from_sentiment`~~

### View Generation 전략

**결정**: Multi-agent debate로 View 생성

```
기존 계획 (복잡):
  기술지표/펀더멘탈 → 규칙 기반 로직 → P, Q, confidence
                     ↑ 자의적, 정당화 어려움

새 접근 (단순 + 강력):
  Multi-agent debate → LLM reasoning → P, Q, confidence
                       ↑ LLM이 직접 판단
```

**이유**:
1. 절대 뷰("AAPL이 10% 오른다")는 예측 거의 불가능
2. 상대 뷰("AAPL이 MSFT보다 나을 것")는 논쟁으로 정당화 가능
3. LLM이 데이터 보고 직접 토론 → 더 유연하고 설명 가능

### 예상 워크플로우 (bl-orchestrator)

```
1. Data Collection: AAPL, MSFT 펀더멘탈/기술지표/뉴스

2. Agent Debate:
   Bull: "AAPL P/E 낮고 모멘텀 강함, MSFT 대비 15% 아웃퍼폼"
   Bear: "AAPL 성장 둔화, MSFT 클라우드 강세, 5%가 현실적"
   Moderator: "합의: AAPL > MSFT by 8%, confidence 65%"

3. Output:
   {"P": [{"AAPL": 1, "MSFT": -1}], "Q": [0.08], "confidence": [0.65]}

4. bl-mcp 호출:
   optimize_portfolio_bl(tickers, views=output)
   backtest_portfolio(tickers, weights=result)
```

## Reference

상세 문서는 `memory-bank/` 참조:
- `activeContext.md` - 최근 변경사항
- `systemPatterns.md` - 설계 패턴
- `progress.md` - 전체 진행 상황
