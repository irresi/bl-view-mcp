# Active Context

## 현재 상태

**Phase**: Phase 1 완료 ✅ + API 검증 및 최적화 완료 ✅
**초점**: Idzorek Black-Litterman 구현 검증 및 LLM 친화적 설계 완성

## 최근 변경사항

### Relative View Support 구현 완료 (2025-11-22) 🚀

#### 1. **Breaking Change: P, Q 전용 API**
   - ✅ 절대적 뷰 dict 형식 제거 (`{"AAPL": 0.10}` ❌)
   - ✅ P, Q 형식으로 통일 (`{"P": [{"AAPL": 1}], "Q": [0.10]}` ✅)
   - ✅ LLM 혼동 방지 (ticker 키 + P/Q 혼용 불가)
   - ✅ 명확한 에러 메시지
   - ✅ API 일관성 향상

#### 2. **Relative View 지원**
   - ✅ Dict-based P: `{"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}`
   - ✅ NumPy P: `{"P": [[1, -1, 0]], "Q": [0.20]}`
   - ✅ Absolute view도 P, Q 형식: `{"P": [{"AAPL": 1}], "Q": [0.10]}`
   - ✅ Multiple views: `{"P": [{...}, {...}], "Q": [0.20, 0.15]}`

#### 3. **Confidence 간소화**
   - ✅ Dict confidence 제거 (혼란 방지)
   - ✅ Float: `confidence=0.7` (모든 뷰에 동일)
   - ✅ List: `confidence=[0.9, 0.8]` (뷰별 다르게)
   - ✅ None: 기본값 0.5
   - ✅ Type hint 업데이트: `float | list` (dict 제거)

#### 4. **Implementation**
   - ✅ `_parse_views()`: P, Q 필수, 절대 뷰 로직 제거
   - ✅ `_normalize_confidence()`: dict 처리 제거
   - ✅ Validation 강화: 혼합 형식 차단
   - ✅ server.py docstring 업데이트 (한국어 예시 포함)
   - ✅ tools.py docstring 업데이트

#### 5. **테스트 업데이트**
   - ✅ `test_relative_views_simple.py` 전면 수정
   - ✅ 구 형식 거부 테스트 추가
   - ✅ Dict confidence 거부 테스트 추가
   - ✅ 모든 테스트 통과 (15+ 케이스)

#### 6. **Design Rationale**
   - **Why Breaking Change?**
     - LLM이 `{"AAPL": 0.10, "P": [...], "Q": [...]}`처럼 혼용
     - 예측 불가능한 동작
     - 하나의 명확한 방법 = 더 적은 오류
   
   - **Why Remove Dict Confidence?**
     - P, Q 뷰에서는 ticker 이름이 P 내부에 있음
     - Dict key로 매칭 불가능
     - List가 더 명확하고 일관적

#### 7. **Documentation**
   - ✅ MCP tool docstring 업데이트
   - ✅ 한국어 예시: "엔비디아가 애플과 마이크로소프트보다 30% 높다"
   - ✅ 4가지 형식 예시 (absolute, relative, multiple, NumPy)

### Idzorek 구현 검증 및 개선 (2025-11-22) ✅

#### 1. **심층 검증 완료**
   - ✅ Idzorek 방식 올바른 사용 확인 (`omega="idzorek"`)
   - ✅ server.py ↔ tools.py 시그니처 완벽 일치
   - ✅ PyPortfolioOpt BlackLittermanModel 정확한 활용
   - ✅ Absolute View 완벽 지원
   - ✅ Parameter validation 강화

#### 2. **Per-View Confidence 지원 추가** 🆕
   - ✅ 단일 confidence: `confidence=0.7` (모든 view에 동일)
   - ✅ view별 confidence: `confidence={"AAPL": 0.9, "MSFT": 0.6}`
   - ✅ Dict confidence validation (누락된 view 감지)
   - ✅ Type hint 정확화 (`Optional[float | dict]`)
   - ✅ Docstring 업데이트 (server.py, tools.py)

#### 3. **테스트 시스템 구축**
   - ✅ `tests/test_idzorek_implementation.py` 작성
   - ✅ 6개 테스트 시나리오 모두 통과:
     - Single confidence
     - Per-view confidence
     - Missing confidence detection
     - Percentage input (70 → 0.7)
     - Market equilibrium (no views)
     - Default confidence (0.5)
   - ✅ Makefile에 `test-idzorek` 타겟 추가

#### 4. **검증 문서 작성**
   - ✅ `docs/IDZOREK_VERIFICATION.md`: 완전한 검증 보고서
   - ✅ 모든 검증 결과 문서화
   - ✅ 사용 예시 및 권장사항 포함
   - ✅ LLM 호출 가능성 확인

#### 5. **Parameter Swap 버그 수정**
   - ✅ server.py에 `period` 파라미터 누락 발견
   - ✅ Positional arguments로 인한 매핑 오류 해결
   - ✅ Keyword arguments 사용으로 안전성 확보
   - ✅ Debug logging 추가 (parameter 추적)
   - ✅ 자동 swap 감지 및 복구 로직 추가

### Agent Prompt 간소화 (2025-11-22) ✅

#### 1. **프롬프트 대폭 축소**
   - ✅ **267줄 → 72줄 (73% 감소)**
   - ✅ 핵심만 남기고 중복 제거
   - ✅ LLM 집중도 향상
   - ✅ 토큰 비용 ~70% 절감

#### 2. **구조 개선**
   - ✅ 타입 규칙 (4줄)
   - ✅ 가장 흔한 실수 (2개만)
   - ✅ 자연어 변환 (간결하게)
   - ✅ 1개의 완벽한 예시

#### 3. **제거한 것**
   - ❌ 중복된 파라미터 설명
   - ❌ 너무 많은 예시 (8개 → 1개)
   - ❌ 장황한 이론 설명
   - ❌ 중복된 올바른/잘못된 예시들

#### 4. **핵심 메시지 강조**
   - ✅ `views = 딕셔너리` (어떤 종목이 얼마?)
   - ✅ `confidence = 숫자` (얼마나 확신?)
   - ✅ `period` 우선 사용
   - ✅ 확신도 스케일 간결하게

### Period 파라미터 추가 (2025-11-22) ✅

#### 1. **날짜 범위 처리 개선**
   - ✅ `period` 파라미터 추가 (상대 기간 지원)
   - ✅ 상호 배타적 파라미터 패턴 적용
   - ✅ LLM 친화적 docstring 개선
   - ✅ Phase 1 Tools에 모두 적용:
     - `calculate_expected_returns`
     - `calculate_covariance_matrix`
     - `optimize_portfolio_bl`

#### 2. **validators.py 확장**
   - ✅ `parse_period()`: "1Y", "3M" 등 파싱
   - ✅ `resolve_date_range()`: period vs absolute dates 해결
   - ✅ 기본값 "1Y" (1년) 적용
   - ✅ 상호 배타성 경고 (start_date + period 동시 사용 시)

#### 3. **지원 형식**
   - ✅ Days: "1D", "7D"
   - ✅ Weeks: "1W", "4W"
   - ✅ Months: "1M", "3M", "6M"
   - ✅ Years: "1Y", "2Y", "5Y"

#### 4. **설계 결정 이유**
   - **통합 인자 방식 기각**: start_date에 "1Y" 또는 "2023-01-01" 혼용
     - 파싱 로직 복잡
     - LLM 혼란 가능성
     - 에러 메시지 모호
   
   - **분리 방식 채택**: period vs start_date
     - 필드 이름만 봐도 의도 명확
     - LLM이 "Slot Filling" 방식으로 쉽게 처리
     - 검증 로직 단순
     - 금융 도메인에서 데이터 정확성 보장

#### 5. **Docstring 개선 포인트**
   - "Mutually exclusive" 명시
   - "(RECOMMENDED)" 키워드로 period 우선 사용 유도
   - "Do NOT use with" 명확한 금지 지시
   - 예제 포함으로 LLM 이해도 향상



### MCP 서버 배포 준비 완료 (2025-11-21) 🚀

#### 1. **자동 데이터 다운로드** (MCP 사용자 지원)
   - ✅ `ensure_data_available()` 함수 추가
   - ✅ GitHub Release에서 자동 다운로드
   - ✅ 첫 실행 시 자동으로 data.tar.gz (49MB, 503개 종목) 다운로드
   - ✅ 로컬 캐싱 (이후 실행은 캐시 사용)
   - ✅ **MCP 서버 사용자가 수동 설정 없이 바로 사용 가능**

#### 2. **Public Repository 전환**
   - ✅ GitHub Repository Public 공개
   - ✅ GitHub Release 공개 접근 가능
   - ✅ MCP Server Registry/Marketplace 배포 준비 완료

### 협업 인프라 완성 (2025-11-21) 🚀

#### 1. **CONTRIBUTING.md 작성**
   - ✅ 프로젝트 구조 및 도구 설명
   - ✅ 개발 환경 설정 가이드 (Docker/로컬)
   - ✅ 데이터 준비 방법 (패키징/직접 다운로드)
   - ✅ 개발 워크플로우 전체 문서화
   - ✅ 테스트 가이드 및 예제
   - ✅ 코드 스타일 및 PR 가이드라인
   - ✅ 데이터 공유 워크플로우

#### 2. **Docker 환경 구축** 🐳
   - ✅ `Dockerfile`: Python 3.11 + uv (pip 설치)
     - build-essential 포함 (gcc 등 빌드 도구)
     - README.md 명시적 복사
   - ✅ `.dockerignore`: 빌드 최적화
     - reference/, memory-bank/ 제외
     - 개별 문서 파일 제외 (README.md는 포함)
   - ✅ 크로스 플랫폼 지원 (Windows/macOS/Linux)

#### 3. **Makefile Docker 통합**
   - ✅ **docker-compose.yml 제거** (불필요한 복잡성)
   - ✅ Makefile에서 `docker run` 직접 사용
   - ✅ **관심사 분리**:
     - `docker-setup`: 환경 설정만 (이미지 빌드 + 컨테이너 생성)
     - 서버 실행: 사용자가 컨테이너 내에서 `make server-http` 실행
   - ✅ `--network host` 사용 (포트 충돌 없음)
   - ✅ 전체 프로젝트 마운트 (`$(PWD):/app`)
   - ✅ `docker-shell`: 컨테이너 접속
   - ✅ `docker-clean`: 환경 제거

#### 4. **개발 워크플로우 단순화**
   - ✅ Docker: `make docker-setup` → `make docker-shell` → `make server-http`
   - ✅ 로컬: 바로 `make server-http` 사용
   - ✅ 일관성: 컨테이너 내외 모든 명령어 동일
   - ✅ 단순성: 1개 파일 (Makefile), Docker Compose 불필요

### 개발 워크플로우 개선 (2025-11-21) 🛠️

#### 1. **Makefile 개선**
   - ✅ 포트 충돌 자동 해결
     - `server-http`: 5000번 포트 사용 중인 프로세스 자동 kill
     - `web-ui`: 8000번 포트 사용 중인 프로세스 자동 kill
     - `lsof -ti:PORT | xargs kill -9` 패턴 적용
   - ✅ 명령어 네이밍 개선
     - `data` → `sample` (샘플 데이터 3개)
     - `data-full` 제거 (불필요)
     - `data-snp500` 추가 (S&P 500 전체 503개)
   - ✅ `.PHONY` 정리 및 help 메시지 업데이트

#### 2. **데이터 공유 시스템 구축**
   - ✅ GitHub Release 기반 배포 (S3 이전 전 임시)
     - `pack-data`: data 폴더 전체 압축 (data.tar.gz, 49MB)
     - `download-data`: GitHub Release에서 다운로드
     - GitHub CLI (`gh`) 사용으로 안정적 다운로드
     - `--clobber` 옵션으로 덮어쓰기 지원
   - ✅ Release 생성 완료
     - Tag: `data-v1.0`
     - 파일: `data.tar.gz` (48.51 MB)
     - URL: https://github.com/irresi/bl-view-mcp/releases/tag/data-v1.0
   - ✅ 다운로드 테스트 완료 (503개 파일 모두 복원)

#### 3. **저장소 정리**
   - ✅ GitHub 저장소 이름 변경
     - 기존: `Black-Litterman-View-Generation`
     - 신규: `bl-view-mcp` (간결하고 명확)
   - ✅ git remote 업데이트
     - `https://github.com/irresi/bl-view-mcp.git`
   - ✅ `.gitignore` 업데이트
     - `data.tar.gz` 추가

#### 4. **협업 워크플로우**
   - ✅ 데이터 제공자 (본인)
     ```bash
     make data-snp500  # 데이터 다운로드
     make pack-data    # 압축
     # GitHub Release 업로드 (자동)
     ```
   - ✅ 협업자 (팀원)
     ```bash
     make download-data  # 한 줄로 완료!
     ```
   - ✅ 장점
     - ⚡ 빠름: 503개 개별 다운로드 → 1개 압축 파일
     - 🔒 일관성: 모든 협업자가 동일한 데이터 사용
     - 💾 압축: 49MB (yfinance 재다운로드 불필요)

### S&P 500 데이터 파이프라인 구축 🚀

#### 1. **Session 관리 모듈 구현**
   - ✅ `bl_mcp/utils/session.py`: HTTP 세션 관리 유틸리티
     - 12개 다양한 User-Agent 리스트 (Chrome, Firefox, Safari, Edge)
     - 랜덤 User-Agent 선택으로 차단 회피
     - Retry 로직 내장 (429, 500, 502, 503, 504 자동 재시도)
     - Connection pooling 최적화
     - MCP 서버 안전 (여러 사용자 동시 사용 가능)

#### 2. **S&P 500 데이터 다운로드 스크립트**
   - ✅ `scripts/download_sp500.py`: S&P 500 전체 종목 다운로드
     - Wikipedia에서 503개 티커 자동 수집 (custom session 사용)
     - yfinance로 상장일부터 전체 데이터 다운로드
     - Incremental update 지원 (기존 데이터 보존)
     - Success/Skip/Failed 상태 구분
     - CSV 저장 (`data/sp500_tickers.csv`) - 섹터 정보 포함

#### 3. **의존성 정리**
   - ✅ FinanceDataReader 제거 (403 에러로 작동 불가)
   - ✅ `requests` 추가 (session 관리용)
   - ✅ `lxml`, `html5lib` 추가 (Wikipedia 파싱용)

#### 4. **다운로드 완료** ✅
   - ✅ **S&P 500 전체 503개 종목 다운로드 완료!**
   - ✅ 성공: 503/503 (100%)
   - ✅ 실패: 0개
   - ✅ 상장일부터 전체 히스토리 데이터 수집
   - 📁 데이터 위치: `data/*.parquet` (503개 파일)
   - 📊 티커 리스트: `data/sp500_tickers.csv` (섹터 정보 포함)

### Phase 1 MVP 완료 🎉

#### 1. **핵심 구현 완료**
   - ✅ `pyproject.toml`: 의존성 관리 (fastmcp, PyPortfolioOpt, pandas, numpy, yfinance, pyarrow, scikit-learn, google-adk)
   - ✅ `bl_mcp/server.py`: FastMCP 서버 (@mcp.tool 데코레이터)
   - ✅ `bl_mcp/tools.py`: 4개 MCP Tools 구현
     - calculate_expected_returns
     - calculate_covariance_matrix
     - create_investor_view
     - optimize_portfolio_bl (Black-Litterman 핵심)
   - ✅ `bl_mcp/utils/data_loader.py`: Parquet 데이터 로딩
   - ✅ `bl_mcp/utils/validators.py`: 입력 검증

#### 2. **ADK Agent 구현**
   - ✅ `bl_agent/agent.py`: Google ADK Agent 정의
   - ✅ `bl_agent/prompt.py`: 한국어 프롬프트 (상세 instruction)
   - ✅ MCPToolset 연동 (StreamableHTTPConnectionParams)

#### 3. **데이터 파이프라인**
   - ✅ `scripts/download_data.py`: yfinance → Parquet (개별 종목용)
   - ✅ `scripts/download_sp500.py`: S&P 500 전체 다운로드 (503개)
   - ✅ `bl_mcp/utils/session.py`: Session 관리 (랜덤 User-Agent)
   - ✅ Wikipedia 파싱으로 S&P 500 티커 자동 수집
   - ✅ 증분 업데이트 지원 (Incremental update)
   - ✅ 상장일부터 전체 히스토리 다운로드
   - 🔄 503개 종목 다운로드 진행 중

#### 4. **테스트 시스템**
   - ✅ `tests/test_simple.py`: 직접 테스트 (모든 테스트 통과!)
   - ✅ `tests/test_agent.py`: ADK Agent 통합 테스트
   - ✅ `tests/README.md`: 테스트 가이드
   - ✅ `tests/ADK_WEB_GUIDE.md`: Web UI 상세 가이드

#### 5. **실행 스크립트**
   - ✅ `start_stdio.py`: Windsurf/Claude Desktop용
   - ✅ `start_http.py`: ADK Agent/Web UI용

#### 6. **문서화 & 개발 도구**
   - ✅ `TESTING.md`: 퀵스타트 가이드
   - ✅ `QUICKSTART.md`: 5분 시작 가이드
   - ✅ `Makefile`: 모든 작업 자동화
   - ✅ `WINDSURF_SETUP.md`: Windsurf 연동 가이드

#### 7. **Reference 정리**
   - ✅ `reference/db대회/` 삭제 (1.1GB → 0)
   - ✅ 핵심 기능만 추출 (scripts/download_data.py)

### Phase 0 준비 단계 완료

1. **README.md 대폭 수정**
2. **Memory Bank 초기화**
3. **Reference 자료 정리** (693MB → 11.6MB)

## 현재 작업 초점

### 완료: S&P 500 전체 데이터 다운로드 ✅

**최종 결과**:
- ✅ **503개 종목 모두 성공** (100% 완료, 실패 0개)
- ✅ 상장일부터 전체 히스토리 수집
- ✅ 평균 ~30년 데이터 (종목별 상장일에 따라 다름)
- ✅ **총 파일 크기: 2.0MB** (503개 Parquet 파일)
- ✅ 섹터 정보 포함 CSV 저장 (`data/sp500_tickers.csv`)

**다음 단계**:
1. ✅ S&P 500 데이터 다운로드 완료
2. 📊 데이터 품질 검증
3. 🧪 대규모 포트폴리오 테스트 (50개+ 종목)
4. 📝 사용 예제 문서화
5. 🚀 Memory Bank 최종 업데이트 및 커밋

### 완료: Web UI 테스트 & 검증 ✅

**테스트 결과**:
- ✅ MCP Server 정상 작동
- ✅ ADK Web UI 정상 작동  
- ✅ Black-Litterman 모델 정확도 확인
- ✅ 실제 대화 예제 저장 (`reference/agent_example/202511210112`)

**검증된 시나리오**:
```
AAPL, MSFT, GOOGL로 포트폴리오를 최적화해줘.
AAPL이 6개월동안 30% 수익을 낼 것 같아 (확신도 0.3)
```

**실제 결과**:
- Portfolio Weights: AAPL 64.39%, GOOGL 17.80%, MSFT 17.80%
- Expected Return: 23.11%
- Volatility: 22.62%
- Sharpe Ratio: 1.02

### Phase 2 준비

- [x] S&P 500 데이터 파이프라인 구축
- [x] Session 관리 모듈 구현
- [x] Web UI 테스트 완료
- [ ] Windsurf 연동 테스트
- [ ] 백테스팅 도구 추가
- [ ] 추가 최적화 방법 (HRP, Risk Parity)

### 우선순위 2: Phase 1 준비

다음 단계로 Phase 1 구현을 시작합니다:

1. **프로젝트 설정**
   - [ ] `pyproject.toml` 작성
   - [ ] 패키지 구조 생성 (`bl_mcp/`, `bl_agent/`)
   - [ ] 의존성 설치

2. **유틸리티 구현**
   - [ ] `bl_mcp/utils/data_loader.py`
   - [ ] `bl_mcp/utils/validators.py`

3. **핵심 Tools**
   - [ ] `bl_mcp/tools.py` (4개 Tool 로직)
   - [ ] `bl_mcp/server.py` (FastMCP 래퍼)

4. **실행 스크립트**
   - [ ] `start_stdio.py`
   - [ ] `start_http.py`

## 활성 결정사항

### FastMCP 사용 결정

**날짜**: 2025-11-20

**결정**: FastMCP를 사용하여 stdio/HTTP 듀얼 모드 구현

**이유**:
1. `@mcp.tool` 데코레이터로 간결한 구현
2. stdio 모드로 Windsurf에서 직접 테스트 가능
3. HTTP 모드로 ADK Agent 연동 가능
4. 하나의 서버 코드로 두 가지 사용 사례 지원

**영향**:
- 개발 속도 향상 (보일러플레이트 최소화)
- 유연성 증가 (개발 → 프로덕션)
- 학습 곡선 낮음 (간단한 API)

### Reference 자료 정리

**위치**: `/reference/`

**내용**:
1. **fastmcp/** (35MB)
   - FastMCP 소스 코드
   - 예제 프로젝트들
   - 참고: `examples/`, API 사용법

2. **PyPortfolioOpt/** (28MB)
   - PyPortfolioOpt 소스 코드
   - 🌟 핵심: `cookbook/2-black-litterman.ipynb`
   - 참고: `pypfopt/*.py` API, `tests/` 사용 예제

3. **9_AGENT_PROTOCOL/** (630MB)
   - ADK Agent + FastMCP 샘플 프로젝트
   - 참고: `image_mcp/server.py`, `image_editor_agent_with_mcp/agent.py`

4. **Idzorek_onBL.pdf** (283KB, 선택적)
   - Black-Litterman 이론 배경
   - PyPortfolioOpt의 `idzorek_method()` 근거
   - 필요할 때만 참고 (이미 구현되어 있음)

**학습한 패턴**:
1. **FastMCP 서버 구조**
   - `@mcp.tool` 데코레이터 사용
   - tools.py로 로직 분리 (thin wrapper)
   - 명확한 Docstring

2. **Tools 로직 분리**
   - 순수 Python 함수
   - Dict 반환 (`{"success": True, ...}`)
   - 예외 처리 포함

3. **ADK Agent 패턴**
   - MCPToolset + StreamableHTTPConnectionParams
   - instruction/description 분리
   - Gemini 모델 사용

4. **PyPortfolioOpt API**
   - `expected_returns.mean_historical_return()`
   - `risk_models.ledoit_wolf()`
   - `BlackLittermanModel()`

## 다음 단계

### 완료됨 ✅

1. ✅ Memory Bank 완성 및 검토
2. ✅ Reference 자료 정리 및 최적화 (693MB → 11.6MB)
3. ✅ Phase 1 완료 (MVP - 4개 도구)
4. ✅ 협업 인프라 구축 (CONTRIBUTING.md, Docker, Makefile 통합)
5. ✅ 데이터 공유 시스템 (GitHub Release)
6. ✅ **MCP 서버 배포 준비 완료** (자동 데이터 다운로드)

### 단기 (이번 주)

1. **Phase 2 준비**
   - [ ] 백테스팅 요구사항 정의
   - [ ] 추가 도구 설계 (5-8번)
   - [ ] 테스트 시나리오 작성

2. **문서 개선 (선택)**
   - [ ] README에 Docker 빠른 시작 추가
   - [ ] QUICKSTART.md 업데이트
   - [ ] 사용 예제 추가

### 중기 (다음 주)

1. **Phase 2 구현**
   - [ ] Tool 5: `backtest_portfolio` - 백테스팅
   - [ ] Tool 6: `get_market_data` - 시장 데이터 조회
   - [ ] Tool 7: `calculate_factor_scores` - 팩터 스코어링
   - [ ] Tool 8: `calculate_hrp_weights` - HRP 가중치

2. **배포 준비**
   - [ ] Docker Hub 이미지 퍼블리시
   - [ ] 사용 예제 및 튜토리얼

## 현재 고려사항

### 기술적 고려사항

1. **데이터 로딩 전략**
   - Parquet 파일이 이미 존재하는지 확인 필요
   - 없으면 `collect_ohlcv.py` 실행
   - 캐싱 전략 (동일한 데이터 중복 로드 방지)

2. **에러 처리**
   - 티커가 유효하지 않은 경우
   - 데이터가 부족한 경우 (최소 60일 권장)
   - 공분산 행렬이 singular인 경우

3. **타입 안전성**
   - 모든 함수에 type hints 추가
   - mypy로 검증

### 사용자 경험 고려사항

1. **명확한 피드백**
   - 각 Tool의 결과에 `success` 필드
   - 에러 시 명확한 메시지
   - 중간 결과 포함 (투명성)

2. **유연한 입력**
   - `start_date`/`end_date` 또는 `lookback_days`
   - 기본값 제공 (예: method="historical_mean")
   - 선택적 파라미터 활용

## 블로커 및 리스크

### 현재 블로커

없음 - Memory Bank 완성 후 바로 Phase 1 시작 가능

### 잠재적 리스크

1. **데이터 품질**
   - yfinance 데이터 누락 가능성
   - 완화: 충분한 데이터 검증, 대체 소스 고려

2. **공분산 행렬 특이성**
   - 데이터가 부족하거나 상관관계가 너무 높으면 singular
   - 완화: Ledoit-Wolf 축소 추정, 최소 데이터 요구사항

3. **성능**
   - 대량의 티커 처리 시 느려질 수 있음
   - 완화: 캐싱, 병렬 처리

## 학습 노트

### FastMCP 핵심 패턴

```python
# 1. 서버 초기화
mcp = FastMCP("server-name")

# 2. Tool 등록
@mcp.tool
def my_tool(param: str) -> dict:
    """설명"""
    return {"result": "value"}

# 3. 실행
mcp.run(transport="stdio")  # 또는 "http"
```

### PyPortfolioOpt 핵심 패턴

```python
# 1. 기대수익률
from pypfopt import expected_returns
mu = expected_returns.mean_historical_return(prices)

# 2. 공분산
from pypfopt import risk_models
S = risk_models.ledoit_wolf(prices)

# 3. 블랙-리터만
from pypfopt.black_litterman import BlackLittermanModel
bl = BlackLittermanModel(S, pi=pi, P=P, Q=Q, omega=omega)
weights = bl.bl_weights()
```

## 참고 자료

- **FastMCP 문서**: https://github.com/jlowin/fastmcp
- **PyPortfolioOpt 문서**: https://pyportfolioopt.readthedocs.io/
- **Google ADK**: https://github.com/google/generative-ai-python
- **9_AGENT_PROTOCOL**: 로컬 참고 프로젝트

## 메모

- Memory Bank 전략이 잘 작동하는지 확인 후 Phase 1 시작
- 각 파일의 역할이 명확하게 분리됨
- 점진적으로 복잡도를 높이는 접근 (Phase 1 → 2 → 3 → 4)
- stdio 모드로 빠른 반복, HTTP 모드로 프로덕션 확장
