# Active Context

## 현재 상태 (2025-11-24)

**Phase**: Phase 3 개선 완료 (PR #22)
**초점**: 도구 확장, 시각화 힌트, 테스트 강화

---

## Phase 3 개선 사항 (2025-11-24)

### 1. `get_asset_stats` 신규 도구
- 자산별 통계 (가격, 수익률, 변동성, 샤프, 시가총액)
- VaR 95% 및 95th percentile 포함 (EGARCH 기반)
- 상관행렬, 공분산행렬 제공
- `calculate_var_egarch` 도구 기능 통합

### 2. `backtest_portfolio` 확장
- `timeseries`: 월별 샘플링된 포트폴리오 가치
- `drawdown_details`: 최대 낙폭 시작/종료/회복 날짜
- `compare_strategies`: 모든 전략 한 번에 비교
- `include_equal_weight`: 동일비중 포트폴리오 비교
- `timeseries_freq`: daily/weekly/monthly 선택 가능

### 3. `optimize_portfolio_bl` 확장
- `sensitivity_range`: 신뢰도별 민감도 분석
- 예: `[0.3, 0.5, 0.9]` → 각 신뢰도에서 결과 반환

### 4. `_visualization_hint` 추가
- 모든 도구 응답에 시각화 가이드 포함
- LLM이 대시보드를 더 잘 생성하도록 유도
- safety_rules, recommended_charts, scale_guidance 포함

### 5. README Use Cases 추가
- Dashboard 생성 팁 추가
- 실용적인 프롬프트 예시 5개 추가:
  - 기본 최적화 + 시각화
  - 벤치마크 백테스트
  - 전략 비교
  - 상관관계 분석
  - 민감도 분석

---

## MCP Tools (현재 5개)

| Tool | 용도 | 상태 |
|------|------|------|
| `optimize_portfolio_bl` | BL 포트폴리오 최적화 | ✅ 확장됨 |
| `backtest_portfolio` | 포트폴리오 백테스팅 | ✅ 확장됨 |
| `get_asset_stats` | 자산 통계/상관관계 조회 | ✅ 신규 |
| `upload_price_data` | 커스텀 가격 데이터 업로드 | ✅ |
| `list_available_tickers` | 사용 가능 티커 조회 | ✅ |

---

## PR #22 (Closes #17, #18, #19, #20)

**브랜치**: `feat/phase-3-implementation`
**상태**: Open

**포함된 변경**:
- get_asset_stats 신규 도구
- backtest_portfolio 확장 (timeseries, drawdown_details, compare_strategies)
- optimize_portfolio_bl 확장 (sensitivity_range)
- _visualization_hint 모든 도구에 추가
- README Use Cases 섹션 추가
- 백테스트 테스트 5개 추가

---

## 다음 단계

- [ ] PR #22 리뷰 및 머지
- [ ] PyPI v0.3.0 배포
- [ ] `upload_price_data` 통합 (prices + file_path)
- [ ] bl-orchestrator 프로젝트 생성 (별도)

---

## 참고

- 핵심 컨텍스트: `CLAUDE.md` (Claude Code 자동 로드)
- 상세 히스토리: `memory-bank/progress.md`
