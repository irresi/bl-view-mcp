# Progress

## 전체 진행 상황

**현재 Phase**: Phase 1 완료 ✅ + 검증 및 최적화 완료 ✅
**완료율**: 80% (MVP + 개발 환경 + MCP 배포 + Idzorek 검증 + 프롬프트 최적화!)

```
[████████████████████░░░░░░░░░░░] 80%

Phase 0: ████████████████████████ 100% ✓ (준비)
Phase 1: ████████████████████████ 100% ✓ (MVP + MCP 배포 + API 검증 완료!)
  └─ Idzorek 검증: ████████████ 100% ✓
  └─ LLM 최적화:   ████████████ 100% ✓
Phase 2: ░░░░░░░░░░░░░░░░░░░░░░░░   0% (백테스트)
Phase 3: ░░░░░░░░░░░░░░░░░░░░░░░░   0% (데이터 확장)
Phase 4: ░░░░░░░░░░░░░░░░░░░░░░░░   0% (배포)
```

## Phase 0: 준비 단계 

**목표**: 프로젝트 구상 및 계획 수립

**상태**: 완료

### 완료된 작업

- [x] README.md 작성 및 수정
  - 블랙-리터만 모델 개념 정리
  - 8개 MCP Tools 정의
  - FastMCP 기반 구조 결정
  - stdio/HTTP 듀얼 모드 설계
  - Phase 1~4 단계별 계획 수립

- [x] Memory Bank 초기화
  - [x] `projectbrief.md`: 프로젝트 목표, 요구사항
  - [x] `productContext.md`: 사용자 경험, 시나리오
  - [x] `systemPatterns.md`: 아키텍처, 설계 패턴
  - [x] `techContext.md`: 기술 스택, 개발 환경
  - [x] `activeContext.md`: 현재 초점
  - [x] `progress.md`: 현재 문서

- [x] Reference 자료 정리 및 최적화
  - [x] `reference/` 폴더 생성
  - [x] `fastmcp/`, `PyPortfolioOpt/`, `9_AGENT_PROTOCOL/` 이동
  - [x] 불필요한 파일 제거 (693MB → 11.6MB, 98% 감소)
    - `.git/` (35MB), `tests/` (4.3MB), `docs/` (9.5MB), `.venv/` (630MB) 제거
    - 핵심 파일만 유지: src, examples, pypfopt, cookbook
  - [x] `reference/README.md` 작성 - 상세 구현 가이드
    - FastMCP 사용 예제 및 패턴
    - PyPortfolioOpt API 상세 (cookbook 2-black-litterman.ipynb)
    - ADK Agent 패턴 (9_AGENT_PROTOCOL)
    - 우리 프로젝트 적용 방법
  - [x] `.gitignore` 업데이트 (소스 코드만 제외, README는 Git 추적)
  - [x] `cleanup_reference.sh` 스크립트 작성

### 핵심 결정사항

1. **FastMCP 채택**: 간결성, stdio/HTTP 듀얼 모드
2. **PyPortfolioOpt 사용**: 업계 표준 라이브러리
3. **모듈형 설계**: tools.py (로직) + server.py (MCP 래퍼)
4. **단계적 접근**: Phase 1 MVP → Phase 2-3 확장 → Phase 4 자동화
5. **Reference 폴더 분리**: 참고 자료는 별도 관리, Git 제외

---

## Phase 1: MCP 서버 MVP (4개 핵심 Tools)

**목표**: FastMCP를 사용하여 PyPortfolioOpt를 MCP Tools로 노출

**상태**: ✅ **완료 + 검증 및 최적화 완료** (2025-11-22)

**실제 완료일**: 
- Phase 1 구현: 2025-11-21 (1일)
- API 개선: 2025-11-22 (period 파라미터)
- Idzorek 검증 및 최적화: 2025-11-22 (1일)

### 완료된 작업록

#### 1. 프로젝트 설정 (0/3)

- [x] `pyproject.toml` 작성
  - [x] 기본 의존성 (fastmcp, pypfopt, pandas, numpy, yfinance)
  - [x] 선택적 의존성 (agent, dev, backtest)
  - [x] Python 버전 명시 (>=3.11)
  - [ ] 선택적 의존성 (agent, dev, backtest)
  - [ ] Python 버전 명시 (>=3.11)

- [ ] 패키지 구조 생성
  ```
  bl_mcp/
  ├── __init__.py
  ├── server.py
  ├── tools.py
  └── utils/
      ├── __init__.py
      ├── data_loader.py
      └── validators.py
  ```

- [ ] 의존성 설치
  - [ ] `uv sync` 또는 `pip install -e .`
  - [ ] 설치 확인 (`python -c "import fastmcp; import pypfopt"`)

#### 2. 데이터 인프라 (0/4)

- [ ] `bl_mcp/utils/data_loader.py` 구현
  - [ ] `load_prices()`: Parquet → DataFrame
  - [ ] 날짜 범위 필터링
  - [ ] 결측치 처리
  - [ ] 수익률 계산 유틸리티

- [ ] `bl_mcp/utils/validators.py` 구현
  - [ ] `validate_tickers()`: 티커 유효성
  - [ ] `validate_date_range()`: 날짜 범위 검증
  - [ ] `validate_data_sufficiency()`: 최소 데이터 확인
  - [ ] `validate_covariance_matrix()`: singular 체크

- [ ] 기존 데이터 확인
  - [ ] `data/` 디렉토리 존재 여부
  - [ ] Parquet 파일 확인
  - [ ] 필요 시 `collect_ohlcv.py` 실행

- [ ] 테스트
  - [ ] 샘플 데이터로 로드 테스트
  - [ ] 검증 함수 단위 테스트

#### 3. 데이터 파이프라인 ✅

   - [x] `scripts/download_data.py` 구현 (yfinance → Parquet, 개별 종목용)
   - [x] `scripts/download_sp500.py` 구현 (S&P 500 전체 503개 종목)
   - [x] `bl_mcp/utils/session.py` 구현 (HTTP 세션 관리)
     - 12개 랜덤 User-Agent로 차단 회피
     - Retry 로직 내장 (429, 500, 502, 503, 504)
     - Connection pooling 최적화
     - MCP 서버 안전 설계 (여러 사용자 동시 사용)
   - [x] Wikipedia에서 S&P 500 티커 자동 수집 (Session 사용)
   - [x] 증분 업데이트 로직 (Incremental update)
   - [x] 상장일부터 전체 히스토리 다운로드 (--start None)
   - [x] Success/Skip/Failed 상태 명확히 구분
   - [x] 섹터 정보 CSV 저장 (`data/sp500_tickers.csv`)
   - [x] **503개 종목 모두 다운로드 완료!** (100% 성공)
     - 평균 ~30년 히스토리 데이터
     - 총 503개 Parquet 파일
     - 실패 0개

#### 4. 핵심 Tools 로직 ✅

- [ ] `bl_mcp/tools.py` 구현
  
  - [ ] **Tool 1.1**: `calculate_expected_returns`
    - 입력 검증
    - 데이터 로드
    - PyPortfolioOpt.expected_returns 호출
    - Dict 반환 (`{"success": True, "expected_returns": {...}, ...}`)
  
  - [ ] **Tool 1.2**: `calculate_covariance_matrix`
    - 입력 검증
    - 데이터 로드
    - PyPortfolioOpt.risk_models 호출
    - Dict 반환
  
  - [ ] **Tool 1.3**: `create_investor_view`
    - view_dict → P, Q, Omega 변환
    - confidence 기반 Omega 계산
    - Dict 반환
  
  - [ ] **Tool 1.4**: `optimize_portfolio_bl`
    - 입력 검증 (Tool 1.1, 1.2의 출력 형식)
    - Prior 계산 (market_cap weighted)
    - BlackLittermanModel 생성
    - 최적화 수행
    - Dict 반환 (가중치, 수익률, 샤프 등)

#### 4. FastMCP 서버 (0/2)

- [ ] `bl_mcp/server.py` 구현
  - [ ] FastMCP 초기화
  - [ ] 4개 Tool `@mcp.tool` 데코레이터로 등록
  - [ ] tools.py 함수 호출 (thin wrapper)
  - [ ] Docstring 작성 (AI가 이해할 수 있도록)

- [ ] 실행 스크립트
  - [ ] `start_stdio.py`: stdio 모드
  - [ ] `start_http.py`: HTTP 모드

#### 5. Windsurf 연동 (0/3)

- [ ] MCP 설정 파일 작성
  - [ ] `.windsurf/mcp_config.json` 생성
  - [ ] 절대 경로로 `start_stdio.py` 지정

- [ ] Windsurf 재시작 및 확인
  - [ ] MCP 서버 등록 확인
  - [ ] Tools 목록 표시 확인

- [ ] 기본 테스트
  - [ ] "사용 가능한 도구 목록 보여줘"
  - [ ] 각 Tool 설명 확인

#### 6. 시나리오 1 검증 (0/1)

- [ ] **시나리오 1: 기본 포트폴리오 최적화**
  
  테스트 프롬프트:
  ```
  "AAPL, MSFT, GOOGL로 구성된 포트폴리오를 최적화해줘.
   최근 1년 데이터를 사용하고, 시가총액 가중 prior를 적용해.
   AAPL이 MSFT보다 5% 더 높은 수익을 낼 것으로 예상해."
  ```
  
  기대 결과:
  - AI가 자동으로 Tool 1.1, 1.2, 1.3, 1.4 순차 호출
  - 각 단계의 결과가 명확히 표시
  - 최종 포트폴리오 가중치 제시
  - 예상 수익률, 변동성, 샤프 비율 제공

### 성공 기준

- ✅ Windsurf에서 4개 Tool 모두 인식
- ✅ 시나리오 1 완전히 작동
- ✅ 결과가 합리적 (음수 가중치 없음, 합이 1)
- ✅ 에러 발생 시 명확한 메시지

### 예상 이슈 및 대응

| 이슈 | 대응 |
|------|------|
| 데이터 부족 | 최소 60일 데이터 요구, 명확한 에러 메시지 |
| 공분산 singular | Ledoit-Wolf 사용, 더 많은 데이터 요청 |
| 티커 오류 | yfinance 검증, 지원되는 티커 목록 제공 |
| FastMCP 연동 실패 | 로그 확인, stdio vs HTTP 모드 전환 |

### 개발 워크플로우 개선 (2025-11-21 추가) ✅

#### 7. Makefile 개선 및 데이터 공유 시스템

- [x] **포트 충돌 자동 해결**
  - [x] `server-http`: 5000번 포트 자동 kill
  - [x] `web-ui`: 8000번 포트 자동 kill
  - [x] `lsof -ti:PORT | xargs kill -9` 패턴 적용

- [x] **명령어 네이밍 개선**
  - [x] `data` → `sample` (샘플 3개)
  - [x] `data-full` 제거
  - [x] `data-snp500` 추가 (S&P 500 전체 503개)
  - [x] `.PHONY` 정리 및 help 업데이트

- [x] **데이터 공유 시스템 (GitHub Release)**
  - [x] `pack-data`: data 폴더 압축 (data.tar.gz, 49MB)
  - [x] `download-data`: GitHub Release에서 다운로드
  - [x] GitHub CLI (`gh`) 사용
  - [x] `--clobber` 옵션으로 덮어쓰기
  - [x] Release 생성: `data-v1.0` (48.51 MB)
  - [x] 다운로드 테스트 완료 (503개 파일 복원)

- [x] **저장소 정리**
  - [x] 저장소 이름 변경: `bl-view-mcp`
  - [x] git remote 업데이트
  - [x] `.gitignore`에 `data.tar.gz` 추가
  - [x] 강제 push로 이력 동기화

- [x] **협업 워크플로우 확립**
  - [x] 데이터 제공자: `make pack-data` + Release 업로드
  - [x] 협업자: `make download-data` (한 줄 완료)
  - [x] 장점: 빠름, 일관성, 압축 (S3 이전 전 임시 솔루션)

#### 8. 협업 인프라 구축 ✅

- [x] **CONTRIBUTING.md 작성**
  - [x] 프로젝트 개요 및 구조 설명
  - [x] 개발 환경 설정 (Docker/로컬)
  - [x] 데이터 준비 가이드
  - [x] 개발 워크플로우 문서화
  - [x] 테스트 가이드 및 예제
  - [x] 코드 스타일 및 PR 가이드라인

- [x] **Docker 환경 구축** 🐳
  - [x] `Dockerfile` 작성 (Python 3.11 + uv via pip)
    - [x] build-essential 추가 (gcc 등 빌드 도구)
    - [x] README.md 명시적 복사
  - [x] ~~`docker-compose.yml`~~ → **제거** (불필요한 복잡성)
  - [x] `.dockerignore` 최적화
  - [x] 크로스 플랫폼 지원 (Windows/macOS/Linux)

- [x] **Makefile Docker 통합**
  - [x] `docker run` 직접 사용 (docker-compose 제거)
  - [x] **관심사 분리**:
    - [x] `docker-setup`: 환경 설정만
    - [x] 서버 실행: 사용자가 `make server-http` 직접 실행
  - [x] `--network host` 사용 (포트 충돌 방지)
  - [x] 전체 프로젝트 마운트
  - [x] `docker-shell`: 컨테이너 접속
  - [x] `docker-clean`: 환경 제거
  - [x] 단순화: Makefile 1개로 모든 것 제어

#### 9. MCP 서버 배포 준비 ✅

- [x] **자동 데이터 다운로드**
  - [x] `bl_mcp/utils/data_loader.py`에 `ensure_data_available()` 추가
  - [x] GitHub Release에서 자동 다운로드 (data-v1.0)
  - [x] 첫 실행 시 자동으로 data.tar.gz (49MB) 다운로드
  - [x] tarfile 압축 해제 자동화
  - [x] 로컬 캐싱 (data/ 폴더 존재 시 스킵)
  - [x] urllib.request.urlretrieve 사용 (표준 라이브러리)

- [x] **Repository Public 전환**
  - [x] Private → Public 변경
  - [x] GitHub Release 공개 접근 가능
  - [x] data-v1.0 Release 재생성 (올바른 tar 구조)

- [x] **문서 업데이트**
  - [x] README.md에 자동 다운로드 안내
  - [x] QUICKSTART.md 업데이트
  - [x] "데이터 다운로드 (자동)" 강조

- [x] **테스트 완료**
  - [x] 데이터 없는 상태에서 자동 다운로드 확인
  - [x] 503개 파일 다운로드 성공
  - [x] 모든 테스트 통과

#### 10. API 개선 - Period 파라미터 ✅

- [x] **날짜 범위 처리 개선** (2025-11-22)
  - [x] `period` 파라미터 추가 (상대 기간 지원)
  - [x] 상호 배타적 파라미터 패턴 (period vs start_date)
  - [x] LLM 친화적 docstring 개선
  - [x] Phase 1 Tools에 모두 적용:
    - [x] `calculate_expected_returns`
    - [x] `calculate_covariance_matrix`
    - [x] `optimize_portfolio_bl`

#### 11. Idzorek 구현 검증 및 개선 ✅

- [x] **심층 검증** (2025-11-22)
  - [x] Idzorek 방식 올바른 사용 확인 (`omega="idzorek"`)
  - [x] server.py ↔ tools.py 시그니처 일치 검증
  - [x] PyPortfolioOpt BlackLittermanModel 정확한 활용 확인
  - [x] Absolute View 완벽 지원 검증
  - [x] Parameter validation 강화

- [x] **Per-View Confidence 지원 추가** 🆕
  - [x] 단일 confidence 지원: `confidence=0.7`
  - [x] View별 confidence 지원: `confidence={"AAPL": 0.9, "MSFT": 0.6}`
  - [x] Dict confidence validation (누락된 view 감지)
  - [x] Type hint 정확화 (`Optional[float | dict]`)
  - [x] Docstring 업데이트 (server.py, tools.py)
  - [x] View_confidences 리스트 빌드 로직 구현

- [x] **테스트 시스템 구축**
  - [x] `tests/test_idzorek_implementation.py` 작성
  - [x] 6개 테스트 시나리오 구현
  - [x] 모든 테스트 통과 (6/6)
  - [x] Makefile에 `test-idzorek` 타겟 추가

- [x] **검증 문서 작성**
  - [x] `docs/IDZOREK_VERIFICATION.md` 작성
  - [x] 검증 결과 완전 문서화
  - [x] 사용 예시 및 권장사항 포함
  - [x] LLM 호출 가능성 확인

- [x] **Parameter Swap 버그 수정**
  - [x] server.py에 `period` 파라미터 누락 발견
  - [x] Positional arguments 매핑 오류 해결
  - [x] Keyword arguments 사용으로 안전성 확보
  - [x] Debug logging 추가 (parameter 추적)
  - [x] 자동 swap 감지 및 복구 로직 추가

#### 12. Agent Prompt 최적화 ✅

- [x] **프롬프트 대폭 간소화** (2025-11-22)
  - [x] **267줄 → 72줄 (73% 감소)**
  - [x] 핵심만 남기고 중복 제거
  - [x] LLM 집중도 향상
  - [x] 토큰 비용 ~70% 절감

- [x] **구조 개선**
  - [x] 타입 규칙 (4줄)
  - [x] 가장 흔한 실수 (2개만)
  - [x] 자연어 변환 (간결하게)
  - [x] 1개의 완벽한 예시

- [x] **제거한 것**
  - [x] 중복된 파라미터 설명
  - [x] 너무 많은 예시 (8개 → 1개)
  - [x] 장황한 이론 설명
  - [x] 중복된 올바른/잘못된 예시들

- [x] **핵심 메시지 강조**
  - [x] `views = 딕셔너리` (어떤 종목이 얼마?)
  - [x] `confidence = 숫자` (얼마나 확신?)
  - [x] `period` 우선 사용
  - [x] 확신도 스케일 간결하게
    - [x] `calculate_covariance_matrix`
    - [x] `optimize_portfolio_bl`

- [x] **validators.py 확장**
  - [x] `parse_period()`: "1Y", "3M" 등 파싱
  - [x] `resolve_date_range()`: period vs absolute dates 해결
  - [x] 기본값 "1Y" (1년) 적용
  - [x] 상호 배타성 경고 메커니즘

- [x] **지원 형식**
  - [x] Days: "1D", "7D"
  - [x] Weeks: "1W", "4W"
  - [x] Months: "1M", "3M", "6M"
  - [x] Years: "1Y", "2Y", "5Y"

- [x] **설계 문서화**
  - [x] systemPatterns.md 업데이트 (날짜 범위 처리 패턴)
  - [x] activeContext.md 업데이트 (최근 변경사항)
  - [x] 설계 결정 이유 명시 (통합 vs 분리 방식)

---

## Phase 2: 기능 확장

**목표**: 백테스팅 및 전략 다각화

**상태**: ⏸️ 대기 (Phase 1 완료 후)

**예상 소요 시간**: 3-4일

### 작업 목록 (간략)

- [ ] Tool 1.5: `backtest_portfolio` (empyrical)
- [ ] Tool 1.6: `get_market_data`
- [ ] Tool 1.7: `calculate_factor_scores`
- [ ] Tool 1.8: `calculate_hrp_weights`
- [ ] Resources 구현 (선택사항)
- [ ] 시나리오 2, 3 검증

---

## Phase 3: 데이터 확장

**목표**: 한국 주식, 암호화폐 지원

**상태**: ⏸️ 대기 (Phase 2 완료 후)

**예상 소요 시간**: 2-3일

### 작업 목록 (간략)

- [ ] pykrx 통합 (한국 주식)
- [ ] ccxt 통합 (암호화폐)
- [ ] 데이터 소스별 분기 처리
- [ ] PyPI 배포 준비

---

## Phase 4: ADK Agent 통합

**목표**: Gemini 기반 자동화 워크플로우

**상태**: ⏸️ 선택사항

**예상 소요 시간**: 2일

### 작업 목록 (간략)

- [ ] `bl_agent/agent.py` 구현
- [ ] `bl_agent/prompt.py` 작성
- [ ] HTTP 모드 테스트
- [ ] 자동화 워크플로우 구축

---

## 작동하는 것 (What Works)

### 데이터 수집
- ✅ `collect_ohlcv.py`: yfinance → Parquet
- ✅ OHLCV 데이터 저장 구조

### 문서화
- ✅ README.md: 전체 계획 및 구조
- ✅ Memory Bank: 6개 핵심 파일 완성

### 개념 검증
- ✅ FastMCP 패턴 이해
- ✅ PyPortfolioOpt 사용법 파악
- ✅ 9_AGENT_PROTOCOL 참고

---

## 남은 작업 (What's Left)

### Phase 1 (즉시 착수)
- 프로젝트 설정 (pyproject.toml, 패키지 구조)
- 유틸리티 구현 (data_loader, validators)
- 핵심 4개 Tools 구현
- FastMCP 서버 구현
- Windsurf 연동 및 테스트

### Phase 2-4 (순차 진행)
- 백테스팅, 팩터 모델, HRP
- 추가 데이터 소스
- ADK Agent 통합

### 배포 (최종)
- PyPI 패키지 등록
- GitHub 공개
- 문서화 완성

---

## 현재 상태 (Current Status)

### 완료된 마일스톤
1. ✅ **프로젝트 구상** (2025-11-20)
   - 블랙-리터만 모델 선택
   - MCP 프로토콜 채택
   - 8개 Tools 정의

2. ✅ **기술 스택 결정** (2025-11-20)
   - FastMCP 2.13.0.1
   - PyPortfolioOpt
   - stdio/HTTP 듀얼 모드

3. ✅ **Memory Bank 구축** (2025-11-20)
   - 6개 핵심 파일 작성
   - 전략 및 패턴 문서화

### 다음 마일스톤
1. 🔜 **Phase 1 MVP** (목표: 3일 이내)
   - 기본 최적화 작동
   - Windsurf 연동 성공
   - 시나리오 1 검증

2. ⏸️ **Phase 2 확장** (Phase 1 완료 후)
   - 백테스팅 추가
   - 팩터 모델 통합

---

## 알려진 이슈 (Known Issues)

현재 없음 - Phase 1 시작 전

---

## 메트릭 (Metrics)

### 코드 작성
- **라인 수**: 0 (구현 시작 전)
- **테스트 커버리지**: 0%
- **타입 커버리지**: N/A

### 기능 완성도
- **Tools**: 0/8 (0%)
- **Resources**: 0/4 (0%)
- **시나리오**: 0/3 (0%)

### 문서화
- **Memory Bank**: 6/6 (100%)
- **README**: 1/1 (100%)
- **코드 주석**: 0% (구현 시작 전)

---

## 다음 액션 아이템

### 오늘 (2025-11-20)
1. ✅ Memory Bank 완성 및 검토
2. ✅ Reference 자료 정리 (fastmcp, PyPortfolioOpt, 9_AGENT_PROTOCOL)
3. [ ] `pyproject.toml` 작성
4. [ ] 패키지 구조 생성
5. [ ] 의존성 설치

### 내일
1. [ ] `data_loader.py` 구현
2. [ ] `validators.py` 구현
3. [ ] Tool 1.1, 1.2 구현 시작

### 이번 주 말까지
1. [ ] Phase 1 완료
2. [ ] 시나리오 1 검증
3. [ ] Phase 2 계획 구체화

---

## 변경 이력

### 2025-11-22
- **API 개선 완료** ✅
  - Period 파라미터 추가 (3개 Tools)
  - validators.py 확장 (parse_period, resolve_date_range)
  - Docstring 개선 (LLM 친화적)
  - Memory Bank 업데이트 (systemPatterns.md, activeContext.md, progress.md)
  - 설계 결정 문서화 (통합 vs 분리 방식)

### 2025-11-21
- **MCP 서버 배포 준비 완료** 🚀
  - 자동 데이터 다운로드 구현
  - Repository Public 전환
  - GitHub Release 공개 (data-v1.0)
- **협업 인프라 구축** 🤝
  - CONTRIBUTING.md 작성
  - Docker 환경 구축
  - Makefile 통합
- **S&P 500 데이터 다운로드** 📊
  - 503개 종목 완료
  - Session 관리 모듈 구현

### 2025-11-20
- Memory Bank 초기 생성 (6개 파일)
- progress.md 작성
- Reference 자료 정리
  - `reference/` 폴더 생성
  - fastmcp, PyPortfolioOpt, 9_AGENT_PROTOCOL 이동
  - Idzorek 논문 추가 (선택적 참고 자료)
  - `reference/README.md` 작성 (핵심 참고 포인트 + 선택적 자료)
  - `.gitignore` 업데이트
- Phase 0 완료 표시
