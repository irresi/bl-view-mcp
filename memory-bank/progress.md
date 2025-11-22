# Progress

## 전체 진행 상황 (2025-11-23)

```
Phase 0: ████████████████████████ 100% ✓ (준비)
Phase 1: ████████████████████████ 100% ✓ (MVP + 간소화)
Phase 2: ░░░░░░░░░░░░░░░░░░░░░░░░   0% (백테스트)
```

---

## Phase 1: 완료 ✅

### 핵심 구현

| 항목 | 상태 |
|------|------|
| `optimize_portfolio_bl` | ✅ 유일한 MCP Tool |
| P, Q 형식 Views | ✅ Absolute + Relative |
| Idzorek confidence | ✅ float/list |
| Investment Style | ✅ aggressive/balanced/conservative |
| 데이터 자동 다운로드 | ✅ GitHub Release |

### 인프라

- ✅ FastMCP stdio/HTTP 듀얼 모드
- ✅ 503개 S&P 500 데이터 (Parquet)
- ✅ Docker 지원
- ✅ Makefile 자동화
- ✅ 테스트 시스템

---

## Phase 2: 대기 중

- [ ] `backtest_portfolio` - 백테스팅
- [ ] `calculate_hrp_weights` - HRP 최적화
- [ ] 한국 주식 지원 (pykrx)

---

## Phase 3: 계획

- [ ] 암호화폐 지원 (ccxt)
- [ ] PyPI 배포

---

## 변경 이력

### 2025-11-23 (오후)
- **시가총액 자동 로드 구현**
  - `market_caps` 파라미터 제거
  - `get_market_caps()` 함수 추가 (data_loader.py)
  - Parquet 캐시 → yfinance → equal weight fallback
  - 한 번 가져온 시가총액은 자동 캐싱

### 2025-11-23 (오전)
- MCP Tool 간소화: 4개 → 1개 (`optimize_portfolio_bl`)
- Views 형식 통일: P, Q 형식만 지원
- Confidence 단순화: float/list만 지원
- Ticker 정렬 제거 (사용자 순서 유지)
- `CLAUDE.md` 생성 (자동 컨텍스트)
- memory-bank 정리

### 2025-11-22
- P, Q 전용 API (Breaking Change)
- Relative View 지원
- Period 파라미터 추가
- Idzorek 구현 검증

### 2025-11-21
- Phase 1 MVP 완료
- S&P 500 데이터 다운로드 (503개)
- GitHub Release 배포
- Docker 환경 구축

### 2025-11-20
- 프로젝트 시작
- Memory Bank 초기화
- FastMCP + PyPortfolioOpt 선택
