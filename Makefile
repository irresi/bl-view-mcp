.PHONY: help install sync test test-simple test-agent clean sample data-snp500 download-data pack-data server-http server-stdio web-ui all

# Default target
help:
	@echo "Black-Litterman MCP Server - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install all dependencies (including agent extras)"
	@echo "  make sync         - Sync dependencies only"
	@echo ""
	@echo "Data:"
	@echo "  make sample       - Download sample data (AAPL, MSFT, GOOGL)"
	@echo "  make data-snp500  - Download S&P 500 data (503 tickers)"
	@echo "  make download-data - Download pre-packaged data from GitHub"
	@echo "  make pack-data    - Pack data folder for sharing (creates tar.gz)"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-simple  - Run simple direct tests (fastest)"
	@echo "  make test-agent   - Run ADK agent tests (requires server)"
	@echo ""
	@echo "Servers:"
	@echo "  make server-http  - Start HTTP server (port 5000)"
	@echo "  make server-stdio - Start stdio server (for Windsurf)"
	@echo "  make web-ui       - Start ADK Web UI (port 8000)"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start both HTTP server and Web UI"
	@echo "  make clean        - Clean generated files"
	@echo "  make clean-all    - Clean everything including data"
	@echo ""

# Installation
install:
	@echo "📦 Installing dependencies..."
	uv sync --extra agent
	@echo "✅ Installation complete!"

sync:
	@echo "🔄 Syncing dependencies..."
	uv sync
	@echo "✅ Sync complete!"

# Data download
sample:
	@echo "📊 Downloading sample data (AAPL, MSFT, GOOGL)..."
	uv run python scripts/download_data.py --tickers AAPL MSFT GOOGL --start 2023-01-01
	@echo "✅ Sample data download complete!"

data-snp500:
	@echo "📊 Downloading S&P 500 data (503 tickers)..."
	uv run python scripts/download_sp500.py
	@echo "✅ S&P 500 data download complete!"

# Data sharing (temporary, will migrate to S3)
download-data:
	@echo "📥 Downloading pre-packaged data from GitHub..."
	@which gh >/dev/null 2>&1 || (echo "❌ GitHub CLI (gh) not installed. Run: brew install gh" && exit 1)
	gh release download data-v1.0 -p "data.tar.gz" --clobber
	tar -xzf data.tar.gz
	rm data.tar.gz
	@echo "✅ Data download complete!"
	@echo "📊 Downloaded $$(ls data/*.parquet 2>/dev/null | wc -l | tr -d ' ') parquet files"

pack-data:
	@echo "📦 Packing data folder for sharing..."
	@if [ ! -d "data" ] || [ -z "$$(ls -A data/ 2>/dev/null)" ]; then \
		echo "❌ No data folder found. Run 'make sample' or 'make data-snp500' first."; \
		exit 1; \
	fi
	tar -czf data.tar.gz data/
	@echo "✅ Data packed: data.tar.gz"
	@ls -lh data.tar.gz
	@echo ""
	@echo "📤 Next steps:"
	@echo "  1. Go to: https://github.com/irresi/bl-view-mcp/releases/new"
	@echo "  2. Create tag: data-v1.0 (or increment version)"
	@echo "  3. Upload: data.tar.gz"
	@echo "  4. Collaborators can run: make download-data"

# Testing
test: test-simple
	@echo "✅ All tests passed!"

test-simple:
	@echo "🧪 Running simple tests..."
	uv run python tests/test_simple.py

test-agent:
	@echo "🤖 Running agent tests..."
	@echo "⚠️  Make sure HTTP server is running (make server-http)"
	uv run python tests/test_agent.py

# Servers
server-http:
	@echo "🚀 Starting HTTP server on http://localhost:5000/mcp"
	@echo "Checking for existing processes on port 5000..."
	@lsof -ti:5000 | xargs kill -9 2>/dev/null || true
	@echo "Press Ctrl+C to stop"
	uv run python start_http.py

server-stdio:
	@echo "🚀 Starting stdio server (for Windsurf)"
	@echo "Press Ctrl+C to stop"
	uv run python start_stdio.py

web-ui:
	@echo "🌐 Starting ADK Web UI on http://localhost:8000"
	@echo "⚠️  Make sure HTTP server is running (make server-http)"
	@echo "Checking for existing processes on port 8000..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@echo "Press Ctrl+C to stop"
	uv run adk web

# Development workflow
dev:
	@echo "🚀 Starting development environment..."
	@echo ""
	@echo "Terminal 1: HTTP Server"
	@echo "Terminal 2: Run 'make web-ui' in a new terminal"
	@echo ""
	@$(MAKE) server-http

# Quickstart for new users
quickstart: install sample test-simple
	@echo ""
	@echo "✅ Quickstart complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Terminal 1: make server-http"
	@echo "  2. Terminal 2: make web-ui"
	@echo "  3. Browser: http://localhost:8000"
	@echo ""

# Cleanup
clean:
	@echo "🧹 Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete!"

clean-all: clean
	@echo "🧹 Cleaning data files..."
	rm -rf data/*.parquet
	@echo "✅ Full cleanup complete!"

# Utility targets
check:
	@echo "🔍 Checking project status..."
	@echo ""
	@echo "Python version:"
	@python3 --version
	@echo ""
	@echo "UV installed:"
	@which uv && uv --version || echo "❌ UV not installed"
	@echo ""
	@echo "Data files:"
	@ls -lh data/*.parquet 2>/dev/null || echo "❌ No data files found (run 'make sample')"
	@echo ""
	@echo "Dependencies:"
	@uv pip list | grep -E "(fastmcp|PyPortfolioOpt|google-adk)" || echo "❌ Dependencies not installed (run 'make install')"

# Run everything (for CI/CD or full verification)
all: install sample test
	@echo "✅ All tasks completed successfully!"
