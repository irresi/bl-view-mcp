# Active Context

## 현재 상태

**날짜**: 2025-11-20
**Phase**: Phase 1 시작 전 (준비 단계)
**초점**: Memory Bank 초기화 및 구현 계획 수립

## 최근 변경사항

### 2025-11-20

1. **README.md 대폭 수정**
   - ❌ 제거: mcp Python SDK, Claude Desktop 연동
   - ✅ 추가: FastMCP 2.13.0.1, stdio/HTTP 듀얼 모드
   - 프로젝트 구조 명시
   - Phase 4 추가 (ADK Agent 통합)

2. **Memory Bank 초기화**
   - `projectbrief.md`: 프로젝트 목표 및 범위
   - `productContext.md`: 사용자 경험, 시나리오
   - `systemPatterns.md`: 아키텍처, 설계 패턴
   - `techContext.md`: 기술 스택, 개발 환경
   - `activeContext.md`: 현재 문서
   - `progress.md`: 진행 상황 추적

3. **Reference 자료 정리 및 최적화**
   - `reference/` 폴더 생성
   - `fastmcp/`, `PyPortfolioOpt/`, `9_AGENT_PROTOCOL/` 이동
   - 불필요한 파일 제거 (693MB → 11.6MB, 98% 감소)
     - `.git/` 제거 (35MB)
     - `tests/` 제거 (4.3MB)
     - `docs/` 제거 (9.5MB)
     - `.venv/` 제거 (630MB)
   - 핵심 파일만 유지:
     - fastmcp: `src/`, `examples/`
     - PyPortfolioOpt: `pypfopt/`, `cookbook/`
     - 9_AGENT_PROTOCOL: 전체 샘플 프로젝트 (380KB)
   - `reference/README.md` 작성 (상세 가이드)
   - `.gitignore` 업데이트 (소스 코드만 제외, README는 Git 추적)

## 현재 작업 초점

### 우선순위 1: 프로젝트 구조 정리 ✅

- [x] projectbrief.md 작성
- [x] productContext.md 작성
- [x] systemPatterns.md 작성
- [x] techContext.md 작성
- [x] activeContext.md 작성
- [x] progress.md 작성
- [x] Reference 자료 정리 (fastmcp, PyPortfolioOpt, 9_AGENT_PROTOCOL)

### 우선순위 2: Phase 1 준비

다음 단계로 Phase 1 구현을 시작합니다:

1. **프로젝트 설정**
   - [ ] `pyproject.toml` 작성
   - [ ] 패키지 구조 생성 (`bl_mcp/`, `bl_agent/`)
   - [ ] 의존성 설치

2. **유틸리티 구현**
   - [ ] `bl_mcp/utils/data_loader.py`
   - [ ] `bl_mcp/utils/validators.py`

3. **핵심 Tools**
   - [ ] `bl_mcp/tools.py` (4개 Tool 로직)
   - [ ] `bl_mcp/server.py` (FastMCP 래퍼)

4. **실행 스크립트**
   - [ ] `start_stdio.py`
   - [ ] `start_http.py`

## 활성 결정사항

### FastMCP 사용 결정

**날짜**: 2025-11-20

**결정**: FastMCP를 사용하여 stdio/HTTP 듀얼 모드 구현

**이유**:
1. `@mcp.tool` 데코레이터로 간결한 구현
2. stdio 모드로 Windsurf에서 직접 테스트 가능
3. HTTP 모드로 ADK Agent 연동 가능
4. 하나의 서버 코드로 두 가지 사용 사례 지원

**영향**:
- 개발 속도 향상 (보일러플레이트 최소화)
- 유연성 증가 (개발 → 프로덕션)
- 학습 곡선 낮음 (간단한 API)

### Reference 자료 정리

**위치**: `/reference/`

**내용**:
1. **fastmcp/** (35MB)
   - FastMCP 소스 코드
   - 예제 프로젝트들
   - 참고: `examples/`, API 사용법

2. **PyPortfolioOpt/** (28MB)
   - PyPortfolioOpt 소스 코드
   - 🌟 핵심: `cookbook/2-black-litterman.ipynb`
   - 참고: `pypfopt/*.py` API, `tests/` 사용 예제

3. **9_AGENT_PROTOCOL/** (630MB)
   - ADK Agent + FastMCP 샘플 프로젝트
   - 참고: `image_mcp/server.py`, `image_editor_agent_with_mcp/agent.py`

4. **Idzorek_onBL.pdf** (283KB, 선택적)
   - Black-Litterman 이론 배경
   - PyPortfolioOpt의 `idzorek_method()` 근거
   - 필요할 때만 참고 (이미 구현되어 있음)

**학습한 패턴**:
1. **FastMCP 서버 구조**
   - `@mcp.tool` 데코레이터 사용
   - tools.py로 로직 분리 (thin wrapper)
   - 명확한 Docstring

2. **Tools 로직 분리**
   - 순수 Python 함수
   - Dict 반환 (`{"success": True, ...}`)
   - 예외 처리 포함

3. **ADK Agent 패턴**
   - MCPToolset + StreamableHTTPConnectionParams
   - instruction/description 분리
   - Gemini 모델 사용

4. **PyPortfolioOpt API**
   - `expected_returns.mean_historical_return()`
   - `risk_models.ledoit_wolf()`
   - `BlackLittermanModel()`

## 다음 단계

### 즉시 (오늘)

1. ✅ Memory Bank 완성 및 검토
2. ✅ Reference 자료 정리 및 최적화 (693MB → 11.6MB)
3. [ ] Phase 1 구현 시작
   - `pyproject.toml` 작성
   - 패키지 구조 생성

### 단기 (이번 주)

1. **Phase 1 완료**
   - Tools 로직 구현 (4개)
   - FastMCP 서버 구현
   - Windsurf 연동 테스트

2. **시나리오 1 검증**
   - "AAPL, MSFT, GOOGL로 포트폴리오 최적화"
   - 전체 워크플로우 작동 확인

### 중기 (다음 주)

1. **Phase 2 시작**
   - 백테스팅 Tool
   - 팩터 스코어링
   - HRP 가중치

## 현재 고려사항

### 기술적 고려사항

1. **데이터 로딩 전략**
   - Parquet 파일이 이미 존재하는지 확인 필요
   - 없으면 `collect_ohlcv.py` 실행
   - 캐싱 전략 (동일한 데이터 중복 로드 방지)

2. **에러 처리**
   - 티커가 유효하지 않은 경우
   - 데이터가 부족한 경우 (최소 60일 권장)
   - 공분산 행렬이 singular인 경우

3. **타입 안전성**
   - 모든 함수에 type hints 추가
   - mypy로 검증

### 사용자 경험 고려사항

1. **명확한 피드백**
   - 각 Tool의 결과에 `success` 필드
   - 에러 시 명확한 메시지
   - 중간 결과 포함 (투명성)

2. **유연한 입력**
   - `start_date`/`end_date` 또는 `lookback_days`
   - 기본값 제공 (예: method="historical_mean")
   - 선택적 파라미터 활용

## 블로커 및 리스크

### 현재 블로커

없음 - Memory Bank 완성 후 바로 Phase 1 시작 가능

### 잠재적 리스크

1. **데이터 품질**
   - yfinance 데이터 누락 가능성
   - 완화: 충분한 데이터 검증, 대체 소스 고려

2. **공분산 행렬 특이성**
   - 데이터가 부족하거나 상관관계가 너무 높으면 singular
   - 완화: Ledoit-Wolf 축소 추정, 최소 데이터 요구사항

3. **성능**
   - 대량의 티커 처리 시 느려질 수 있음
   - 완화: 캐싱, 병렬 처리

## 학습 노트

### FastMCP 핵심 패턴

```python
# 1. 서버 초기화
mcp = FastMCP("server-name")

# 2. Tool 등록
@mcp.tool
def my_tool(param: str) -> dict:
    """설명"""
    return {"result": "value"}

# 3. 실행
mcp.run(transport="stdio")  # 또는 "http"
```

### PyPortfolioOpt 핵심 패턴

```python
# 1. 기대수익률
from pypfopt import expected_returns
mu = expected_returns.mean_historical_return(prices)

# 2. 공분산
from pypfopt import risk_models
S = risk_models.ledoit_wolf(prices)

# 3. 블랙-리터만
from pypfopt.black_litterman import BlackLittermanModel
bl = BlackLittermanModel(S, pi=pi, P=P, Q=Q, omega=omega)
weights = bl.bl_weights()
```

## 참고 자료

- **FastMCP 문서**: https://github.com/jlowin/fastmcp
- **PyPortfolioOpt 문서**: https://pyportfolioopt.readthedocs.io/
- **Google ADK**: https://github.com/google/generative-ai-python
- **9_AGENT_PROTOCOL**: 로컬 참고 프로젝트

## 메모

- Memory Bank 전략이 잘 작동하는지 확인 후 Phase 1 시작
- 각 파일의 역할이 명확하게 분리됨
- 점진적으로 복잡도를 높이는 접근 (Phase 1 → 2 → 3 → 4)
- stdio 모드로 빠른 반복, HTTP 모드로 프로덕션 확장
