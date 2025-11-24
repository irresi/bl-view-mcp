# Progress

## Overall Progress (2025-11-25)

```
Phase 0: ████████████████████████ 100% ✓ (Preparation)
Phase 1: ████████████████████████ 100% ✓ (MVP + Simplification)
Phase 2: ████████████████████████ 100% ✓ (Backtest complete)
Phase 3: ████████████████████████ 100% ✓ (PyPI v0.3.2)
```

---

## Phase 2 Scope Decision (2025-11-23)

### Included

- [x] `backtest_portfolio` - Backtesting ✅
- ~~`calculate_hrp_weights`~~ - HRP excluded (BL focus)

### Excluded (moved to bl-orchestrator)

- ~~`generate_views_from_technicals`~~
- ~~`generate_views_from_fundamentals`~~
- ~~`generate_views_from_sentiment`~~
- ~~`get_market_data`~~
- ~~`calculate_factor_scores`~~

---

## Change History

### 2025-11-25 - v0.3.2 Release
- **README.md update**
  - Features section updated (Asset Analysis, Dashboard Generation added)
  - PyPI image paths changed to absolute URLs (raw.githubusercontent.com)
  - Demo Dashboard links changed to GitHub Pages (v0.3.1)
- **docs/ cleanup**
  - Deleted: image.png, image2.png, image3.png, WINDSURF_SETUP.md
  - Moved: screenshots/ → examples/screenshots/
  - Updated to English: ARCHITECTURE.md, CONFIDENCE_SCALE.md, IDZOREK_VERIFICATION.md, RELATIVE_VIEWS_IMPLEMENTATION.md
- **examples/ cleanup**
  - Renamed: dashboards/tool*.html → demo_*.html
- **memory-bank cleanup**
  - Deleted: productContext.md, techContext.md, systemPatterns.md, projectbrief.md, activeContext.md
  - Kept: progress.md only (CLAUDE.md covers the rest)
- **reference/ folder deleted** (~12MB removed)

### 2025-11-24 - Phase 3 Improvements (PR #22)
- **`get_asset_stats` new tool**: VaR, correlation, covariance
- **`backtest_portfolio` extensions**: timeseries, drawdown_details, compare_strategies, include_equal_weight
- **`optimize_portfolio_bl` extensions**: sensitivity_range
- **`_visualization_hint` added** to all tool responses
- **PR #22**: Closes #17, #18, #19, #20

### 2025-11-23 - PyPI v0.2.x Releases
- **v0.2.3**: Added str type for views parameter (Claude Desktop workaround)
- **v0.2.2**: Moved data directory to `~/.black-litterman/data`
- **v0.2.1**: Added backtest_portfolio

### 2025-11-23 - backtest_portfolio Implementation
- Strategy presets: buy_and_hold, passive_rebalance, risk_managed
- Custom config: rebalance_frequency, fees, stop_loss, max_drawdown_limit
- Performance metrics: CAGR, Sharpe, Sortino, Max Drawdown, Calmar
- Benchmark comparison: Alpha, Beta, Information Ratio

### 2025-11-23 - Phase 1 Simplification
- MCP Tool: 4 → 1 (`optimize_portfolio_bl`)
- Views format: P, Q only
- Confidence: float/list only
- Auto market cap loading (yfinance + Parquet cache)
- `CLAUDE.md` created

### 2025-11-22
- P, Q only API (Breaking Change)
- Relative View support
- Period parameter added

### 2025-11-21
- Phase 1 MVP complete
- S&P 500 data download (503 tickers)
- GitHub Release deployment

### 2025-11-20
- Project started
- FastMCP + PyPortfolioOpt selected
