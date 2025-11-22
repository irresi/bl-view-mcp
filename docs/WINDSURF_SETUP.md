# Windsurf 연동 가이드

## 1. MCP 설정 파일 위치

Windsurf의 MCP 설정 파일: `~/.codeium/windsurf/mcp_config.json`

## 2. 설정 추가

`mcp_config.json`에 다음 내용을 추가:

```json
{
  "mcpServers": {
    "black-litterman-portfolio": {
      "command": "python",
      "args": [
        "/Users/leejaehwan/Desktop/3-2/blackLittermanViewGeneration/start_stdio.py"
      ],
      "env": {}
    }
  }
}
```

**중요**: 
- `args`의 경로는 **절대 경로**를 사용해야 합니다
- 현재 프로젝트 경로: `/Users/leejaehwan/Desktop/3-2/blackLittermanViewGeneration`

## 3. Windsurf 재시작

설정 파일 수정 후 Windsurf를 완전히 종료하고 재시작합니다.

## 4. MCP 서버 확인

Windsurf 재시작 후:
1. 채팅 창에서 "@" 입력
2. "black-litterman-portfolio" 서버가 목록에 나타나는지 확인
3. `optimize_portfolio_bl` Tool이 보여야 함

## 5. 테스트 프롬프트

```
AAPL, MSFT, GOOGL로 포트폴리오를 최적화해줘.
최근 1년 데이터를 사용하고,
AAPL이 10% 수익을 낼 것으로 예상해. 확신도는 70%야.
```

## 6. 예상 동작

AI가 자동으로 `optimize_portfolio_bl` 호출:
- 포트폴리오 가중치, 수익률, 샤프 비율 제시
- 견해가 반영된 최적 포트폴리오 제안

## 7. 문제 해결

### 서버가 목록에 없는 경우:
- mcp_config.json 경로 확인
- JSON 문법 오류 확인 (콤마, 중괄호 등)
- Windsurf 완전히 재시작했는지 확인

### Tools가 작동하지 않는 경우:
- 의존성 설치 확인: `uv sync`
- start_stdio.py 실행 가능 확인: `python start_stdio.py`
- 데이터 파일 존재 확인: `ls data/*.parquet`

### 데이터 파일이 없는 경우:
- data/ 폴더에 AAPL.parquet, MSFT.parquet, GOOGL.parquet 등이 있어야 함
- 없으면 데이터 수집 스크립트 실행 필요
