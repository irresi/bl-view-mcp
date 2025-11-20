# Quick Start Guide

Black-Litterman MCP Server를 5분 안에 시작하는 방법입니다.

## 🚀 한 번에 시작하기

```bash
make quickstart
```

이 명령어는 다음을 자동으로 수행합니다:
1. ✅ 의존성 설치
2. ✅ 샘플 데이터 다운로드 (AAPL, MSFT, GOOGL)
3. ✅ 테스트 실행

---

## 📋 단계별 실행

### 1단계: 설치

```bash
make install
```

### 2단계: 데이터 다운로드

```bash
# 샘플 데이터 (3개 종목)
make data

# 또는 더 많은 데이터 (5개 종목)
make data-full
```

### 3단계: 테스트

```bash
# 빠른 테스트
make test-simple
```

**예상 출력**:
```
✅ Success!
📊 Portfolio Weights:
  AAPL: 33.33%
  MSFT: 33.33%
  GOOGL: 33.33%
```

---

## 🌐 Web UI로 테스트 (추천!)

### Terminal 1: MCP 서버 시작

```bash
make server-http
```

### Terminal 2: Web UI 시작

```bash
make web-ui
```

### 브라우저 접속

```
http://localhost:8000
```

**테스트 프롬프트**:
```
AAPL, MSFT, GOOGL로 포트폴리오를 최적화해줘.
2023년부터 데이터를 사용하고,
AAPL이 10% 수익을 낼 것으로 예상해. 확신도는 70%야.
```

---

## 🛠️ 유용한 명령어

### 모든 명령어 보기
```bash
make help
```

### 프로젝트 상태 확인
```bash
make check
```

### 정리
```bash
# 캐시만 삭제
make clean

# 데이터까지 모두 삭제
make clean-all
```

---

## 📚 다음 단계

- **상세 테스트**: `tests/README.md`
- **Web UI 가이드**: `tests/ADK_WEB_GUIDE.md`
- **Windsurf 연동**: `WINDSURF_SETUP.md`
- **전체 문서**: `README.md`

---

## ❓ 문제 해결

### "make: command not found"
macOS/Linux에는 기본 설치되어 있습니다. Windows는 WSL 사용을 권장합니다.

### "uv: command not found"
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Data file not found"
```bash
make data
```

### 서버 연결 실패
```bash
# 서버가 실행 중인지 확인
lsof -i :5000
lsof -i :8000

# 포트가 사용 중이면 프로세스 종료 후 재시작
```

---

**Happy Optimizing! 📈**
