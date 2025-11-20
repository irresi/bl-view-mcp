#!/bin/bash
# Reference 폴더 정리 스크립트
# 구현에 필요한 핵심 파일만 남기고 나머지 제거

set -e

cd "$(dirname "$0")/reference"

echo "🧹 Reference 폴더 정리 시작..."
echo ""

# FastMCP 정리
echo "📦 FastMCP 정리 중..."
cd fastmcp

# 유지할 폴더: src, examples
# 제거할 폴더: .git, tests, docs, .cursor, .github, .vscode 등

# .git 제거 (20MB)
if [ -d ".git" ]; then
    echo "  - .git 제거 (20MB)"
    rm -rf .git
fi

# tests 제거 (2.7MB)
if [ -d "tests" ]; then
    echo "  - tests 제거 (2.7MB)"
    rm -rf tests
fi

# docs 제거 (9.4MB) - 온라인 문서 참고
if [ -d "docs" ]; then
    echo "  - docs 제거 (9.4MB)"
    rm -rf docs
fi

# 기타 불필요한 폴더들
for dir in .cursor .github .vscode .pytest_cache htmlcov; do
    if [ -d "$dir" ]; then
        echo "  - $dir 제거"
        rm -rf "$dir"
    fi
done

# 불필요한 파일들
for file in .gitignore .pre-commit-config.yaml .coverage .editorconfig; do
    if [ -f "$file" ]; then
        rm -f "$file"
    fi
done

echo "  ✅ FastMCP 정리 완료 (src, examples, README 유지)"
echo ""

# PyPortfolioOpt 정리
cd ../PyPortfolioOpt
echo "📦 PyPortfolioOpt 정리 중..."

# 유지할 폴더: pypfopt, cookbook
# 제거할 폴더: .git, tests, docs, .github 등

# .git 제거 (15MB)
if [ -d ".git" ]; then
    echo "  - .git 제거 (15MB)"
    rm -rf .git
fi

# tests 제거 (1.6MB)
if [ -d "tests" ]; then
    echo "  - tests 제거 (1.6MB)"
    rm -rf tests
fi

# docs 제거 (144KB) - cookbook이 더 유용
if [ -d "docs" ]; then
    echo "  - docs 제거 (144KB)"
    rm -rf docs
fi

# example 제거 (4KB) - cookbook이 더 상세함
if [ -d "example" ]; then
    echo "  - example 제거"
    rm -rf example
fi

# media 제거
if [ -d "media" ]; then
    echo "  - media 제거"
    rm -rf media
fi

# 기타 불필요한 폴더들
for dir in .github .pytest_cache htmlcov; do
    if [ -d "$dir" ]; then
        echo "  - $dir 제거"
        rm -rf "$dir"
    fi
done

# 불필요한 파일들
for file in .gitignore .pre-commit-config.yaml .editorconfig readthedocs.yml requirements.txt pyproject.toml; do
    if [ -f "$file" ]; then
        rm -f "$file"
    fi
done

echo "  ✅ PyPortfolioOpt 정리 완료 (pypfopt, cookbook, README 유지)"
echo ""

# 9_AGENT_PROTOCOL은 그대로 유지 (샘플 프로젝트 전체 필요)
echo "📦 9_AGENT_PROTOCOL은 유지 (전체 샘플 프로젝트)"
echo ""

cd ..

echo "✨ 정리 완료!"
echo ""
echo "📊 용량 확인:"
du -sh fastmcp PyPortfolioOpt 9_AGENT_PROTOCOL 2>/dev/null || echo "용량 확인 중..."
