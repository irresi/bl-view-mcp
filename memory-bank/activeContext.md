# Active Context

## 현재 상태 (2025-11-23)

**Phase**: Phase 1 완료 + 시가총액 자동 로드
**초점**: Single Tool 설계, 시가총액 자동화

---

## 최신 변경사항 (2025-11-23 오후)

### 시가총액 자동 로드 구현

**`market_caps` 파라미터 제거** → 자동으로 시가총액 가져옴

```python
# ❌ 이전 (수동)
optimize_portfolio_bl(tickers, market_caps={"AAPL": 3e12, ...})

# ✅ 현재 (자동)
optimize_portfolio_bl(tickers)  # 시가총액 자동 로드
```

**동작 흐름**:
1. `data/market_caps.parquet` 캐시 확인
2. 없으면 yfinance에서 다운로드
3. 성공 시 Parquet에 캐싱
4. 실패 시 equal weight fallback

**변경 파일**:
- `bl_mcp/utils/data_loader.py`: `get_market_caps()` 함수 추가
- `bl_mcp/tools.py`: `market_caps` 파라미터 제거
- `bl_mcp/server.py`: MCP 인터페이스 업데이트

---

## 핵심 아키텍처 (2025-11-23)

### 1. MCP Tool 간소화

| 이전 | 현재 |
|------|------|
| 4개 Tool | **1개 Tool만** |
| `market_caps` 수동 | **자동 로드** |

### 2. Views 형식 (P, Q Only)

```python
views = {"P": [{"AAPL": 1}], "Q": [0.10]}           # Absolute
views = {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}  # Relative
views = {"P": [[1, -1, 0]], "Q": [0.20]}            # NumPy
```

### 3. 시가총액 자동화

```python
# data_loader.py
get_market_caps(tickers)
# 1. Parquet 캐시 → 2. yfinance → 3. equal weight fallback
```

---

## 테스트 결과

```
✅ Basic Optimization (No Views) - 시가총액 기반 가중치
✅ Absolute View (AAPL +10%)
✅ Relative View (NVDA > AAPL 20%)
✅ NumPy P Format
✅ Investment Styles
✅ Multiple Views + Per-View Confidence
```

yfinance에서 시가총액 자동 로드 확인:
```
📥 Fetching market caps from yfinance: ['AAPL', 'MSFT', 'GOOGL']
📥 Fetching market caps from yfinance: ['NVDA']  # 캐시에 없는 것만
```

---

## 알려진 이슈

- **SPY.parquet 없음**: `investment_style` 효과 없음 (fallback δ=2.5)

---

## 다음 단계

- [ ] SPY 데이터 다운로드
- [ ] README.md 업데이트
- [x] ~~시가총액 자동 로드~~ ✅

---

## 참고

- 핵심 컨텍스트: `CLAUDE.md` (Claude Code 자동 로드)
- 상세 히스토리: `memory-bank/progress.md`
