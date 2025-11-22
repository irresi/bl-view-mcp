# Testing Guide

Black-Litterman MCP Server 테스트 가이드입니다.

## 🚀 빠른 시작

```bash
# 1. 데이터 준비 (자동 다운로드)
make download-data

# 2. 테스트 실행
make test-simple
```

---

## 🧪 테스트 방법

### 방법 1: 직접 테스트 (가장 빠름) ⚡

MCP 서버 없이 tools를 직접 호출합니다.

```bash
make test-simple
# 또는
uv run python tests/test_simple.py
```

**6가지 테스트 시나리오:**
1. Basic Optimization (No Views)
2. Absolute View (AAPL +10%)
3. Relative View (NVDA > AAPL by 20%)
4. NumPy P Format
5. Investment Styles
6. Multiple Views with Per-View Confidence

**직접 호출 예시** (P, Q 형식):
```python
from bl_mcp.tools import optimize_portfolio_bl

# Absolute View
result = optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="1Y",
    views={"P": [{"AAPL": 1}], "Q": [0.10]},
    confidence=0.7
)

# Relative View
result = optimize_portfolio_bl(
    tickers=["NVDA", "AAPL", "MSFT"],
    period="1Y",
    views={"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]},
    confidence=0.85
)
```

---

### 방법 2: ADK Agent 테스트 🤖

```bash
# Terminal 1: MCP 서버 시작
make server-http

# Terminal 2: Agent 테스트
make test-agent
```

---

### 방법 3: Web UI 테스트 🌐

```bash
# Terminal 1: MCP 서버 시작
make server-http

# Terminal 2: Web UI 시작
make web-ui
```

브라우저에서 `http://localhost:8000` 접속

**테스트 프롬프트:**
```
AAPL, MSFT, GOOGL로 포트폴리오를 최적화해줘.
최근 1년 데이터를 사용하고,
AAPL이 10% 수익을 낼 것으로 예상해. 확신도는 70%야.
```

**Web UI 시나리오:**

| 시나리오 | 프롬프트 |
|----------|----------|
| 기본 최적화 | "AAPL, MSFT, GOOGL로 포트폴리오 최적화해줘" |
| Absolute View | "AAPL 10% 수익 예상, 확신도 70%" |
| Relative View | "NVDA가 AAPL보다 20% 더 나을 것 같아" |

---

## ✅ 예상 결과

### 성공 시:
```
✅ Success!

📊 Portfolio Weights:
  AAPL: 33.33%
  MSFT: 33.33%
  GOOGL: 33.33%

📈 Performance:
  Expected Return: 13.46%
  Volatility: 23.20%
  Sharpe Ratio: 0.58
```

---

## 🛠️ 문제 해결

| 에러 | 해결 |
|------|------|
| "Data file not found" | `make download-data` |
| "Module not found" | `uv sync` |
| "Connection refused" | MCP 서버 시작 확인 |

### 서버 연결 실패 시:
```bash
# 포트 확인
lsof -i :5000
lsof -i :8000

# 서버 재시작
make server-http
```

---

## 📚 관련 문서

- [QUICKSTART.md](QUICKSTART.md) - 빠른 시작
- [docs/WINDSURF_SETUP.md](docs/WINDSURF_SETUP.md) - Windsurf 연동
- [CONTRIBUTING.md](CONTRIBUTING.md) - 기여 가이드
