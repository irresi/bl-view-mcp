# Contributing to Black-Litterman View Generation MCP

프로젝트에 기여해주셔서 감사합니다! 이 문서는 프로젝트를 처음 접하는 분들을 위한 가이드입니다.

## 목차

- [프로젝트 개요](#프로젝트-개요)
- [개발 환경 설정](#개발-환경-설정)
- [데이터 준비](#데이터-준비)
- [개발 워크플로우](#개발-워크플로우)
- [테스트](#테스트)
- [코드 스타일](#코드-스타일)
- [Pull Request 가이드](#pull-request-가이드)

---

## 프로젝트 개요

Black-Litterman 포트폴리오 최적화를 MCP(Model Context Protocol) 서버로 구현한 프로젝트입니다.

### 핵심 구조

```
bl_mcp/               # MCP 서버 코드
├── server.py         # FastMCP 서버 (MCP 래퍼)
├── tools.py          # 핵심 로직 (4개 도구)
└── utils/            # 유틸리티
    ├── data_loader.py
    ├── validators.py
    └── session.py

scripts/              # 데이터 다운로드 스크립트
├── download_data.py
└── download_sp500.py

tests/                # 테스트
├── test_simple.py
└── test_agent.py
```

### 구현된 도구 (Phase 1)

1. `calculate_expected_returns` - 기대수익률 계산
2. `calculate_covariance_matrix` - 공분산 행렬 계산
3. `create_investor_view` - 투자자 견해 생성
4. `optimize_portfolio_bl` - Black-Litterman 최적화

---

## 개발 환경 설정

### 1. 사전 요구사항

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (권장) 또는 pip
- Git

### 2. 저장소 클론

```bash
git clone https://github.com/irresi/bl-view-mcp.git
cd bl-view-mcp
```

### 3. 의존성 설치

```bash
# uv 사용 (권장)
make install

# 또는 직접
uv sync --extra agent
```

### 4. 환경 확인

```bash
make check
```

---

## 데이터 준비

### 옵션 1: 미리 패키징된 데이터 다운로드 (빠름) ⚡

```bash
# GitHub Release에서 다운로드 (503개 종목, 49MB)
make download-data
```

**요구사항**: [GitHub CLI](https://cli.github.com/) (`brew install gh`)

### 옵션 2: 직접 다운로드

```bash
# 샘플 데이터 (3개 종목)
make sample

# 또는 S&P 500 전체 (503개 종목, 시간 소요)
make data-snp500
```

### 데이터 위치

- `data/*.parquet` - 개별 종목 데이터
- `data/sp500_tickers.csv` - S&P 500 티커 목록

---

## 개발 워크플로우

### 서버 실행

#### HTTP 모드 (ADK Agent, Web UI)

```bash
# Terminal 1: HTTP 서버 시작
make server-http

# Terminal 2: Web UI 시작 (선택)
make web-ui
```

- HTTP 서버: http://localhost:5000/mcp
- Web UI: http://localhost:8000

**포트 충돌 시**: 자동으로 기존 프로세스를 종료하고 재시작합니다.

#### stdio 모드 (Windsurf, Claude Desktop)

```bash
make server-stdio
```

Windsurf 설정 파일 (`.windsurf/mcp_config.json`):
```json
{
  "mcpServers": {
    "bl-view-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/start_stdio.py"]
    }
  }
}
```

### 개발 명령어

```bash
# 모든 명령어 확인
make help

# 테스트 실행
make test

# Python 캐시 정리
make clean

# 데이터 포함 전체 정리
make clean-all
```

---

## 테스트

### 단위 테스트

```bash
# 빠른 테스트 (직접 호출)
make test-simple

# 또는 직접 실행
uv run python tests/test_simple.py
```

### Agent 테스트 (HTTP 서버 필요)

```bash
# Terminal 1
make server-http

# Terminal 2
make test-agent
```

### 테스트 시나리오 예제

```python
# tests/test_simple.py 참고
from bl_mcp.tools import optimize_portfolio_bl

result = optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    start_date="2023-01-01",
    views={
        "AAPL": {"relative_to": "MSFT", "return": 0.05}
    },
    confidence=0.3
)

assert result["success"] == True
assert "weights" in result
```

---

## 코드 스타일

### Python

- **Type hints**: 모든 함수에 타입 힌트 추가
- **Docstring**: Google 스타일
- **명명 규칙**: snake_case (함수, 변수), PascalCase (클래스)

```python
def calculate_expected_returns(
    tickers: list[str],
    start_date: str,
    end_date: Optional[str] = None,
    method: str = "historical_mean"
) -> dict:
    """
    Calculate expected returns for assets.
    
    Args:
        tickers: List of ticker symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), defaults to most recent
        method: Calculation method ("historical_mean" or "ema")
    
    Returns:
        Dict with success status and expected returns
    """
    # Implementation
```

### 에러 처리

- 명확한 에러 메시지 제공
- `success` 필드로 성공/실패 구분
- 원인과 해결 방법 포함

```python
return {
    "success": False,
    "error": "Insufficient data",
    "message": "At least 60 days of data required. Found: 30 days.",
    "suggestion": "Try a longer date range or different tickers"
}
```

### 반환 형식

모든 도구는 Dict를 반환:

```python
# 성공
{
    "success": True,
    "result": {...},
    "metadata": {...}
}

# 실패
{
    "success": False,
    "error": "ErrorType",
    "message": "Human-readable message"
}
```

---

## Pull Request 가이드

### 1. 브랜치 전략

```bash
# feature 브랜치 생성
git checkout -b feature/your-feature-name

# 또는 bugfix
git checkout -b fix/bug-description
```

### 2. 커밋 메시지

명확하고 간결하게:

```
Add backtest_portfolio tool

- Implement backtest logic using PyPortfolioOpt
- Add unit tests for edge cases
- Update documentation
```

### 3. PR 체크리스트

- [ ] 테스트 통과 (`make test`)
- [ ] Type hints 추가
- [ ] Docstring 작성
- [ ] 관련 문서 업데이트 (README, Memory Bank)
- [ ] 코드 스타일 준수

### 4. PR 설명

```markdown
## 변경 사항
- 새로운 도구/기능 추가
- 버그 수정

## 테스트
- [ ] 단위 테스트 추가
- [ ] 기존 테스트 통과

## 관련 이슈
Closes #123
```

---

## 데이터 공유 (협업자용)

### 데이터 업데이트 시

```bash
# 1. 데이터 수정/추가
make data-snp500

# 2. 압축
make pack-data

# 3. GitHub Release 생성
# https://github.com/irresi/bl-view-mcp/releases/new
# - Tag: data-v1.1 (버전 증가)
# - Upload: data.tar.gz
```

### Makefile 업데이트

`download-data` 타겟의 버전 업데이트:
```makefile
gh release download data-v1.1 -p "data.tar.gz" --clobber
```

---

## 추가 자료

### 프로젝트 문서

- [README.md](README.md) - 프로젝트 개요
- [QUICKSTART.md](QUICKSTART.md) - 5분 시작 가이드
- [TESTING.md](TESTING.md) - 테스트 가이드
- [WINDSURF_SETUP.md](WINDSURF_SETUP.md) - Windsurf 연동

### Memory Bank

프로젝트 컨텍스트와 설계 결정을 기록한 문서들:

- `memory-bank/projectbrief.md` - 프로젝트 목표
- `memory-bank/activeContext.md` - 현재 작업 상태
- `memory-bank/progress.md` - 진행 상황
- `memory-bank/systemPatterns.md` - 아키텍처
- `memory-bank/techContext.md` - 기술 스택

### Reference 자료

- `reference/PyPortfolioOpt/cookbook/2-black-litterman.ipynb` - BL 모델 예제
- `reference/fastmcp/examples/` - FastMCP 사용 예제
- `reference/Idzorek_onBL.pdf` - Black-Litterman 이론

---

## 질문이나 도움이 필요하신가요?

- **Issue**: [GitHub Issues](https://github.com/irresi/bl-view-mcp/issues)
- **Documentation**: 프로젝트 루트의 `*.md` 파일들 참고
- **Memory Bank**: 설계 결정과 컨텍스트 확인

**Happy Contributing! 🚀**
