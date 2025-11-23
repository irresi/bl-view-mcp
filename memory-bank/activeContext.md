# Active Context

## 현재 상태 (2025-11-23)

**Phase**: Phase 3 완료 (PyPI 배포)
**초점**: v0.2.3 배포 완료, Claude Desktop 정상 작동 확인됨

---

## PyPI 배포 (v0.2.3)

### 설치
```bash
uv tool install black-litterman-mcp
# 또는
pip install black-litterman-mcp
```

### Claude Desktop 설정
```json
{
  "mcpServers": {
    "black-litterman": {
      "command": "/Users/사용자/.local/bin/bl-view-mcp"
    }
  }
}
```

---

## Claude Desktop 호환성 이슈 (해결됨)

### 문제 1: Read-only 파일 시스템 (v0.2.2에서 해결)
- **증상**: `[Errno 30] Read-only file system: 'data'`
- **원인**: Claude Desktop이 MCP를 루트 `/`에서 실행
- **해결**: 데이터 디렉토리를 `~/.black-litterman/data`로 변경

### 문제 2: JSON 문자열 파라미터 (v0.2.3에서 해결)
- **증상**: views 파라미터 Pydantic 검증 실패
- **원인**: Claude Desktop이 JSON object를 문자열로 전송
- **해결**: `views: Optional[Union[ViewMatrix, dict, str]]` - str 타입 추가
- **참고**: FastMCP + Claude Code 알려진 이슈
  - GitHub Issue: anthropics/claude-code#3084
  - 현재 workaround가 업계 표준

---

## 핵심 결정 (2025-11-23)

### 프로젝트 분리

| 프로젝트 | 역할 | 기술 |
|----------|------|------|
| **bl-mcp** (이 프로젝트) | MCP Tool 라이브러리 | FastMCP, PyPortfolioOpt |
| **bl-orchestrator** (별도) | Multi-agent view generation | CrewAI |

### Phase 2 범위 축소

**포함**:
- `backtest_portfolio` - 포트폴리오 백테스팅 ✅
- `calculate_hrp_weights` - HRP 최적화 (선택)

**제외** (bl-orchestrator로 이동):
- ~~`generate_views_from_technicals`~~
- ~~`generate_views_from_fundamentals`~~
- ~~`generate_views_from_sentiment`~~

---

## 버전 히스토리

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| v0.2.3 | 2025-11-23 | views 파라미터 str 타입 추가 (Claude Desktop 호환) |
| v0.2.2 | 2025-11-23 | 데이터 디렉토리 홈으로 이동 (read-only 해결) |
| v0.2.1 | 2025-11-23 | backtest_portfolio 추가 |

---

## 다음 단계

- [x] `backtest_portfolio` 구현 ✅
- [x] PyPI 배포 ✅
- [x] Claude Desktop 호환성 검증 ✅
- [ ] `calculate_hrp_weights` 구현 (선택)
- [ ] bl-orchestrator 프로젝트 생성 (별도)

---

## 참고

- 핵심 컨텍스트: `CLAUDE.md` (Claude Code 자동 로드)
- 상세 히스토리: `memory-bank/progress.md`
