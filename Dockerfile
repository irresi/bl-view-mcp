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

# 의존성 설치 (core only - data comes from GitHub Releases)
# Set version for setuptools-scm (no .git in Docker)
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.3.1
RUN uv sync

# 데이터 디렉토리 생성
RUN mkdir -p /app/data

# S&P 500 데이터 사전 다운로드 (첫 요청 timeout 방지)
# GitHub Releases에서 다운로드 (빌드 시간 +10초, 런타임 +30초 절약)
RUN curl -L -o /app/data/snp500.parquet \
    https://github.com/irresi/bl-view-mcp/releases/download/v0.3.1/snp500.parquet || \
    echo "Warning: Failed to download S&P 500 data, will auto-download on first request"

# 포트 노출
EXPOSE 5000

# 기본 명령어 (HTTP 모드)
CMD ["uv", "run", "python", "start_http.py"]
