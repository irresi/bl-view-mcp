# Progress

## Overall Progress (2025-11-24)

```
Phase 0: ████████████████████████ 100% ✓ (Preparation)
Phase 1: ████████████████████████ 100% ✓ (MVP + Simplification)
Phase 2: ████████████████░░░░░░░░  66% (Backtest complete, HRP TBD)
Phase 3: ████████████████████████ 100% ✓ (PyPI v0.2.3 + Phase 3 improvements PR #22)
```

---

## Phase 1: Complete ✅

### Core Implementation

| Item | Status |
|------|--------|
| `optimize_portfolio_bl` | ✅ Only MCP Tool |
| P, Q format Views | ✅ Absolute + Relative |
| Idzorek confidence | ✅ float/list |
| Investment Style | ✅ aggressive/balanced/conservative |
| Auto data download | ✅ GitHub Release |
| Auto market cap load | ✅ yfinance + Parquet cache |

### Infrastructure

- ✅ FastMCP stdio/HTTP dual mode
- ✅ 503 S&P 500 data (Parquet)
- ✅ Docker support
- ✅ Makefile automation
- ✅ Test system

---

## Phase 2: Backtest Complete (2025-11-23)

### Included

- [x] `backtest_portfolio` - Backtesting ✅
- [ ] `calculate_hrp_weights` - HRP optimization (optional)

### Excluded (moved to bl-orchestrator)

- ~~`generate_views_from_technicals`~~
- ~~`generate_views_from_fundamentals`~~
- ~~`generate_views_from_sentiment`~~
- ~~`get_market_data`~~
- ~~`calculate_factor_scores`~~

### Project Separation Decision

| Project | Role |
|---------|------|
| **bl-mcp** | MCP Tool library (pure) |
| **bl-orchestrator** | Multi-agent view generation (CrewAI) |

---

## Phase 3: PyPI Release Complete ✅

### Release Status

| Item | Status |
|------|--------|
| PyPI package | ✅ `black-litterman-mcp` |
| Latest version | v0.2.3 |
| Trusted Publishing | ✅ GitHub Actions |
| Dynamic Versioning | ✅ hatch-vcs (git tags) |

### Claude Desktop Compatibility (v0.2.3)

| Issue | Cause | Solution |
|-------|-------|----------|
| Read-only filesystem | MCP runs at root | Use home directory |
| JSON string parameter | Claude sends dict as str | Added Union[dict, str] |

---

## Change History

### 2025-11-24 - Phase 3 Improvements (PR #22)
- **`get_asset_stats` new tool**
  - Per-asset statistics (price, return, volatility, Sharpe, market cap)
  - VaR 95% and 95th percentile (EGARCH-based)
  - Correlation matrix, covariance matrix
- **`backtest_portfolio` extensions**
  - `timeseries`: Monthly sampled portfolio values
  - `drawdown_details`: Max drawdown start/end/recovery dates
  - `compare_strategies`: Compare all strategies at once
  - `include_equal_weight`: Compare equal-weight portfolio
  - `timeseries_freq`: Selectable daily/weekly/monthly
- **`optimize_portfolio_bl` extensions**
  - `sensitivity_range`: Sensitivity analysis by confidence level
- **`_visualization_hint` added**
  - Visualization guide in all tool responses
  - safety_rules, recommended_charts, scale_guidance
- **README update**
  - Dashboard generation tips added
  - Example Use Cases section (5 prompt examples)
- **Tests added**
  - 5 backtest tests added to test_simple.py
- **PR #22**: Closes #17, #18, #19, #20

### 2025-11-23 (late night) - PyPI v0.2.3 Release
- **v0.2.3**: Added str type for views parameter
  - Resolved Claude Desktop sending JSON object as string
  - FastMCP + Claude Code known bug (anthropics/claude-code#3084)
  - Applied `Union[ViewMatrix, dict, str]` workaround
- **v0.2.2**: Moved data directory to home
  - `~/.black-litterman/data` default path
  - `BL_DATA_DIR` environment variable override support
  - Resolved Claude Desktop read-only issue
- **v0.2.1**: Added backtest_portfolio

### 2025-11-23 (night) - backtest_portfolio Implementation Complete
- **backtest_portfolio MCP Tool added**
  - Strategy preset pattern: buy_and_hold, passive_rebalance, risk_managed
  - Custom config support: rebalance_frequency, fees, stop_loss, max_drawdown_limit
  - Performance metrics: CAGR, Sharpe, Sortino, Max Drawdown, Calmar
  - Benchmark comparison: Alpha, Beta, Information Ratio
  - Holding periods tracking (for tax calculation)
- **Tests added**: tests/test_backtest.py (all 13 tests passed)
- **Documentation updated**: CLAUDE.md, README.md, memory-bank/*

### 2025-11-23 (evening) - Project Separation Decision
- **Phase 2 scope reduced**: Only backtest + HRP included
- **View generation excluded**: Replaced with multi-agent debate (separate project)
- **Reason**: Rule-based view generation is arbitrary, LLM reasoning is more suitable
- **GitHub Issue #11 updated**: Decision documented

### 2025-11-23 (afternoon)
- **Automatic market cap loading implemented**
  - `market_caps` parameter removed
  - `get_market_caps()` function added (data_loader.py)
  - Parquet cache -> yfinance -> equal weight fallback
  - Auto-caching of fetched market caps

### 2025-11-23 (morning)
- MCP Tool simplification: 4 -> 1 (`optimize_portfolio_bl`)
- Views format unified: P, Q format only
- Confidence simplified: float/list only
- Ticker sorting removed (preserve user order)
- `CLAUDE.md` created (auto context)
- memory-bank cleanup

### 2025-11-22
- P, Q only API (Breaking Change)
- Relative View support
- Period parameter added
- Idzorek implementation verification

### 2025-11-21
- Phase 1 MVP complete
- S&P 500 data download (503)
- GitHub Release deployment
- Docker environment setup

### 2025-11-20
- Project started
- Memory Bank initialized
- FastMCP + PyPortfolioOpt selected
