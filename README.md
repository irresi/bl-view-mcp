# Black-Litterman Portfolio Optimization MCP Server

![Claude Desktop Demo](https://raw.githubusercontent.com/irresi/bl-view-mcp/main/docs/image.png)
![Web UI Demo](https://raw.githubusercontent.com/irresi/bl-view-mcp/main/docs/image2.png)

AI 에이전트를 위한 **Black-Litterman 포트폴리오 최적화** MCP 서버입니다.

Claude Desktop, Windsurf IDE, Google ADK Agent 등 MCP를 지원하는 모든 AI 에이전트에서 사용할 수 있습니다.

## 주요 기능

- **포트폴리오 최적화** - Black-Litterman 모델 기반 최적 비중 계산
- **투자자 견해 반영** - "AAPL이 10% 오를 것", "NVDA가 MSFT보다 나을 것" 등
- **백테스팅** - 과거 데이터로 전략 검증
- **VaR 경고** - EGARCH 모델로 낙관적 예측 경고
- **다양한 자산** - S&P 500, NASDAQ 100, ETF, 암호화폐, 커스텀 데이터 지원

---

## 빠른 시작 (Claude Desktop)

### 1단계: uvx 경로 확인

터미널에서 실행:
```bash
which uvx
# 출력 예시: /Users/USERNAME/.local/bin/uvx
```

> uvx가 없으면 먼저 설치: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 2단계: Claude Desktop 설정

설정 파일 위치:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

파일 내용 (경로를 본인의 uvx 경로로 변경):

```json
{
  "mcpServers": {
    "black-litterman": {
      "command": "/Users/USERNAME/.local/bin/uvx",
      "args": ["black-litterman-mcp"]
    }
  }
}
```

### 3단계: Claude Desktop 재시작

**Cmd+Q** (macOS) 또는 완전 종료 후 재시작

### 4단계: 사용

Claude에게 요청:

> "AAPL, MSFT, GOOGL로 포트폴리오를 최적화해줘. AAPL이 10% 수익을 낼 것 같아."

---

## 다른 설치 방법

### Windsurf IDE

`.windsurf/mcp_config.json`:
```json
{
  "mcpServers": {
    "black-litterman": {
      "command": "/Users/USERNAME/.local/bin/uvx",
      "args": ["black-litterman-mcp"]
    }
  }
}
```

### 소스에서 설치 (개발자용)

```bash
git clone https://github.com/irresi/bl-view-mcp.git
cd bl-view-mcp
make install
make download-data  # S&P 500 데이터
make test-simple
```

### Docker

```bash
docker build -t bl-mcp .
docker run -p 5000:5000 -v $(pwd)/data:/app/data bl-mcp
```

### Web UI (테스트용)

```bash
# 터미널 1: MCP 서버
make server-http

# 터미널 2: Web UI
make web-ui
```

브라우저에서 http://localhost:8000 접속

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

**VaR 경고**: 40%를 초과하는 수익률 예측 시 자동으로 EGARCH 기반 VaR 분석 결과를 `warnings` 필드에 포함합니다.

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

### `calculate_var_egarch`

EGARCH(1,1) 모델로 개별 종목의 VaR을 계산합니다.

```python
calculate_var_egarch(
    ticker="NVDA",
    period="3Y",
    confidence_level=0.95
)
```

### `upload_price_data`

외부 데이터(한국 주식, 커스텀 자산 등)를 업로드합니다.

```python
upload_price_data(
    ticker="005930.KS",  # 삼성전자
    prices=[
        {"date": "2024-01-02", "close": 78000.0},
        {"date": "2024-01-03", "close": 78500.0},
        ...
    ],
    source="pykrx"
)
```

### `upload_price_data_from_file`

CSV/Parquet 파일에서 가격 데이터를 로드합니다.

```python
upload_price_data_from_file(
    ticker="KOSPI",
    file_path="/path/to/kospi.csv",
    date_column="Date",
    close_column="Close"
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
- **리스크 모델**: [arch](https://github.com/bashtage/arch) (EGARCH)
- **데이터**: yfinance, ccxt (암호화폐)

---

## 라이선스

MIT License - [LICENSE](LICENSE)

---

## 문제 해결

### "spawn uvx ENOENT" / "uv binary not found"

Claude Desktop은 시스템 PATH를 인식하지 못할 수 있습니다. **절대 경로**를 사용하세요:

```bash
which uvx
# 출력된 경로를 config에 사용
```

### "Data file not found"

소스 설치 시:
```bash
make download-data
```

PyPI 설치 시 첫 실행에서 자동 다운로드됩니다 (30초 소요).

### "uv: command not found"

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 더 많은 도움이 필요하면

- [GitHub Issues](https://github.com/irresi/bl-view-mcp/issues)
- [QUICKSTART.md](QUICKSTART.md) 참고
