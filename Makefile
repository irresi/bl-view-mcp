.PHONY: help install sync test test-simple test-agent clean data server-http server-stdio web-ui all

# Default target
help:
	@echo "Black-Litterman MCP Server - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install all dependencies (including agent extras)"
	@echo "  make sync         - Sync dependencies only"
	@echo ""
	@echo "Data:"
	@echo "  make data         - Download sample data (AAPL, MSFT, GOOGL)"
	@echo "  make data-full    - Download extended data (5 tickers)"
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
data:
	@echo "📊 Downloading sample data (AAPL, MSFT, GOOGL)..."
	uv run python scripts/download_data.py --tickers AAPL MSFT GOOGL --start 2023-01-01
	@echo "✅ Data download complete!"

data-full:
	@echo "📊 Downloading extended data..."
	uv run python scripts/download_data.py --tickers AAPL MSFT GOOGL AMZN TSLA --start 2023-01-01
	@echo "✅ Extended data download complete!"

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
	@echo "Press Ctrl+C to stop"
	uv run python start_http.py

server-stdio:
	@echo "🚀 Starting stdio server (for Windsurf)"
	@echo "Press Ctrl+C to stop"
	uv run python start_stdio.py

web-ui:
	@echo "🌐 Starting ADK Web UI on http://localhost:8000"
	@echo "⚠️  Make sure HTTP server is running (make server-http)"
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
quickstart: install data test-simple
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
	@ls -lh data/*.parquet 2>/dev/null || echo "❌ No data files found (run 'make data')"
	@echo ""
	@echo "Dependencies:"
	@uv pip list | grep -E "(fastmcp|PyPortfolioOpt|google-adk)" || echo "❌ Dependencies not installed (run 'make install')"

# Run everything (for CI/CD or full verification)
all: install data test
	@echo "✅ All tasks completed successfully!"
