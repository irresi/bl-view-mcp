# Progress

## 전체 진행 상황 (2025-11-23)

```
Phase 0: ████████████████████████ 100% ✓ (준비)
Phase 1: ████████████████████████ 100% ✓ (MVP + 간소화)
Phase 2: ████████████████░░░░░░░░  66% (백테스트 완료, HRP 미정)
Phase 3: ████████████████████░░░░  80% (PyPI 배포 완료)
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
| 시가총액 자동 로드 | ✅ yfinance + Parquet 캐시 |

### 인프라

- ✅ FastMCP stdio/HTTP 듀얼 모드
- ✅ 503개 S&P 500 데이터 (Parquet)
- ✅ Docker 지원
- ✅ Makefile 자동화
- ✅ 테스트 시스템

---

## Phase 2: 백테스트 완료 (2025-11-23)

### 포함

- [x] `backtest_portfolio` - 백테스팅 ✅
- [ ] `calculate_hrp_weights` - HRP 최적화 (선택)

### 제외 (bl-orchestrator로 이동)

- ~~`generate_views_from_technicals`~~
- ~~`generate_views_from_fundamentals`~~
- ~~`generate_views_from_sentiment`~~
- ~~`get_market_data`~~
- ~~`calculate_factor_scores`~~

### 프로젝트 분리 결정

| 프로젝트 | 역할 |
|----------|------|
| **bl-mcp** | MCP Tool 라이브러리 (순수) |
| **bl-orchestrator** | Multi-agent view generation (CrewAI) |

---

## Phase 3: PyPI 배포 완료 ✅

### 배포 현황

| 항목 | 상태 |
|------|------|
| PyPI 패키지 | ✅ `black-litterman-mcp` |
| 최신 버전 | v0.2.3 |
| Trusted Publishing | ✅ GitHub Actions |
| Dynamic Versioning | ✅ hatch-vcs (git tags) |

### Claude Desktop 호환성 (v0.2.3)

| 이슈 | 원인 | 해결 |
|------|------|------|
| Read-only filesystem | MCP가 루트에서 실행 | 홈 디렉토리 사용 |
| JSON string parameter | Claude가 dict를 str로 전송 | Union[dict, str] 추가 |

---

## 변경 이력

### 2025-11-23 (심야) - PyPI v0.2.3 배포
- **v0.2.3**: views 파라미터 str 타입 추가
  - Claude Desktop이 JSON object를 문자열로 전송하는 이슈 해결
  - FastMCP + Claude Code 알려진 버그 (anthropics/claude-code#3084)
  - `Union[ViewMatrix, dict, str]` workaround 적용
- **v0.2.2**: 데이터 디렉토리 홈으로 이동
  - `~/.black-litterman/data` 기본 경로
  - `BL_DATA_DIR` 환경변수 오버라이드 지원
  - Claude Desktop read-only 이슈 해결
- **v0.2.1**: backtest_portfolio 추가

### 2025-11-23 (밤) - backtest_portfolio 구현 완료
- **backtest_portfolio MCP Tool 추가**
  - Strategy preset 패턴: buy_and_hold, passive_rebalance, risk_managed
  - Custom config 지원: rebalance_frequency, fees, stop_loss, max_drawdown_limit
  - Performance metrics: CAGR, Sharpe, Sortino, Max Drawdown, Calmar
  - Benchmark comparison: Alpha, Beta, Information Ratio
  - Holding periods tracking (세금 계산용)
- **테스트 추가**: tests/test_backtest.py (13개 테스트 모두 통과)
- **문서 업데이트**: CLAUDE.md, README.md, memory-bank/*

### 2025-11-23 (저녁) - 프로젝트 분리 결정
- **Phase 2 범위 축소**: backtest + HRP만 포함
- **View generation 제외**: Multi-agent debate로 대체 (별도 프로젝트)
- **이유**: 규칙 기반 View 생성은 자의적, LLM reasoning이 더 적합
- **GitHub Issue #11 업데이트**: 결정 사항 문서화

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
