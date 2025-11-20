# Project Brief: Black-Litterman Portfolio Optimization MCP Server

## 프로젝트 목표

베이지안 통계 모델 기반 포트폴리오 최적화 MCP 서버 구축

## 핵심 컨셉

블랙-리터만 모델을 MCP(Model Context Protocol) 서버로 구현하여 AI가 포트폴리오 최적화를 수행할 수 있도록 함

### 베이지안 접근

- **Prior (사전 분포)**: 시가총액 가중 포트폴리오 - 시장의 균형 상태를 반영
- **Likelihood (우도)**: MCP Tools - 사용자/AI가 투자 견해를 입력하여 포트폴리오 업데이트
- **Posterior (사후 분포)**: 최적화된 포트폴리오

## 핵심 요구사항

### 1. MCP Tools 제공

8개의 핵심 도구를 MCP 프로토콜로 노출:

1. `calculate_expected_returns` - 기대수익률 계산
2. `calculate_covariance_matrix` - 공분산 행렬 계산
3. `create_investor_view` - 투자자 견해 생성
4. `optimize_portfolio_bl` - 블랙-리터만 최적화
5. `backtest_portfolio` - 백테스팅
6. `get_market_data` - 시장 데이터 조회
7. `calculate_factor_scores` - 팩터 스코어링
8. `calculate_hrp_weights` - HRP 가중치 계산

### 2. 유연한 전송 방식

- **stdio 모드**: Windsurf, Claude Desktop 등 IDE 통합
- **HTTP 모드**: Google ADK Agent, 웹 서비스 통합

### 3. 모듈화 설계

각 단계(데이터 수집, 모델링, 백테스팅)를 독립적인 Tool로 제공하여 AI가 조합 가능

## 성공 기준

1. ✅ Windsurf에서 MCP 서버로 등록되어 AI가 Tools 사용 가능
2. ✅ 기본 포트폴리오 최적화 시나리오 작동
3. ✅ 백테스팅으로 전략 검증 가능
4. ✅ (선택) ADK Agent로 자동화 워크플로우 구현

## 기술 제약

- Python 3.11+
- FastMCP 2.13.0.1
- PyPortfolioOpt (핵심 최적화 라이브러리)
- 로컬 Parquet 데이터 (yfinance로 수집)

## 비기능 요구사항

- 타입 안전성 (Python type hints)
- 명확한 에러 처리 및 검증
- 각 Tool의 결과는 Dict 형태로 명확히 반환
- 투명성: 중간 결과 모두 반환

## 프로젝트 범위

### In Scope

- 주식, ETF 데이터 (yfinance)
- 기본 블랙-리터만 모델
- 팩터 모델, HRP 통합
- 백테스팅 및 성과 분석

### Out of Scope (현재)

- 실시간 거래 연동
- 프론트엔드 UI
- 채권, 파생상품
- 실시간 데이터 스트리밍

## 차별화 포인트

1. **베이지안 접근**: Prior + Likelihood = Posterior
2. **AI 친화적**: MCP 프로토콜로 AI가 직접 사용
3. **모듈화**: 각 단계를 독립적인 Tool로 제공
4. **유연성**: stdio/HTTP 듀얼 모드
5. **현대적**: FastMCP의 간결함과 타입 안전성
