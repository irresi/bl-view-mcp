# Active Context

## Current Status (2025-11-24)

**Phase**: Phase 3 Improvements Complete (PR #22)
**Focus**: Tool extensions, visualization hints, test enhancements

---

## Phase 3 Improvements (2025-11-24)

### 1. `get_asset_stats` New Tool
- Per-asset statistics (price, return, volatility, Sharpe, market cap)
- Includes VaR 95% and 95th percentile (EGARCH-based)
- Provides correlation matrix, covariance matrix
- Integrated `calculate_var_egarch` tool functionality

### 2. `backtest_portfolio` Extensions
- `timeseries`: Monthly sampled portfolio values
- `drawdown_details`: Max drawdown start/end/recovery dates
- `compare_strategies`: Compare all strategies at once
- `include_equal_weight`: Compare equal-weight portfolio
- `timeseries_freq`: Selectable daily/weekly/monthly

### 3. `optimize_portfolio_bl` Extensions
- `sensitivity_range`: Sensitivity analysis by confidence level
- e.g., `[0.3, 0.5, 0.9]` -> Results at each confidence level

### 4. `_visualization_hint` Added
- Visualization guide included in all tool responses
- Guides LLM to generate better dashboards
- Includes safety_rules, recommended_charts, scale_guidance

### 5. README Use Cases Added
- Dashboard generation tips added
- 5 practical prompt examples added:
  - Basic optimization + visualization
  - Benchmark backtest
  - Strategy comparison
  - Correlation analysis
  - Sensitivity analysis

---

## MCP Tools (Currently 5)

| Tool | Purpose | Status |
|------|---------|--------|
| `optimize_portfolio_bl` | BL portfolio optimization | Extended |
| `backtest_portfolio` | Portfolio backtesting | Extended |
| `get_asset_stats` | Asset stats/correlation lookup | NEW |
| `upload_price_data` | Upload custom price data | Done |
| `list_available_tickers` | List available tickers | Done |

---

## PR #22 (Closes #17, #18, #19, #20)

**Branch**: `feat/phase-3-implementation`
**Status**: Open

**Changes included**:
- get_asset_stats new tool
- backtest_portfolio extensions (timeseries, drawdown_details, compare_strategies)
- optimize_portfolio_bl extensions (sensitivity_range)
- _visualization_hint added to all tools
- README Use Cases section added
- 5 backtest tests added

---

## Next Steps

- [ ] PR #22 review and merge
- [ ] PyPI v0.3.0 release
- [ ] `upload_price_data` integration (prices + file_path)
- [ ] bl-orchestrator project creation (separate)

---

## Reference

- Core context: `CLAUDE.md` (auto-loaded by Claude Code)
- Detailed history: `memory-bank/progress.md`
