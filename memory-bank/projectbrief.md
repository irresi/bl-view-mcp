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

### 1. MCP Tool 제공

**Single Tool** 아키텍처로 간소화:

`optimize_portfolio_bl` - 블랙-리터만 포트폴리오 최적화

**내부 처리:**
- 데이터 수집 (yfinance)
- 기대수익률 계산 (히스토리컬)
- 공분산 행렬 계산 (Ledoit-Wolf)
- 투자자 견해 (P, Q 형식)
- Idzorek Confidence → Omega 역산
- 최적화 수행

### 2. 유연한 전송 방식

- **stdio 모드**: Windsurf, Claude Desktop 등 IDE 통합
- **HTTP 모드**: Google ADK Agent, 웹 서비스 통합

### 3. 통합 설계

모든 단계를 하나의 Tool에 통합하여 AI가 단일 호출로 완료:
- 복잡한 Tool 조합 불필요
- 일관된 인터페이스
- 간결한 프롬프트

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
