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
