# System Patterns

## 시스템 아키텍처

### 전체 구조

```
┌─────────────────┐
│   AI Client     │  (Windsurf, Claude Desktop, ADK Agent)
│   (사용자)       │
└────────┬────────┘
         │
         │ MCP Protocol
         │
┌────────▼────────┐
│  FastMCP Server │
│  (stdio/HTTP)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────┐
│ Tools │ │ Utils   │
│ Logic │ │ (검증,   │
│       │ │ 데이터)  │
└───┬───┘ └──┬──────┘
    │        │
    └────┬───┘
         │
┌────────▼────────┐
│ PyPortfolioOpt  │
│ (핵심 라이브러리) │
└────────┬────────┘
         │
┌────────▼────────┐
│ Parquet Data    │
│ (로컬 저장소)    │
└─────────────────┘
```

### 레이어 분리

#### 1. Presentation Layer (FastMCP Server)

**책임**: MCP 프로토콜 처리, 타입 변환

```python
# bl_mcp/server.py
from fastmcp import FastMCP
from . import tools

mcp = FastMCP("black-litterman-portfolio")

@mcp.tool
def calculate_expected_returns(
    tickers: list[str],
    start_date: str,
    end_date: str | None = None,
    method: str = "historical_mean"
) -> dict:
    """MCP Tool 래퍼 - FastMCP가 자동으로 스키마 생성"""
    return tools.calculate_expected_returns(tickers, start_date, end_date, method)
```

**패턴**: 
- Thin wrapper - 로직은 tools.py로 위임
- Type hints를 통한 자동 스키마 생성
- 예외는 FastMCP가 자동 처리

#### 2. Business Logic Layer (Tools)

**책임**: 핵심 계산 로직, PyPortfolioOpt 래퍼

```python
# bl_mcp/tools.py
from pypfopt import expected_returns, risk_models, BlackLittermanModel
from .utils import data_loader, validators

def calculate_expected_returns(
    tickers: list[str],
    start_date: str,
    end_date: str | None,
    method: str
) -> dict:
    """순수 Python 함수 - MCP 독립적"""
    # 1. 검증
    validators.validate_tickers(tickers)
    validators.validate_date_range(start_date, end_date)
    
    # 2. 데이터 로드
    prices = data_loader.load_prices(tickers, start_date, end_date)
    
    # 3. 계산
    if method == "historical_mean":
        returns = expected_returns.mean_historical_return(prices)
    elif method == "capm":
        returns = expected_returns.capm_return(prices)
    
    # 4. 결과 반환
    return {
        "success": True,
        "tickers": tickers,
        "expected_returns": returns.to_dict(),
        "method": method,
        "period": {"start": start_date, "end": end_date}
    }
```

**패턴**:
- Pure functions - 테스트 용이
- Dict 반환 - JSON 직렬화 가능
- 명확한 에러 처리

#### 3. Utility Layer

**책임**: 공통 기능 (데이터 로딩, 검증)

```python
# bl_mcp/utils/data_loader.py
def load_prices(tickers, start_date, end_date):
    """Parquet에서 가격 데이터 로드"""
    
# bl_mcp/utils/validators.py
def validate_tickers(tickers):
    """티커 유효성 검증"""
    if not tickers:
        raise ValueError("티커 목록이 비어있습니다")
```

## 핵심 설계 결정

### 1. FastMCP 선택

**이유**:
- `@mcp.tool` 데코레이터로 간결한 구현
- stdio/HTTP 듀얼 모드 지원
- Type hints 자동 변환
- 보일러플레이트 코드 최소화

**대안 고려**:
- ❌ mcp Python SDK: 너무 저수준, 보일러플레이트 많음
- ❌ 직접 구현: 시간 소모, 버그 위험

### 2. PyPortfolioOpt 사용

**이유**:
- 업계 표준 라이브러리
- 블랙-리터만 모델 내장
- 다양한 최적화 기법 지원
- 활발한 유지보수

**래퍼 패턴**:
```python
# PyPortfolioOpt를 직접 노출하지 않고 래핑
def optimize_portfolio_bl(...):
    bl_model = BlackLittermanModel(...)
    weights = bl_model.bl_weights()
    return {"success": True, "weights": weights}
```

### 3. 데이터 저장: Parquet

**이유**:
- 빠른 읽기 성능
- 효율적인 압축
- 타입 정보 보존
- Pandas 네이티브 지원

**구조**:
```
data/
├── prices/
│   ├── AAPL.parquet
│   ├── MSFT.parquet
│   └── ...
└── fundamentals/
    └── market_cap.parquet
```

### 4. 모듈형 Tools

**패턴**: 각 Tool은 독립적으로 사용 가능

```python
# Tool 체이닝
returns = calculate_expected_returns(...)
cov = calculate_covariance_matrix(...)
view = create_investor_view(...)
portfolio = optimize_portfolio_bl(
    expected_returns=returns,  # Tool 1의 출력
    covariance_matrix=cov,      # Tool 2의 출력
    views=[view]                # Tool 3의 출력
)
```

**장점**:
- AI가 필요한 단계만 선택 가능
- 중간 결과 검증 용이
- 재사용성 높음

## 에러 처리 전략

### 1. 입력 검증 (Validators)

```python
def validate_date_range(start_date, end_date):
    if end_date and start_date > end_date:
        raise ValueError(f"시작 날짜({start_date})가 종료 날짜({end_date})보다 늦습니다")
```

### 2. 데이터 검증

```python
def load_prices(tickers, start_date, end_date):
    prices = pd.read_parquet(...)
    if prices.isnull().sum().sum() > len(prices) * 0.1:
        raise DataQualityError("결측치가 10% 이상입니다")
    return prices
```

### 3. 계산 검증

```python
def optimize_portfolio_bl(...):
    try:
        weights = bl_model.bl_weights()
    except np.linalg.LinAlgError:
        return {
            "success": False,
            "error": "공분산 행렬이 특이(singular)합니다. 더 많은 데이터가 필요합니다."
        }
```

### 4. 명확한 에러 메시지

```python
{
    "success": False,
    "error": "AAPL 데이터가 부족합니다 (최소 60일 필요, 현재 45일)",
    "error_type": "InsufficientDataError"
}
```

## 전송 모드 패턴

### stdio 모드 (개발/일반 사용)

```python
# start_stdio.py
from bl_mcp.server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**사용 케이스**:
- Windsurf에서 직접 테스트
- Claude Desktop 통합
- 빠른 프로토타이핑

### HTTP 모드 (프로덕션)

```python
# start_http.py
from bl_mcp.server import mcp

if __name__ == "__main__":
    mcp.run(transport="http", host="localhost", port=5000)
```

**사용 케이스**:
- ADK Agent 연동
- 웹 서비스 통합
- 멀티 클라이언트 지원

## 테스트 전략

### 1. Unit Tests (tools.py)

```python
def test_calculate_expected_returns():
    result = tools.calculate_expected_returns(
        tickers=["AAPL", "MSFT"],
        start_date="2023-01-01",
        end_date="2024-01-01",
        method="historical_mean"
    )
    assert result["success"] is True
    assert "expected_returns" in result
```

### 2. Integration Tests (MCP 서버)

```python
def test_mcp_tool_chain():
    # 실제 MCP 서버에 요청
    returns = mcp_client.call_tool("calculate_expected_returns", ...)
    cov = mcp_client.call_tool("calculate_covariance_matrix", ...)
    portfolio = mcp_client.call_tool("optimize_portfolio_bl", ...)
    assert portfolio["success"] is True
```

### 3. Scenario Tests (Windsurf)

실제 AI와의 상호작용 테스트:
1. Windsurf에서 자연어 요청
2. AI가 적절한 Tools 호출하는지 확인
3. 결과가 합리적인지 검증

## 확장성 고려

### 새로운 Tool 추가

```python
# 1. tools.py에 로직 구현
def calculate_risk_parity_weights(...):
    ...

# 2. server.py에 MCP Tool 등록
@mcp.tool
def calculate_risk_parity_weights(...) -> dict:
    return tools.calculate_risk_parity_weights(...)
```

### 새로운 자산군 추가

```python
# data_loader.py에 로더 추가
def load_crypto_prices(tickers, start_date, end_date):
    # ccxt를 사용한 암호화폐 데이터
    ...
```

## 날짜 범위 처리 패턴 (Period Parameter)

### 설계 원칙: 상호 배타적 파라미터 (Mutually Exclusive)

MCP와 LLM의 특성을 고려한 날짜 범위 처리 설계:

**핵심 결정**:
- `period` (상대 기간) vs `start_date` (절대 날짜)를 분리
- 두 파라미터를 동시 사용하지 않도록 권장
- LLM이 의도를 명확히 전달할 수 있도록 docstring 개선

### 구현 패턴

```python
# 1. 파라미터 정의 (tools.py)
def calculate_expected_returns(
    tickers: list[str],
    start_date: Optional[str] = None,  # 절대 날짜: "2023-01-01"
    end_date: Optional[str] = None,
    period: Optional[str] = None,      # 상대 기간: "1Y", "3M"
    method: str = "historical_mean"
) -> dict:
    """
    Date Range Options (mutually exclusive):
        - Provide 'period' for recent data (RECOMMENDED): "1Y", "3M", "1W"
        - Provide 'start_date' for historical data: "2023-01-01"
        - If both provided, 'start_date' takes precedence
        - If neither provided, defaults to "1Y" (1 year)
    """
    # 날짜 범위 해결
    start_date, end_date = validators.resolve_date_range(
        period=period,
        start_date=start_date,
        end_date=end_date
    )
```

```python
# 2. 날짜 범위 해결 로직 (validators.py)
def resolve_date_range(
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> tuple[str, str]:
    """
    Resolve date range from either period or absolute dates.
    
    Priority:
    1. If both period and start_date provided -> use start_date (with warning)
    2. If only start_date -> absolute date mode
    3. If only period -> relative period mode
    4. If neither -> default to "1Y"
    """
    # end_date 기본값: 오늘
    target_end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
    
    # 상호 배타성 체크
    if start_date and period:
        warnings.warn("Both provided. Using 'start_date'.")
        period = None
    
    # start_date 해결
    if start_date:
        target_start = datetime.strptime(start_date, "%Y-%m-%d")
    elif period:
        period_delta = parse_period(period)  # "1Y" -> timedelta(days=365)
        target_start = target_end - period_delta
    else:
        target_start = target_end - timedelta(days=365)  # 기본 1년
    
    return target_start.strftime("%Y-%m-%d"), target_end.strftime("%Y-%m-%d")
```

```python
# 3. Period 파싱 (validators.py)
def parse_period(period: str) -> timedelta:
    """
    Parse relative period string to timedelta.
    
    Supported formats:
    - "1D", "7D" (days)
    - "1W", "4W" (weeks)
    - "1M", "3M", "6M" (months, ~30 days)
    - "1Y", "2Y", "5Y" (years, ~365 days)
    """
    match = re.match(r"^(\d+)([DWMY])$", period.upper())
    if not match:
        raise ValueError(f"Invalid period: '{period}'. Use '1Y', '3M', etc.")
    
    amount, unit = int(match.group(1)), match.group(2)
    
    if unit == "D":
        return timedelta(days=amount)
    elif unit == "W":
        return timedelta(weeks=amount)
    elif unit == "M":
        return timedelta(days=amount * 30)  # 근사값
    elif unit == "Y":
        return timedelta(days=amount * 365)  # 근사값
```

### 사용 시나리오

```python
# 시나리오 A: 최근 데이터 (권장)
result = calculate_expected_returns(
    tickers=["AAPL", "MSFT"],
    period="1Y"  # 최근 1년
)

# 시나리오 B: 특정 구간
result = calculate_expected_returns(
    tickers=["AAPL", "MSFT"],
    start_date="2020-01-01",
    end_date="2020-12-31"  # 2020년 전체
)

# 시나리오 C: 특정 시점부터 현재까지
result = calculate_expected_returns(
    tickers=["AAPL", "MSFT"],
    start_date="2023-01-01"  # end_date는 오늘
)
```

### LLM 가이드 (Docstring)

**핵심 문구**:
- "Mutually exclusive: Provide EITHER 'period' OR 'start_date'"
- "(RECOMMENDED)" - LLM이 period를 우선 선택하도록 유도
- "Do NOT use with 'start_date'" - 명확한 금지 지시

**이점**:
1. **명확성**: LLM이 어떤 파라미터를 사용할지 쉽게 판단
2. **안정성**: 파싱 로직이 단순해져 에러 감소
3. **유지보수**: 절대/상대 날짜 처리가 명확히 분리
4. **토큰 효율**: 복잡한 설명 불필요, 간결한 docstring

### 왜 통합 인자가 아닌가?

**통합 방식 (start_date에 "1Y" 또는 "2023-01-01")**:
- ❌ 파싱 로직 복잡 (정규식 필요)
- ❌ LLM 혼란 가능 ("1Y"가 날짜 필드에 들어갈 수 있나?)
- ❌ 에러 메시지 모호

**분리 방식 (period vs start_date)**:
- ✅ 필드 이름만 봐도 의도 명확
- ✅ 검증 로직 단순
- ✅ LLM이 "Slot Filling" 방식으로 쉽게 처리
- ✅ 금융 도메인에서 데이터 정확성 보장

## 성능 최적화

### 1. 데이터 캐싱

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def load_prices(tickers_tuple, start_date, end_date):
    # 동일한 요청은 캐시에서 반환
    ...
```

### 2. 병렬 처리

```python
from concurrent.futures import ThreadPoolExecutor

def load_multiple_tickers(tickers):
    with ThreadPoolExecutor() as executor:
        results = executor.map(load_single_ticker, tickers)
    return pd.concat(results)
```

### 3. 지연 로딩

```python
# 필요할 때만 데이터 로드
def optimize_portfolio_bl(...):
    if views:
        # 견해가 있을 때만 Omega 계산
        omega = calculate_omega(...)
```

## Idzorek Black-Litterman 패턴

### 핵심 원리

**Idzorek 방식**: Confidence → Ω (Omega) 역산

```
사용자 입력                PyPortfolioOpt 내부              Idzorek 알고리즘
───────────────           ─────────────────────           ──────────────────
views (dict)     →        P, Q 자동 생성          →       
confidence (%)   →                                →       Ω 역산
                                                  →       Black-Litterman
                                                          최적화
```

### 구현 패턴

```python
# 1. Absolute View 사용 (간단하고 LLM 친화적)
bl = BlackLittermanModel(
    S,                                  # Covariance matrix
    pi=market_prior,                    # Market equilibrium
    absolute_views=views,               # {"AAPL": 0.10} → P, Q 자동!
    omega="idzorek",                    # Ω 역산 알고리즘
    view_confidences=view_conf_list     # [0.7, 0.8, ...]
)

# 2. Per-View Confidence 지원
if isinstance(confidence, dict):
    # View별로 다른 confidence
    view_conf_list = [confidence[ticker] for ticker in views.keys()]
else:
    # 모든 view에 동일한 confidence
    view_conf_list = [confidence] * len(views)
```

### 검증 패턴

```python
# Dict confidence validation
if isinstance(confidence, dict):
    for ticker in views.keys():
        if ticker not in confidence:
            raise ValueError(f"Missing confidence for view '{ticker}'")
    # 각 confidence 개별 검증
    confidence = {k: validate_confidence(v) for k, v in confidence.items()}
```

### 사용 예시

```python
# 기본: 단일 confidence
views = {"AAPL": 0.10}
confidence = 0.7  # 모든 view에 70%

# 고급: View별 다른 confidence
views = {"AAPL": 0.10, "MSFT": 0.05}
confidence = {"AAPL": 0.9, "MSFT": 0.6}  # AAPL 90%, MSFT 60%
```

## Parameter Safety 패턴

### Parameter Swap 감지 및 복구

```python
# CRITICAL: Check parameter types first (MCP may swap them!)
if views is not None:
    if not isinstance(views, dict):
        # Check if views and confidence got swapped
        if isinstance(views, (int, float)) and isinstance(confidence, dict):
            # Swap them back
            logging.warning("⚠️ PARAMETER SWAP DETECTED!")
            views, confidence = confidence, views
        else:
            raise ValueError(
                f"views must be a dict or None, got {type(views).__name__}"
            )
```

### Keyword Arguments 패턴

```python
# server.py → tools.py (keyword args로 안전성 확보)
return tools.optimize_portfolio_bl(
    tickers=tickers,          # ✅ Keyword args
    start_date=start_date,
    end_date=end_date,
    period=period,            # ✅ Parameter 순서 무관
    market_caps=market_caps,
    views=views,
    confidence=confidence,
    risk_aversion=risk_aversion
)
```

### Debug Logging 패턴

```python
# Parameter 추적 로깅
logging.warning("=" * 80)
logging.warning(f"🔍 optimize_portfolio_bl CALLED:")
logging.warning(f"  📊 views = {views!r} (type: {type(views).__name__})")
logging.warning(f"  🎯 confidence = {confidence!r}")
logging.warning("=" * 80)
```

## LLM Prompt 최적화 패턴

### 간결성 우선 원칙

**Before (267줄)**:
- 중복된 설명
- 너무 많은 예시
- 장황한 이론

**After (72줄, 73% 감소)**:
- 핵심만 남김
- 1개의 완벽한 예시
- 명확한 타입 규칙

### 핵심 메시지 강조

```markdown
# 핵심 규칙 (CRITICAL!)

## 파라미터 타입
- tickers: 리스트 → ["AAPL", "MSFT"]
- views: 딕셔너리 → {"AAPL": 0.10}
- confidence: 숫자 → 85 또는 0.85

## 가장 흔한 실수 (절대 하지 마세요!)
❌ views=0.85 (숫자 X, 딕셔너리여야 함!)
❌ confidence={"AAPL": 0.10} (딕셔너리 X, 숫자여야 함!)
```

### 자연어 변환 간결화

```markdown
## 확신도 (confidence)
- "매우 확신" → 95
- "확신" → 85
- "보통" → 50
- "불확실" → 30
```

### 1개의 완벽한 예시

```python
# 모든 것을 보여주는 하나의 예시
optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="1Y",
    views={"AAPL": 0.10},
    confidence=85
)
```

## 테스트 패턴

### Idzorek 구현 테스트

```python
def test_single_confidence():
    """단일 confidence 테스트"""
    result = optimize_portfolio_bl(
        tickers=["AAPL", "MSFT", "GOOGL"],
        period="1Y",
        views={"AAPL": 0.10},
        confidence=0.7
    )
    assert result["success"]

def test_per_view_confidence():
    """View별 confidence 테스트"""
    result = optimize_portfolio_bl(
        tickers=["AAPL", "MSFT", "GOOGL"],
        period="1Y",
        views={"AAPL": 0.10, "MSFT": 0.05},
        confidence={"AAPL": 0.9, "MSFT": 0.6}
    )
    assert result["success"]
```

### 검증 테스트 구조

```python
# 6가지 핵심 시나리오
tests = [
    "Single confidence",           # ✅
    "Per-view confidence",         # ✅
    "Missing confidence detection",# ✅
    "Percentage input (70 → 0.7)", # ✅
    "Market equilibrium (no views)",# ✅
    "Default confidence (0.5)"     # ✅
]
```

---

## Relative View Support Patterns

### P, Q 전용 API 패턴

**Date**: 2025-11-22

**Context**: LLM이 절대적 뷰 dict와 P, Q를 혼용하여 예측 불가능한 동작 발생

**Decision**: Breaking Change - 모든 views를 P, Q 형식으로 통일

**Implementation**:

```python
# ❌ 제거된 형식 (Breaking Change!)
views = {"AAPL": 0.10}
views = {"AAPL": 0.10, "P": [...], "Q": [...]}  # 혼용
confidence = {"AAPL": 0.9}  # Dict confidence

# ✅ 유일한 형식
views = {"P": [{"AAPL": 1}], "Q": [0.10]}  # Absolute
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}  # Relative
confidence = 0.7  # Float
confidence = [0.9, 0.8]  # List
```

**Benefits**:
1. **API 일관성**: 하나의 명확한 방법
2. **LLM 친화적**: 혼동 가능성 제거
3. **명확한 에러**: "must use P, Q format"
4. **확장성**: Relative view 자연스럽게 지원

**Trade-offs**:
- 기존 코드 깨짐 (Breaking Change)
- 더 verbose (3자 대신 P, Q 명시)

### Dict-based P Matrix 패턴

**Pattern**: Ticker 이름 기반 P 매트릭스

**Format**:
```python
# Dict-based (LLM 친화적)
P = [{"NVDA": 1, "AAPL": -1}]  # NVDA - AAPL

# NumPy (고급 사용자)
P = [[1, -1, 0]]  # Index 기반
```

**Advantages**:
1. **Order-independent**: Ticker 순서 상관없음
2. **Self-documenting**: 코드만 봐도 의미 명확
3. **LLM generation**: 자연어에서 쉽게 생성
   - "NVDA가 AAPL보다 높다" → `{"NVDA": 1, "AAPL": -1}`

**Implementation**:
```python
def _parse_views(views: dict, tickers: list[str]):
    if isinstance(P_input[0], dict):
        # Dict-based P
        P = np.zeros((len(P_input), len(tickers)))
        for i, view_dict in enumerate(P_input):
            for ticker, weight in view_dict.items():
                j = tickers.index(ticker)  # Ticker → Index
                P[i, j] = weight
    else:
        # NumPy P
        P = np.array(P_input)
```

### Confidence 단순화 패턴

**Pattern**: Float 또는 List만 허용

**Rationale**:
- P, Q 형식에서는 ticker 이름이 P 내부에 있음
- Dict key로 매칭 불가능
- List가 더 명확하고 일관적

**Before**:
```python
# 3가지 타입 지원 (혼란)
confidence = 0.7  # Float
confidence = {"AAPL": 0.9}  # Dict (absolute views only!)
confidence = [0.9, 0.8]  # List
```

**After**:
```python
# 2가지 타입만 지원 (명확)
confidence = 0.7  # Float → all views
confidence = [0.9, 0.8]  # List → per-view
```

**Implementation**:
```python
def _normalize_confidence(confidence, views, tickers):
    num_views = len(views["Q"])
    
    if confidence is None:
        return [0.5] * num_views
    elif isinstance(confidence, (int, float)):
        return [confidence] * num_views
    elif isinstance(confidence, list):
        if len(confidence) != num_views:
            raise ValueError("Length mismatch")
        return confidence
    else:
        raise TypeError("Invalid type")  # Dict 제거!
```

### Breaking Change 관리 패턴

**Pattern**: 명확한 에러 메시지로 마이그레이션 유도

**Old Format Detection**:
```python
if "P" not in views or "Q" not in views:
    raise ValueError(
        "Views must use P, Q format. "
        "Examples:\n"
        "  Absolute view: {'P': [{'AAPL': 1}], 'Q': [0.10]}\n"
        "  Relative view: {'P': [{'NVDA': 1, 'AAPL': -1}], 'Q': [0.20]}"
    )
```

**Benefits**:
1. **Clear migration path**: 예시 포함
2. **Fail fast**: 즉시 에러로 명확한 피드백
3. **Documentation**: 에러 메시지 자체가 문서

**Testing**:
```python
def test_old_format_rejected():
    result = optimize_portfolio_bl(
        views={"AAPL": 0.10}  # Old format
    )
    assert not result["success"]
    assert "must use P, Q format" in result["error"]
```
