# Testing Guide - Quick Start

Black-Litterman MCP Server를 테스트하는 3가지 방법입니다.

## 🚀 1단계: 데이터 준비

```bash
# 테스트 데이터 다운로드 (AAPL, MSFT, GOOGL)
uv run python scripts/download_data.py --tickers AAPL MSFT GOOGL --start 2023-01-01
```

**출력**:
```
Downloading 3 tickers from 2023-01-01 to 2025-11-21
------------------------------------------------------------
AAPL: Saved 725 rows
MSFT: Saved 725 rows
GOOGL: Saved 725 rows
------------------------------------------------------------
Completed: 3/3 successful
```

---

## 🧪 2단계: 테스트 방법 선택

### 방법 1: 직접 테스트 (가장 빠름) ⚡

MCP 서버 없이 tools를 직접 호출합니다.

```bash
uv run python tests/test_simple.py
```

**소요 시간**: ~5초  
**장점**: 빠른 디버깅, 서버 불필요

---

### 방법 2: ADK Agent 테스트 🤖

```bash
# Terminal 1
uv run python start_http.py

# Terminal 2
uv run python tests/test_agent.py
```

**소요 시간**: ~30초  
**장점**: 실제 AI Agent 동작 확인

---

### 방법 3: Web UI 테스트 (가장 직관적) 🌐

```bash
# Terminal 1
uv run python start_http.py

# Terminal 2  
adk web
```

그 다음 브라우저에서 `http://localhost:8000` 접속

**장점**: 대화형 인터페이스, 실제 사용 환경

**테스트 프롬프트**:
```
AAPL, MSFT, GOOGL로 포트폴리오를 최적화해줘.
2023년 1월 1일부터 데이터를 사용하고,
AAPL이 10% 수익을 낼 것으로 예상해. 확신도는 70%야.
```

---

## 📚 상세 가이드

더 자세한 내용은 다음 문서를 참고하세요:

- **tests/README.md**: 전체 테스트 방법
- **tests/ADK_WEB_GUIDE.md**: Web UI 상세 가이드
- **WINDSURF_SETUP.md**: Windsurf IDE 연동

---

## ✅ 예상 결과

### 성공 시:
```
✅ Success!

📊 Portfolio Weights:
  AAPL: 30.71%
  MSFT: 34.64%
  GOOGL: 34.64%

📈 Performance:
  Expected Return: 11.00%
  Volatility: 21.69%
  Sharpe Ratio: 0.51
```

### 실패 시:
- **"Data file not found"**: 데이터 다운로드 필요
- **"Module not found"**: `uv sync` 실행
- **"Connection refused"**: MCP 서버 시작 확인

---

**Happy Testing! 🚀**
