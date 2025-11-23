FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# uv 설치 (pip 사용 - 더 안정적)
RUN pip install --no-cache-dir uv

# 프로젝트 파일 복사
COPY pyproject.toml uv.lock README.md ./
COPY bl_mcp ./bl_mcp
COPY bl_agent ./bl_agent
COPY scripts ./scripts
COPY tests ./tests
COPY start_http.py start_stdio.py ./

# 의존성 설치 (agent + crypto + dev)
RUN uv sync --extra agent --extra crypto --extra dev

# 데이터 디렉토리 생성
RUN mkdir -p /app/data

# 포트 노출
EXPOSE 5000

# 기본 명령어 (HTTP 모드)
CMD ["uv", "run", "python", "start_http.py"]
