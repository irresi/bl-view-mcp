# Technical Context

## 기술 스택

### 핵심 프레임워크

#### FastMCP 2.13.0.1

**역할**: MCP 서버 프레임워크

**선택 이유**:
- `@mcp.tool` 데코레이터로 간결한 구현
- stdio/HTTP 듀얼 전송 모드
- Python type hints 자동 변환
- 최소 보일러플레이트

**사용 패턴**:
```python
from fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool
def my_tool(param: str) -> dict:
    """Tool 설명"""
    return {"result": "success"}

# stdio 모드
mcp.run(transport="stdio")

# HTTP 모드
mcp.run(transport="http", host="localhost", port=5000)
```

#### PyPortfolioOpt 1.5.5+

**역할**: 포트폴리오 최적화 핵심 라이브러리

**주요 모듈**:
- `expected_returns`: 기대수익률 계산
  - `mean_historical_return()`: 히스토리컬 평균
  - `ema_historical_return()`: 지수이동평균
  - `capm_return()`: CAPM 모델
  
- `risk_models`: 공분산 행렬 계산
  - `sample_cov()`: 샘플 공분산
  - `ledoit_wolf()`: Ledoit-Wolf 축소 추정
  - `exp_cov()`: 지수 가중 공분산
  
- `black_litterman.BlackLittermanModel`: 블랙-리터만 최적화
  - P, Q 행렬로 views 정의
  - `omega="idzorek"` + `view_confidences` 사용
  - `bl_weights()`: 최적 가중치 계산
  - `bl_returns()`: 사후 기대수익률
  
- `hierarchical_portfolio.HRPOpt`: 계층적 위험 분산
  - `optimize()`: HRP 가중치 계산

**문서**: https://pyportfolioopt.readthedocs.io/

### 데이터 처리

#### Pandas 2.0.0+

**역할**: 데이터 조작 및 분석

**주요 사용**:
- 시계열 데이터 처리
- 결측치 처리 (`fillna`, `dropna`)
- 리샘플링 (`resample`)
- 수익률 계산 (`pct_change`)

#### NumPy 1.24.0+

**역할**: 수치 계산

**주요 사용**:
- 행렬 연산 (공분산, 역행렬)
- 통계 함수 (평균, 표준편차)
- 선형대수 (`np.linalg`)

#### yfinance 0.2.0+

**역할**: 시장 데이터 수집

**사용 패턴**:
```python
import yfinance as yf

# 가격 데이터
ticker = yf.Ticker("AAPL")
hist = ticker.history(start="2023-01-01", end="2024-01-01")

# 펀더멘탈 데이터
info = ticker.info  # 시가총액, PE ratio 등

# Parquet 저장
hist.to_parquet(f"data/prices/{ticker}.parquet")
```

### 백테스팅 (Phase 2)

#### empyrical (권장)

**역할**: 성과 지표 계산

**주요 함수**:
- `annual_return()`: 연간 수익률
- `sharpe_ratio()`: 샤프 비율
- `max_drawdown()`: 최대 낙폭
- `sortino_ratio()`: 소르티노 비율
- `alpha_beta()`: 알파, 베타

#### VectorBT (선택)

**역할**: 포트폴리오 백테스팅

**장점**:
- 벡터화 연산으로 빠른 성능
- 리밸런싱 내장
- 다중 자산 포트폴리오 지원

### 선택적 의존성

#### Google ADK 1.14.1 (Phase 4)

**역할**: AI Agent 프레임워크

**설치**: `pip install -e ".[agent]"`

**사용 패턴**:
```python
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

agent = Agent(
    model="gemini-2.5-flash",
    tools=[MCPToolset(connection_params=...)]
)
```

#### ccxt (Phase 3 - 암호화폐)

**역할**: 암호화폐 거래소 데이터

**지원 거래소**: Binance, Upbit, Coinbase 등

#### pykrx (Phase 3 - 한국 주식)

**역할**: 한국 증권 시장 데이터

**주요 기능**:
- KRX 주식 데이터
- 시가총액, 거래량
- 업종 분류

## 개발 환경

### Python 버전

- **요구사항**: Python 3.11+
- **이유**: 
  - Modern type hints (`str | None`)
  - 향상된 성능
  - FastMCP 호환성

### 패키지 관리자

#### uv (권장)

```bash
# 프로젝트 초기화
uv init

# 의존성 설치
uv sync

# 의존성 추가
uv add fastmcp pypfopt pandas numpy yfinance
```

**장점**:
- Rust 기반 고속 설치
- `pyproject.toml` 네이티브 지원
- 가상환경 자동 관리

#### pip (대안)

```bash
pip install -e .
pip install -e ".[agent]"  # ADK Agent 포함
```

### pyproject.toml 구조

```toml
[project]
name = "black-litterman-mcp"
version = "0.1.0"
description = "Black-Litterman Portfolio Optimization MCP Server"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastmcp==2.13.0.1",
    "PyPortfolioOpt>=1.5.5",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "yfinance>=0.2.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
agent = [
    "google-adk[a2a]==1.14.1",
    "google-genai>=1.38.0",
]
dev = [
    "pytest>=7.4.0",
    "mypy>=1.5.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
backtest = [
    "empyrical>=0.5.5",
    "vectorbt>=0.25.0",
]
```

## 개발 도구

### 코드 품질

#### mypy (타입 체커)

```bash
mypy bl_mcp/ --strict
```

**설정** (pyproject.toml):
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

#### ruff (린터 + 포매터)

```bash
ruff check bl_mcp/
ruff format bl_mcp/
```

**장점**: Black + isort + flake8을 대체, 매우 빠름

### 테스팅

#### pytest

```bash
pytest tests/ -v
```

**구조**:
```
tests/
├── test_tools.py           # Unit tests
├── test_validators.py      # 검증 로직
├── test_data_loader.py     # 데이터 로딩
└── test_integration.py     # End-to-end
```

## 데이터 저장

### Parquet 파일 구조

```
data/
├── prices/                 # OHLCV 데이터
│   ├── AAPL.parquet       # 칼럼: Date, Open, High, Low, Close, Volume
│   ├── MSFT.parquet
│   └── ...
├── fundamentals/           # 펀더멘탈 데이터
│   └── market_cap.parquet # 칼럼: Date, Ticker, MarketCap
└── metadata.json           # 메타데이터 (업데이트 시간 등)
```

### 데이터 업데이트 스크립트

```python
# scripts/update_data.py
import yfinance as yf
from pathlib import Path

def update_ticker_data(ticker: str, start_date: str):
    data = yf.Ticker(ticker).history(start=start_date)
    output_path = Path(f"data/prices/{ticker}.parquet")
    data.to_parquet(output_path)
```

## 환경 변수

### .env 파일

```bash
# API Keys (선택사항)
ALPHA_VANTAGE_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here

# 데이터 경로
DATA_PATH=./data

# 캐시 설정
CACHE_ENABLED=true
CACHE_TTL=3600

# 로깅
LOG_LEVEL=INFO
LOG_FILE=logs/bl_mcp.log
```

### python-dotenv 사용

```python
from dotenv import load_dotenv
import os

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH", "./data")
```

## 통신 프로토콜

### MCP (Model Context Protocol)

**개념**: AI와 도구 간 표준 프로토콜

**메시지 형식**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "calculate_expected_returns",
    "arguments": {
      "tickers": ["AAPL", "MSFT"],
      "start_date": "2023-01-01",
      "method": "historical_mean"
    }
  }
}
```

**응답**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "tickers": ["AAPL", "MSFT"],
    "expected_returns": {
      "AAPL": 0.12,
      "MSFT": 0.15
    }
  }
}
```

### stdio vs HTTP

| 특성 | stdio | HTTP |
|------|-------|------|
| 사용 케이스 | IDE 통합 | 프로덕션, 웹 |
| 설정 | MCP config | URL |
| 디버깅 | 어려움 | 용이 (curl, Postman) |
| 멀티 클라이언트 | 불가 | 가능 |
| 보안 | 로컬만 | 인증 필요 |

## 제약사항

### 성능

- **목표**: 각 Tool 호출 < 10초
- **병목**: 데이터 I/O, 행렬 연산
- **최적화**: 캐싱, 병렬 처리

### 메모리

- **제한**: 로컬 메모리 내에서 처리
- **대용량 데이터**: 청킹, 스트리밍

### 데이터 품질

- **yfinance 제약**: 
  - 무료 API, 속도 제한
  - 데이터 누락 가능
  - 펀더멘탈 데이터 제한적

## 향후 기술 고려사항

### Phase 3

- **한국 주식**: pykrx, FinanceDataReader
- **암호화폐**: ccxt
- **실시간 데이터**: WebSocket, 유료 API

### Phase 4

- **ADK Agent**: Gemini 기반 자동화
- **멀티 에이전트**: 데이터 수집, 분석, 최적화 분리
- **웹 UI**: FastAPI + React (선택사항)

### 확장 가능성

- **Docker 배포**: 일관된 환경
- **클라우드 배포**: AWS Lambda, Cloud Run
- **스케일링**: Redis 캐싱, 분산 처리
