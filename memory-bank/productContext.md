# Product Context

## 왜 이 프로젝트가 필요한가?

### 문제 정의

1. **기존 포트폴리오 최적화의 한계**
   - Mean-Variance 최적화는 입력에 민감하여 불안정
   - 극단적인 포지션을 제안하는 경향
   - 투자자의 견해를 반영하기 어려움

2. **AI와 금융 분석의 간극**
   - AI가 금융 분석을 수행하려면 복잡한 라이브러리를 직접 다뤄야 함
   - 각 단계마다 코드를 작성해야 하는 번거로움
   - 재사용 가능한 모듈이 부족

### 블랙-리터만 모델의 장점

1. **베이지안 접근**: Prior(시장 균형) + 투자자 견해 = 안정적인 포트폴리오
2. **견해 통합**: 확신도를 수치화하여 정량적으로 반영
3. **시장 중립**: 견해가 없으면 시가총액 가중 포트폴리오로 회귀

### MCP 프로토콜의 가치

- AI가 **도구**로서 금융 분석 수행
- 복잡한 계산은 서버가 처리, AI는 의사결정에 집중
- 재사용 가능하고 확장 가능한 아키텍처

## 사용자 경험 목표

### Primary User: AI Agent (Windsurf, Claude)

**워크플로우:**

1. 사용자: "AAPL, MSFT, GOOGL로 포트폴리오를 최적화해줘"
2. AI가 자동으로:
   - 데이터 조회 (`get_market_data`)
   - 기대수익률 계산 (`calculate_expected_returns`)
   - 공분산 행렬 계산 (`calculate_covariance_matrix`)
   - 최적화 수행 (`optimize_portfolio_bl`)
   - 결과 설명 및 시각화

**기대 효과:**
- 사용자는 금융 지식만 있으면 됨 (코딩 불필요)
- AI가 복잡한 계산을 대신 수행
- 반복 가능한 분석 워크플로우

### Secondary User: 개발자 (ADK Agent)

**워크플로우:**

1. HTTP 서버 실행
2. ADK Agent로 자동화 시스템 구축
3. 정기적 리밸런싱, 알림 등 프로덕션 워크플로우

## 핵심 기능

### 필수 기능 (Phase 1)

- [x] 데이터 수집 (yfinance → Parquet)
- [ ] 기대수익률 계산 (히스토리컬, CAPM)
- [ ] 공분산 행렬 계산 (샘플, Ledoit-Wolf)
- [ ] 투자자 견해 생성 (P, Q, Omega 자동 계산)
- [ ] 블랙-리터만 최적화 (시가총액 Prior)

### 중요 기능 (Phase 2)

- [ ] 백테스팅 (리밸런싱, 성과 지표)
- [ ] 팩터 스코어링 (value, growth, momentum 등)
- [ ] HRP 가중치 계산
- [ ] 시장 데이터 조회 (펀더멘탈 포함)

### 선택 기능 (Phase 3-4)

- [ ] 한국 주식 지원 (pykrx)
- [ ] 암호화폐 지원 (ccxt)
- [ ] ADK Agent 통합
- [ ] 멀티 에이전트 시스템

## 사용 시나리오

### 시나리오 1: 기본 포트폴리오 최적화

```
사용자: "AAPL, MSFT, GOOGL, AMZN으로 포트폴리오를 최적화해줘. 
        최근 1년 데이터를 사용하고, AAPL이 MSFT보다 5% 높을 것으로 예상해."

AI 실행:
1. get_market_data(["AAPL", "MSFT", "GOOGL", "AMZN"], lookback_days=365)
2. calculate_expected_returns(..., method="historical_mean")
3. calculate_covariance_matrix(..., method="ledoit_wolf")
4. create_investor_view(view_dict={"AAPL": 1, "MSFT": -1}, expected_return=0.05, confidence=0.7)
5. optimize_portfolio_bl(prior_type="market_cap", views=[view])

결과: 최적 가중치 + 예상 수익률 + 샤프 비율
```

### 시나리오 2: 팩터 기반 전략

```
사용자: "S&P 500에서 가치주와 모멘텀이 강한 상위 20개 종목으로 포트폴리오 구성해줘."

AI 실행:
1. calculate_factor_scores(sp500_tickers, factors=["value", "momentum"])
2. 상위 20개 선택
3. optimize_portfolio_bl(prior_type="equal_weight")
4. backtest_portfolio(start_date="2020-01-01")

결과: 포트폴리오 + 백테스팅 결과 (샤프, 최대 낙폭 등)
```

### 시나리오 3: HRP + 블랙-리터만

```
사용자: "ETF로 분산 투자하고 싶어. 저변동성 자산을 선호해."

AI 실행:
1. calculate_hrp_weights(etf_tickers, lookback_days=1095)  # 3년
2. create_investor_view("저변동성 ETF가 5% 더 높을 것")
3. optimize_portfolio_bl(prior_type="hrp", prior_weights=hrp_weights)

결과: HRP 기반 + 견해 반영된 최적 포트폴리오
```

## 제품 철학

1. **투명성**: 모든 중간 결과를 명확히 반환
2. **모듈성**: 각 도구는 독립적으로 사용 가능
3. **유연성**: stdio와 HTTP 모두 지원
4. **안정성**: 입력 검증, 에러 처리 철저
5. **확장성**: 새로운 자산군, 모델 추가 용이

## 성공 측정

1. **기능적**: 모든 시나리오가 작동
2. **성능**: 각 Tool이 10초 이내 응답
3. **사용성**: AI가 자연어로 복잡한 분석 수행
4. **신뢰성**: 에러 발생 시 명확한 메시지 반환
