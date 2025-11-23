# Active Context

## 현재 상태 (2025-11-23)

**Phase**: Phase 1 완료, Phase 2 범위 확정
**초점**: 프로젝트 분리 결정, backtest_portfolio 구현 준비

---

## 핵심 결정 (2025-11-23 저녁)

### 프로젝트 분리

| 프로젝트 | 역할 | 기술 |
|----------|------|------|
| **bl-mcp** (이 프로젝트) | MCP Tool 라이브러리 | FastMCP, PyPortfolioOpt |
| **bl-orchestrator** (별도) | Multi-agent view generation | CrewAI |

### Phase 2 범위 축소

**포함**:
- `backtest_portfolio` - 포트폴리오 백테스팅
- `calculate_hrp_weights` - HRP 최적화 (선택)

**제외** (bl-orchestrator로 이동):
- ~~`generate_views_from_technicals`~~
- ~~`generate_views_from_fundamentals`~~
- ~~`generate_views_from_sentiment`~~
- ~~`get_market_data`~~
- ~~`calculate_factor_scores`~~

### View Generation 전략 변경

**이전 계획** (폐기):
```
기술지표/펀더멘탈 → 규칙 기반 로직 → P, Q, confidence
                   ↑ 자의적, 정당화 어려움
```

**새 접근** (채택):
```
Multi-agent debate → LLM reasoning → P, Q, confidence
                     ↑ LLM이 직접 판단
```

**이유**:
1. "AAPL이 10% 오른다" 같은 절대 뷰는 예측 불가능
2. "AAPL이 MSFT보다 나을 것" 같은 상대 뷰는 LLM 토론으로 정당화 가능
3. 규칙 기반 로직은 자의적 (RSI < 30 → 매수? 왜 30?)

---

## 예상 워크플로우 (Phase 2 완료 후)

```
bl-orchestrator:
1. 데이터 수집 (yfinance, ccxt)
2. Agent Debate (Bull vs Bear vs Moderator)
3. 합의된 Views 출력: {"P": [...], "Q": [...], "confidence": [...]}

bl-mcp:
4. optimize_portfolio_bl(tickers, views=debate_output)
5. backtest_portfolio(tickers, weights=result)
```

---

## GitHub Issue 업데이트

Issue #11에 결정 사항 코멘트 추가됨:
https://github.com/irresi/bl-view-mcp/issues/11#issuecomment-3567495975

---

## 다음 단계

- [ ] `backtest_portfolio` 구현
- [ ] `calculate_hrp_weights` 구현 (선택)
- [ ] bl-orchestrator 프로젝트 생성 (별도)

---

## 참고

- 핵심 컨텍스트: `CLAUDE.md` (Claude Code 자동 로드)
- 상세 히스토리: `memory-bank/progress.md`
