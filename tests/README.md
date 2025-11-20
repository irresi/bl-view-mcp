# Black-Litterman MCP Server - Testing

이 폴더는 Black-Litterman MCP Server의 다양한 테스트 방법을 제공합니다.

## 📋 테스트 종류

### 1. **test_simple.py** - 직접 테스트 (가장 빠름)

MCP 서버 없이 tools를 직접 호출하여 테스트합니다.

```bash
# 프로젝트 루트에서 실행
uv run python tests/test_simple.py
```

**장점**:
- 가장 빠른 테스트
- 서버 시작 불필요
- 명확한 디버깅

**테스트 항목**:
- ✅ Expected Returns 계산
- ✅ Covariance Matrix 계산
- ✅ 기본 포트폴리오 최적화 (견해 없음)
- ✅ 견해 포함 포트폴리오 최적화

---

### 2. **test_agent.py** - ADK Agent 테스트 (통합 테스트)

Google ADK Agent와 MCP 서버의 통합을 테스트합니다.

```bash
# Terminal 1: MCP 서버 시작
uv run python start_http.py

# Terminal 2: Agent 테스트 실행
uv run python tests/test_agent.py
```

**장점**:
- 실제 Agent 동작 확인
- MCP 프로토콜 검증
- 자동화된 시나리오 테스트

**테스트 항목**:
- ✅ Direct tool call
- ✅ Basic optimization (AI 해석)
- ✅ Optimization with views (AI 해석)

---

### 3. **ADK Web UI** - 브라우저 테스트 (가장 직관적)

Google ADK의 웹 UI를 통해 대화형으로 테스트합니다.

```bash
# Terminal 1: MCP 서버 시작
uv run python start_http.py

# Terminal 2: ADK Web UI 시작
adk web
```

그 다음 브라우저에서 `http://localhost:8000` 접속

**장점**:
- 가장 직관적
- 실시간 대화형 인터페이스
- 실제 사용 환경과 동일

**상세 가이드**: `ADK_WEB_GUIDE.md` 참조

---

## 🔄 테스트 순서 추천

### 초기 개발 단계
1. **test_simple.py** - 빠른 기능 검증
2. **test_agent.py** - 통합 검증
3. **ADK Web UI** - 사용자 경험 확인

### 디버깅 시
1. **test_simple.py** - 문제 원인 파악
2. 수정 후 재테스트
3. **test_agent.py** - 통합 재확인

### 데모/발표 시
- **ADK Web UI** - 실시간 시연

---

## 📊 테스트 데이터 준비

모든 테스트 전에 데이터를 다운로드해야 합니다:

```bash
# 기본 3개 종목
uv run python scripts/download_data.py --tickers AAPL MSFT GOOGL

# 더 많은 종목
uv run python scripts/download_data.py --tickers AAPL MSFT GOOGL AMZN TSLA

# 특정 기간
uv run python scripts/download_data.py --tickers AAPL MSFT --start 2020-01-01
```

다운로드된 데이터는 `data/` 폴더에 Parquet 형식으로 저장됩니다.

---

## 🐛 문제 해결

### "Data file not found" 에러
```bash
uv run python scripts/download_data.py --tickers AAPL MSFT GOOGL
```

### "Module not found" 에러
```bash
uv sync
# 또는 agent 의존성 포함
uv sync --extra agent
```

### MCP 서버 연결 실패
```bash
# 서버 재시작
# Terminal 1에서 Ctrl+C 후
uv run python start_http.py
```

---

## 📁 파일 구조

```
tests/
├── README.md              # 이 파일
├── test_simple.py         # 직접 테스트
├── test_agent.py          # ADK Agent 테스트
└── ADK_WEB_GUIDE.md       # ADK Web UI 가이드
```

---

## 🎯 예상 결과

### test_simple.py 성공 출력:
```
🧪 Black-Litterman Tools - Simple Tests

============================================================
TEST: Expected Returns Calculation
============================================================

✅ Success!

📊 Expected Returns:
  AAPL: 32.08%
  MSFT: 29.50%
  GOOGL: 53.67%

[... more tests ...]

============================================================
✅ All tests completed!
============================================================
```

### ADK Web UI 성공 시나리오:
**입력**: "AAPL, MSFT, GOOGL로 포트폴리오를 최적화해줘. 2023년부터 데이터를 사용해."

**출력**: 
```
3개 자산으로 최적 포트폴리오를 생성했습니다.

📊 포트폴리오 비중:
- AAPL: 33.33%
- MSFT: 33.33%
- GOOGL: 33.33%

📈 성과 지표:
- 예상 수익률: 11.38% (연율)
- 변동성: 21.34% (연율)
- 샤프 비율: 0.53
```

---

**Happy Testing! 🚀**
