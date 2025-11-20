# Reference Materials

이 폴더는 프로젝트 구현 시 참고할 자료들을 보관합니다.

**정리 완료**: 693MB → 11.6MB (98% 감소)

## 📁 폴더 구조

```
reference/
├── fastmcp/              # FastMCP 소스 코드 (2.6MB) ✅ 정리 완료
│   ├── src/             # 핵심 API 구현 (1.6MB)
│   ├── examples/        # 사용 예제 (612KB)
│   └── README.md
├── PyPortfolioOpt/       # PyPortfolioOpt 소스 코드 (9.0MB) ✅ 정리 완료
│   ├── pypfopt/         # 핵심 모듈 (224KB)
│   ├── cookbook/        # 실전 레시피 (8.8MB)
│   └── README.md
├── 9_AGENT_PROTOCOL/     # ADK Agent 샘플 (380KB) ✅ 정리 완료
│   ├── image_mcp/       # FastMCP 서버 예제
│   ├── image_editor_agent_with_mcp/  # ADK Agent 예제
│   └── pyproject.toml
├── Idzorek_onBL.pdf      # 📄 Black-Litterman 이론 (283KB, 선택적)
└── README.md            # 이 파일
```

---

## 1. FastMCP

**용도**: MCP 서버 구현 패턴 참고

### 핵심 참고 파일

```
fastmcp/
├── src/fastmcp/
│   ├── server.py          # 🔥 FastMCP 클래스 구현
│   ├── tools.py           # 🔥 @mcp.tool 데코레이터
│   └── utilities/         # HTTP/stdio 전송 모드
└── examples/              # 🔥 실제 사용 예제
    ├── hello_world/
    ├── weather/
    └── ...
```

### 주요 참고 사항

1. **`@mcp.tool` 데코레이터 사용법**
   - Type hints 자동 변환
   - Docstring → Tool 설명
   
2. **전송 모드**
   - `mcp.run(transport="stdio")`: Windsurf/Claude Desktop
   - `mcp.run(transport="http", host="...", port=...)`: ADK Agent

3. **에러 처리**
   - FastMCP가 자동으로 예외 처리
   - Dict 반환만 신경쓰면 됨

**참고할 예제**:
- `examples/weather/`: 외부 API 호출 패턴
- `examples/simple/`: 기본 Tool 구현

---

## 2. PyPortfolioOpt

**용도**: 블랙-리터만 모델 및 포트폴리오 최적화 API 참고

### 핵심 참고 파일

```
PyPortfolioOpt/
├── pypfopt/
│   ├── expected_returns.py       # 🔥 기대수익률 계산
│   ├── risk_models.py            # 🔥 공분산 행렬
│   ├── black_litterman.py        # 🔥 블랙-리터만 모델
│   ├── hierarchical_portfolio.py # 🔥 HRP
│   └── efficient_frontier.py     # Mean-Variance 최적화
├── cookbook/                     # 🔥 실전 레시피
│   ├── 1-basic-mean-variance.ipynb
│   ├── 2-black-litterman.ipynb   # 가장 중요!
│   ├── 3-hrp.ipynb
│   └── ...
└── tests/                        # 🔥 사용 예제 (단위 테스트)
    ├── test_black_litterman.py
    └── ...
```

### 필수 참고 자료

#### 1. 기대수익률 계산
```python
# pypfopt/expected_returns.py
from pypfopt import expected_returns

# 히스토리컬 평균
mu = expected_returns.mean_historical_return(prices)

# CAPM
mu = expected_returns.capm_return(prices, market_prices)

# 지수이동평균
mu = expected_returns.ema_historical_return(prices)
```

#### 2. 공분산 행렬
```python
# pypfopt/risk_models.py
from pypfopt import risk_models

# 샘플 공분산
S = risk_models.sample_cov(prices)

# Ledoit-Wolf 축소 추정 (권장)
S = risk_models.ledoit_wolf(prices)

# 지수 가중 공분산
S = risk_models.exp_cov(prices)
```

#### 3. 블랙-리터만 모델
```python
# pypfopt/black_litterman.py
from pypfopt.black_litterman import BlackLittermanModel

# 초기화
bl = BlackLittermanModel(
    cov_matrix=S,
    pi=market_implied_returns,  # Prior
    P=P_matrix,                  # View matrix
    Q=Q_vector,                  # Expected returns
    omega=omega_matrix,          # Uncertainty
    tau=0.025
)

# 사후 가중치 계산
weights = bl.bl_weights()

# 사후 기대수익률
posterior_returns = bl.bl_returns()
```

#### 4. HRP (계층적 위험 분산)
```python
# pypfopt/hierarchical_portfolio.py
from pypfopt import HRPOpt

hrp = HRPOpt(returns)
weights = hrp.optimize()
```

### 주요 Cookbook

1. **`cookbook/2-black-litterman.ipynb`** 🌟
   - 가장 중요한 참고 자료
   - View 생성 방법
   - Omega 계산 방법
   - Prior 설정 (시가총액 가중)

2. **`cookbook/3-hrp.ipynb`**
   - HRP 가중치 계산
   - 다각화 비율

3. **`cookbook/4-advanced-mean-variance.ipynb`**
   - 제약 조건 설정
   - 리스크 한도

### 테스트 파일 활용

`tests/test_black_litterman.py`:
- 실제 사용 예제
- 엣지 케이스 처리
- 검증 로직

---

## 3. 9_AGENT_PROTOCOL

**용도**: ADK Agent + FastMCP 통합 패턴 참고

### 핵심 참고 파일

```
9_AGENT_PROTOCOL/
├── image_mcp/
│   ├── server.py          # 🔥 FastMCP 서버 구조
│   └── tools.py           # 🔥 Tool 로직 분리 패턴
├── image_editor_agent_with_mcp/
│   ├── agent.py           # 🔥 ADK Agent 정의
│   └── prompt.py          # 🔥 Instruction/Description
├── start_image_mcp.py     # 🔥 HTTP 서버 실행
└── pyproject.toml         # 🔥 의존성 관리
```

### 학습 포인트

#### 1. FastMCP 서버 구조 (`image_mcp/server.py`)
```python
from fastmcp import FastMCP
from . import tools

mcp = FastMCP("image-processor")

@mcp.tool
def get_image_info(image_path: str) -> dict:
    """
    Get information about an image file.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Dictionary with image information
    """
    return tools.get_image_info(image_path)
```

**패턴**:
- FastMCP 초기화
- `@mcp.tool` 데코레이터
- tools.py로 로직 위임 (thin wrapper)
- 명확한 Docstring

#### 2. Tools 로직 분리 (`image_mcp/tools.py`)
```python
def get_image_info(image_path: str) -> dict:
    """순수 Python 함수 - MCP 독립적"""
    try:
        # 실제 로직
        return {
            "success": True,
            "width": ...,
            "height": ...,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**패턴**:
- 순수 함수 (테스트 용이)
- Dict 반환 (`success` 필드 포함)
- 예외 처리

#### 3. ADK Agent (`image_editor_agent_with_mcp/agent.py`)
```python
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

root_agent = Agent(
    model="gemini-2.5-flash",
    name="image_editor",
    description=DESCRIPTION,
    instruction=INSTRUCTION,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="http://localhost:5000/mcp"
            )
        )
    ]
)
```

**패턴**:
- MCPToolset으로 HTTP 연결
- instruction/description 분리
- Gemini 모델 사용

#### 4. Prompt 관리 (`image_editor_agent_with_mcp/prompt.py`)
```python
DESCRIPTION = """
이미지 편집 전문 에이전트입니다.
"""

INSTRUCTION = """
당신은 이미지 처리 전문가입니다.

# 주요 기능
1. 이미지 정보 조회
2. 리사이징
...

# 작업 방식
1. 사용자가 원하는 작업을 명확히 파악
2. 필요한 경우 이미지 정보를 먼저 조회
...
```

**패턴**:
- DESCRIPTION: 에이전트 역할 (한 줄)
- INSTRUCTION: 상세 가이드 (구조화된 마크다운)

#### 5. 실행 스크립트 (`start_image_mcp.py`)
```python
from image_mcp.server import mcp

mcp.run(transport="http", host="localhost", port=5000)
```

**패턴**:
- 간단한 진입점
- HTTP 모드 (ADK Agent용)

---

## 우리 프로젝트에 적용할 패턴

### 1. FastMCP 패턴 (from fastmcp + 9_AGENT_PROTOCOL)

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
    """Calculate expected returns for assets."""
    return tools.calculate_expected_returns(tickers, start_date, end_date, method)
```

### 2. Tools 로직 분리 (from 9_AGENT_PROTOCOL)

```python
# bl_mcp/tools.py
def calculate_expected_returns(...) -> dict:
    """순수 로직"""
    try:
        # PyPortfolioOpt 사용
        from pypfopt import expected_returns
        mu = expected_returns.mean_historical_return(prices)
        
        return {
            "success": True,
            "expected_returns": mu.to_dict(),
            ...
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 3. PyPortfolioOpt API 사용 (from cookbook/2-black-litterman.ipynb)

```python
# bl_mcp/tools.py - optimize_portfolio_bl
from pypfopt.black_litterman import BlackLittermanModel
from pypfopt import risk_models

# Prior (시가총액 가중)
market_caps = get_market_caps(tickers)
market_weights = market_caps / market_caps.sum()

# 시장 내재 수익률 (reverse optimization)
delta = 2.5  # 위험 회피 계수
pi = delta * S @ market_weights

# 블랙-리터만 모델
bl = BlackLittermanModel(
    cov_matrix=S,
    pi=pi,
    P=P,
    Q=Q,
    omega=omega,
    tau=0.025
)

weights = bl.bl_weights()
```

---

## 참고 자료 사용 가이드

### 구현 전 체크리스트

- [ ] FastMCP 예제 확인 (`fastmcp/examples/`)
- [ ] PyPortfolioOpt Cookbook 2, 3 읽기
- [ ] 9_AGENT_PROTOCOL 구조 분석
- [ ] `test_black_litterman.py` 사용 예제 확인

### 구현 중 참고

1. **API 확인**: `PyPortfolioOpt/pypfopt/*.py` 소스 코드
2. **예제 확인**: `PyPortfolioOpt/cookbook/*.ipynb`
3. **패턴 확인**: `9_AGENT_PROTOCOL/image_mcp/`

### 문제 발생 시

1. **FastMCP 이슈**: `fastmcp/examples/` 유사 케이스 찾기
2. **PyPortfolioOpt 이슈**: `tests/test_*.py` 참고
3. **ADK Agent 이슈**: `9_AGENT_PROTOCOL/` 비교

---

## 선택적 참고 자료

### Idzorek_onBL.pdf (283KB)

**제목**: "A Step-by-Step Guide to the Black-Litterman Model"  
**저자**: Thomas M. Idzorek, CFA  
**용도**: Black-Litterman 이론 배경 (선택적)

**PyPortfolioOpt와의 관계**:
- PyPortfolioOpt의 `idzorek_method()`는 이 논문 기반
- 이미 구현되어 있으므로 **manual 구현 불필요**
- 이론 이해가 필요할 때만 참고

**주요 내용**:
1. Reverse Optimization (Π = λΣw_mkt)
2. View Matrix 구성 (P, Q, Omega)
3. Confidence → Omega 변환 로직

**언제 참고?**:
- ❓ "왜 confidence 0.7인데 이런 결과?"
- ❓ "tau 기본값이 0.05인 이유?"
- ❓ PyPortfolioOpt 내부 동작 이해 필요

**참고 코드**:
```python
# PyPortfolioOpt가 이미 Idzorek 방법 구현
from pypfopt.black_litterman import BlackLittermanModel

bl = BlackLittermanModel(
    S,
    pi=market_prior,
    absolute_views={"AAPL": 0.10},
    omega="idzorek",              # Idzorek 방법 사용
    view_confidences=[0.7]        # 0-1 confidence
)
```

---

## 주의사항

⚠️ **이 폴더의 코드를 직접 복사하지 말 것**
- 참고만 하고 우리 프로젝트에 맞게 재작성
- 필요한 패턴만 추출
- 라이선스 확인 (MIT, Apache 등)

⚠️ **Git에 커밋하지 말 것**
- `.gitignore`에 `reference/` 추가 필요
- 외부 저장소는 dependency로 관리

---

## 다음 단계

1. ✅ Reference 자료 정리 완료
2. [ ] `.gitignore`에 `reference/` 추가
3. [ ] 필요한 패턴 Memory Bank에 요약
4. [ ] Phase 1 구현 시작
