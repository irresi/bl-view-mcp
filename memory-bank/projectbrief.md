# Project Brief: Black-Litterman Portfolio Optimization MCP Server

## Project Goal

Build a portfolio optimization MCP server based on Bayesian statistical model

## Core Concept

Implement the Black-Litterman model as an MCP (Model Context Protocol) server to enable AI to perform portfolio optimization

### Bayesian Approach

- **Prior (Prior Distribution)**: Market-cap weighted portfolio - reflects market equilibrium
- **Likelihood**: MCP Tools - Users/AI input investment views to update portfolio
- **Posterior (Posterior Distribution)**: Optimized portfolio

## Core Requirements

### 1. MCP Tool Provision

Simplified with **Single Tool** architecture:

`optimize_portfolio_bl` - Black-Litterman portfolio optimization

**Internal Processing:**
- Data collection (yfinance)
- Expected returns calculation (historical)
- Covariance matrix calculation (Ledoit-Wolf)
- Investor views (P, Q format)
- Idzorek Confidence -> Omega inversion
- Optimization execution

### 2. Flexible Transport Methods

- **stdio mode**: IDE integration with Windsurf, Claude Desktop, etc.
- **HTTP mode**: Google ADK Agent, web service integration

### 3. Integrated Design

All steps integrated into a single Tool for AI to complete with single call:
- No complex Tool combinations required
- Consistent interface
- Concise prompts

## Success Criteria

1. ✅ MCP server registered in Windsurf, AI can use Tools
2. ✅ Basic portfolio optimization scenarios work
3. ✅ Strategy validation possible with backtesting
4. ✅ (Optional) Automated workflow with ADK Agent

## Technical Constraints

- Python 3.11+
- FastMCP 2.13.0.1
- PyPortfolioOpt (core optimization library)
- Local Parquet data (collected via yfinance)

## Non-functional Requirements

- Type safety (Python type hints)
- Clear error handling and validation
- Each Tool returns results clearly as Dict
- Transparency: Return all intermediate results

## Project Scope

### In Scope

- Stock, ETF data (yfinance)
- Basic Black-Litterman model
- Factor model, HRP integration
- Backtesting and performance analysis

### Out of Scope (Current)

- Real-time trading integration
- Frontend UI
- Bonds, derivatives
- Real-time data streaming

## Differentiation Points

1. **Bayesian Approach**: Prior + Likelihood = Posterior
2. **AI-Friendly**: AI directly uses via MCP protocol
3. **Modular**: Each step provided as independent Tool
4. **Flexible**: stdio/HTTP dual mode
5. **Modern**: FastMCP's simplicity and type safety
