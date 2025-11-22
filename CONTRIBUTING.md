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
├── server.py         # FastMCP 서버 (@mcp.tool 1개)
├── tools.py          # 핵심 로직 (optimize_portfolio_bl)
└── utils/            # 유틸리티
    ├── data_loader.py
    ├── validators.py
    └── session.py

scripts/              # 데이터 다운로드 스크립트
├── download_data.py
└── download_sp500.py

tests/                # 테스트
├── test_simple.py    # 6개 테스트 시나리오
└── test_agent.py
```

### 구현된 도구 (Phase 1)

**Single Tool 설계** - LLM 토큰 효율성을 위해 1개 Tool로 통합

- `optimize_portfolio_bl` - Black-Litterman 최적화 (유일한 MCP Tool)

---

## 개발 환경 설정

### 1. 사전 요구사항

**로컬 개발:**
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (권장) 또는 pip
- Git

**Docker 사용 (권장):**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 또는 Docker Engine

### 2. 저장소 클론

```bash
git clone https://github.com/irresi/bl-view-mcp.git
cd bl-view-mcp
```

### 3. 개발 환경 선택

#### 옵션 A: Docker 환경 (권장, 크로스 플랫폼) 🐳

**장점:**
- ✅ Windows/macOS/Linux 모두 동일한 환경
- ✅ Python 설치 불필요
- ✅ 의존성 자동 설치
- ✅ 격리된 환경

```bash
# 1. Docker 환경 설정 (최초 1회)
make docker-setup

# 2. 컨테이너 접속
make docker-shell

# 3. 컨테이너 내에서 원하는 명령어 실행
make server-http  # HTTP 서버 시작
make test         # 테스트 실행
make sample       # 데이터 다운로드
# ... 모든 make 명령어 동일하게 작동
```

**정리:**
```bash
# Docker 환경 제거
make docker-clean
```

#### 옵션 B: 로컬 개발 (Python 3.11+ 필요)

```bash
# uv 사용 (권장)
make install

# 또는 직접
uv sync --extra agent
```

**환경 확인:**
```bash
make check
```

---

## 데이터 준비

**참고**: Docker 사용 시 `./data` 폴더가 자동으로 컨테이너와 공유됩니다.

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

**중요**: Docker 환경이든 로컬 환경이든 모든 명령어가 동일합니다!
- Docker 사용 시: `make docker-shell`로 컨테이너 접속 후 사용
- 로컬 사용 시: 바로 사용

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

# Absolute View (AAPL 10% 수익 예상)
result = optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="1Y",
    views={"P": [{"AAPL": 1}], "Q": [0.10]},
    confidence=0.7
)

# Relative View (NVDA가 AAPL보다 20% 아웃퍼폼)
result = optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    period="1Y",
    views={"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]},
    confidence=0.85
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
def optimize_portfolio_bl(
    tickers: list[str],
    period: Optional[str] = None,
    views: Optional[dict] = None,
    confidence: Optional[float | list] = None,
    investment_style: str = "balanced"
) -> dict:
    """
    Optimize portfolio using Black-Litterman model.

    Args:
        tickers: List of ticker symbols (order preserved)
        period: Relative period ("1Y", "3M", etc.)
        views: Views in P, Q format (e.g., {"P": [{"AAPL": 1}], "Q": [0.10]})
        confidence: View confidence (float or list)
        investment_style: "aggressive", "balanced", or "conservative"

    Returns:
        Dict with weights, returns, and performance metrics
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

### 컨텍스트 문서

- `CLAUDE.md` - Claude Code 자동 컨텍스트 (핵심)
- `memory-bank/activeContext.md` - 현재 작업 상태
- `memory-bank/progress.md` - 진행 상황
- `memory-bank/systemPatterns.md` - 아키텍처

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
