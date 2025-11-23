# Black-Litterman Portfolio Optimization MCP Server

![Claude Desktop Demo](https://raw.githubusercontent.com/irresi/bl-view-mcp/main/docs/image.png)
![Web UI Demo](https://raw.githubusercontent.com/irresi/bl-view-mcp/main/docs/image2.png)

AI 에이전트를 위한 **Black-Litterman 포트폴리오 최적화** MCP 서버입니다.

Claude Desktop, Windsurf IDE, Google ADK Agent 등 MCP를 지원하는 모든 AI 에이전트에서 사용할 수 있습니다.

## 주요 기능

- **포트폴리오 최적화** - Black-Litterman 모델 기반 최적 비중 계산
- **투자자 견해 반영** - "AAPL이 10% 오를 것", "NVDA가 MSFT보다 나을 것" 등
- **백테스팅** - 과거 데이터로 전략 검증
- **다양한 자산** - S&P 500, NASDAQ 100, ETF, 암호화폐 지원

---

## 빠른 시작

### 1. 설치

**PyPI (권장)**:
```bash
pip install black-litterman-mcp
```

**소스에서 설치**:
```bash
git clone https://github.com/irresi/bl-view-mcp.git
cd bl-view-mcp
make install
```

### 2. 데이터 다운로드

```bash
make download-data      # S&P 500 (~500 종목)
```

> ⚠️ **중요**: 서버 시작 전에 데이터를 미리 다운로드하세요. 그렇지 않으면 첫 실행 시 30초 이상 걸릴 수 있습니다.

**추가 데이터셋** (선택):
```bash
make download-nasdaq100 # NASDAQ 100
make download-etf       # ETF (~130 종목)
make download-crypto    # 암호화폐 (100 심볼)
```

### 3. 테스트

```bash
make test-simple
```

---

## 사용 방법

### Claude Desktop / Windsurf IDE

`claude_desktop_config.json` 또는 `.windsurf/mcp_config.json`에 추가:

```json
{
  "mcpServers": {
    "bl-view-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/bl-view-mcp", "run", "bl-view-mcp"]
    }
  }
}
```

그 후 AI에게 요청:

> "AAPL, MSFT, GOOGL로 포트폴리오를 최적화해줘. AAPL이 10% 수익을 낼 것 같아."

### Web UI (테스트용)

```bash
# 터미널 1: MCP 서버
make server-http

# 터미널 2: Web UI
make web-ui
```

브라우저에서 http://localhost:8000 접속

### Docker

```bash
docker build -t bl-mcp .
docker run -p 5000:5000 -v $(pwd)/data:/app/data bl-mcp
```

---

## MCP 도구

### `optimize_portfolio_bl`

Black-Litterman 모델로 최적 포트폴리오 비중을 계산합니다.

```python
optimize_portfolio_bl(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="1Y",
    views={"P": [{"AAPL": 1}], "Q": [0.10]},  # AAPL 10% 수익 예상
    confidence=0.7,
    investment_style="balanced"  # aggressive / balanced / conservative
)
```

**Views 예시**:
```python
# 절대 견해: "AAPL이 10% 오를 것"
views = {"P": [{"AAPL": 1}], "Q": [0.10]}

# 상대 견해: "NVDA가 AAPL보다 20% 더 나을 것"
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
```

### `backtest_portfolio`

포트폴리오 전략을 과거 데이터로 검증합니다.

```python
backtest_portfolio(
    tickers=["AAPL", "MSFT", "GOOGL"],
    weights={"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25},
    period="3Y",
    strategy="passive_rebalance",  # buy_and_hold / passive_rebalance / risk_managed
    benchmark="SPY"
)
```

### `list_available_tickers`

사용 가능한 티커 목록을 조회합니다.

```python
list_available_tickers(search="AAPL")        # 검색
list_available_tickers(dataset="snp500")     # S&P 500만
list_available_tickers(dataset="custom")     # 커스텀 데이터
```

---

## 문서

| 문서 | 설명 |
|------|------|
| [QUICKSTART.md](QUICKSTART.md) | 5분 시작 가이드 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 개발자 가이드 |
| [TESTING.md](TESTING.md) | 테스트 가이드 |
| [docs/WINDSURF_SETUP.md](docs/WINDSURF_SETUP.md) | Windsurf IDE 설정 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 기술 아키텍처 |

---

## 기술 스택

- **MCP 서버**: [FastMCP](https://github.com/jlowin/fastmcp)
- **최적화**: [PyPortfolioOpt](https://github.com/robertmartin8/PyPortfolioOpt)
- **데이터**: yfinance, ccxt (암호화폐)

---

## 라이선스

MIT License - [LICENSE](LICENSE)

---

## 문제 해결

### "Data file not found"
```bash
make download-data
```

### "uv: command not found"
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 더 많은 도움이 필요하면
- [GitHub Issues](https://github.com/irresi/bl-view-mcp/issues)
- [QUICKSTART.md](QUICKSTART.md) 참고
