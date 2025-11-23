"""Black-Litterman portfolio optimization tools using PyPortfolioOpt."""

from typing import Optional

import numpy as np
import pandas as pd
from pypfopt import black_litterman, expected_returns, risk_models
from pypfopt.black_litterman import BlackLittermanModel

from .utils import data_loader, validators


def _calculate_portfolio_risk_aversion(
    prices: pd.DataFrame,
    mcaps: pd.Series,
    S: pd.DataFrame,
    frequency: int = 252,
    risk_free_rate: float = 0.02
) -> float:
    """
    Calculate risk aversion using portfolio-based approach (Idzorek method).

    Formula: δ = (E(r) - rf) / σ²_portfolio
    where σ²_portfolio = w_mkt^T × Σ × w_mkt

    This approach uses the actual portfolio's market cap weights and covariance,
    rather than relying on a single market proxy (e.g., SPY).

    Args:
        prices: Historical price data for portfolio assets
        mcaps: Market capitalizations for each asset
        S: Covariance matrix (annualized, from Ledoit-Wolf shrinkage)
        frequency: Trading days per year (default: 252)
        risk_free_rate: Annual risk-free rate (default: 0.02)

    Returns:
        Risk aversion coefficient (δ)
    """
    # 1. Calculate market cap weights
    w_mkt = mcaps / mcaps.sum()

    # 2. Calculate portfolio variance: w^T × Σ × w
    portfolio_var = float(w_mkt @ S @ w_mkt)

    # 3. Calculate portfolio expected return (market cap weighted average)
    returns = prices.pct_change().dropna()
    mean_returns = returns.mean() * frequency  # Annualized
    portfolio_return = float((w_mkt * mean_returns).sum())

    # 4. Calculate risk aversion: δ = (E(r) - rf) / σ²
    if portfolio_var <= 0:
        return 2.5  # Fallback for edge case

    delta = (portfolio_return - risk_free_rate) / portfolio_var

    # Ensure reasonable bounds (typically 1-10 for equities)
    return max(0.5, min(delta, 15.0))


def _parse_views(views: dict, tickers: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert view formats to P, Q matrices.
    
    Supports two formats:
    1. Dict-based P: {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
       - Absolute view: {"P": [{"AAPL": 1}], "Q": [0.10]}
       - Relative view: {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
    2. NumPy P: {"P": [[1, -1, 0]], "Q": [0.20]}
    
    Args:
        views: Views in P, Q format (dict or NumPy)
        tickers: List of ticker symbols in portfolio
        
    Returns:
        Tuple of (P matrix, Q vector) as numpy arrays
        
    Raises:
        ValueError: If views format is invalid or contains unknown tickers
    """
    # Ensure P, Q format is used
    if "P" not in views or "Q" not in views:
        raise ValueError(
            "Views must use P, Q format. "
            "Examples:\n"
            "  Absolute view: {'P': [{'AAPL': 1}], 'Q': [0.10]}\n"
            "  Relative view: {'P': [{'NVDA': 1, 'AAPL': -1}], 'Q': [0.20]}\n"
            "  NumPy format: {'P': [[1, -1, 0]], 'Q': [0.20]}"
        )
    
    # Parse P and Q
    P_input = views["P"]
    Q = np.array(views["Q"])
    
    # Validate Q
    if Q is None or len(Q) == 0:
        raise ValueError("Q cannot be empty")
    
    # Validate P
    if len(P_input) == 0:
        raise ValueError("P matrix cannot be empty")
    
    if isinstance(P_input[0], dict):
        # Dict-based P: [{"NVDA": 1, "AAPL": -1}, ...]
        P = np.zeros((len(P_input), len(tickers)))
        for i, view_dict in enumerate(P_input):
            for ticker, weight in view_dict.items():
                if ticker not in tickers:
                    raise ValueError(
                        f"Ticker '{ticker}' in P matrix not found in tickers list. "
                        f"Available tickers: {tickers}"
                    )
                j = tickers.index(ticker)
                P[i, j] = weight
    else:
        # NumPy P: [[1, -1, 0], ...]
        P = np.array(P_input)
        
        # Validate dimensions
        if P.shape[1] != len(tickers):
            raise ValueError(
                f"P matrix has {P.shape[1]} columns but there are {len(tickers)} tickers. "
                f"Dimensions must match."
            )
    
    # Validate P and Q dimensions match
    if P.shape[0] != len(Q):
        raise ValueError(
            f"P matrix has {P.shape[0]} rows but Q has {len(Q)} elements. "
            f"Number of views must match."
        )
    
    return P, Q


def _normalize_confidence(
    confidence: float | list | None,
    views: dict,
    tickers: list[str]
) -> list[float]:
    """
    Normalize confidence to list format.
    
    Handles confidence input types and converts to list:
    - None → [0.5, 0.5, ...] (default neutral confidence)
    - Float → [value, value, ...] (same confidence for all views)
    - List → validate and return (per-view confidence)
    
    Args:
        confidence: Confidence in float or list format
        views: Views dict (to determine number of views)
        tickers: List of tickers (unused, kept for compatibility)
        
    Returns:
        List of confidence values (one per view)
        
    Raises:
        ValueError: If confidence format is invalid or length doesn't match views
        TypeError: If confidence type is not supported
    """
    # Determine number of views from Q
    num_views = len(views["Q"])
    
    # Normalize to list based on input type
    if confidence is None:
        # Default: neutral confidence
        return [0.5] * num_views
    
    elif isinstance(confidence, (int, float)):
        # Single value: apply to all views
        validated = validators.validate_confidence(confidence)
        return [validated] * num_views
    
    elif isinstance(confidence, list):
        # List: validate length and values
        if len(confidence) != num_views:
            raise ValueError(
                f"Confidence length ({len(confidence)}) must match "
                f"number of views ({num_views})"
            )
        
        # Validate each confidence value
        validated_list = []
        for i, conf in enumerate(confidence):
            validated = validators.validate_confidence(conf)
            validated_list.append(validated)
        return validated_list
    
    else:
        raise TypeError(
            f"Invalid confidence type: {type(confidence).__name__}. "
            f"Expected float, list, or None"
        )


def optimize_portfolio_bl(
    tickers: list[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    views: Optional[dict] = None,
    confidence: Optional[float | list] = None,  # Can be float or list
    investment_style: str = "balanced",
    risk_aversion: Optional[float] = None  # Advanced parameter (last)
) -> dict:
    """
    Optimize portfolio using Black-Litterman model.
    
    This is the main optimization tool that combines market equilibrium with your views
    to produce optimal portfolio weights. It uses the Black-Litterman approach:
    - Starts with market-implied equilibrium returns (prior)
    - Incorporates your views with specified confidence (likelihood)
    - Produces posterior returns and optimal weights
    
    Date Range Options (mutually exclusive):
        - Provide 'period' for recent data (RECOMMENDED): "1Y", "3M", "1W"
        - Provide 'start_date' for historical data: "2023-01-01"
        - If both provided, 'start_date' takes precedence
        - If neither provided, defaults to "1Y" (1 year)
    
    Args:
        tickers: List of ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        start_date: Specific start date (YYYY-MM-DD). Use for absolute time ranges.
                   Only use if 'period' is not suitable. Do NOT use with 'period'.
        end_date: Specific end date (YYYY-MM-DD). Defaults to today if not provided.
        period: Relative period from today (e.g., '1M', '2Y').
               Supported: "1D", "7D", "1W", "1M", "3M", "6M", "1Y", "2Y", "5Y"
               Do NOT use with 'start_date'.
        views: Your investment views in P, Q format (optional).
              
              Format: {"P": [...], "Q": [...]}
              
              Examples:
              1. Absolute view (single asset):
                 {"P": [{"AAPL": 1}], "Q": [0.10]}
                 - AAPL expected to return 10%
                 
              2. Relative view:
                 {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
                 - NVDA will outperform AAPL by 20%
                 
              3. Multiple views:
                 {"P": [{"NVDA": 1, "AAPL": -1}, {"NVDA": 1, "MSFT": -1}], "Q": [0.20, 0.15]}
                 - NVDA vs AAPL: 20% difference
                 - NVDA vs MSFT: 15% difference
                 
              4. NumPy format (advanced):
                 {"P": [[1, -1, 0]], "Q": [0.20]}
                 - Index-based (NVDA=0, AAPL=1, MSFT=2)
              
              If not provided or None, uses only market equilibrium (no views).
              
        confidence: How confident you are in your views (0.0 to 1.0, default: 0.5).
                   Can be:
                   - Single float: Same confidence for all views. E.g., 0.7 or 70
                   - List: Per-view confidence. E.g., [0.9, 0.8]
                   - None: Defaults to 0.5 (neutral)
                   Only used if views are provided.
                   
                   Confidence scale (Idzorek method):
                   - 0.95 (95%): Very confident
                   - 0.85 (85%): Confident
                   - 0.75 (75%): Quite confident
                   - 0.60 (60%): Somewhat confident
                   - 0.50 (50%): Neutral (default)
                   - 0.30 (30%): Uncertain
                   - 0.10 (10%): Very uncertain
        risk_aversion: Risk aversion parameter (optional, auto-calculated if not provided).
                      Higher values = more conservative (typically 2-3 for equities).
    
    Returns:
        Dictionary containing:

        Portfolio Allocation (THESE ARE WEIGHTS - sum to 100%):
        - weights: How much to invest in each asset (e.g., {"AAPL": 0.4, "MSFT": 0.6})
                  These ALWAYS sum to 100%. Use these for actual portfolio construction.

        Portfolio Performance (metrics for the TOTAL portfolio):
        - expected_return: Annualized expected return of the portfolio (e.g., 0.15 = 15%)
        - volatility: Annualized volatility/risk (e.g., 0.20 = 20%)
        - sharpe_ratio: Risk-adjusted return (expected_return / volatility)

        Individual Asset Expected Returns (NOT weights - do NOT sum to 100%):
        - prior_returns: Market equilibrium returns BEFORE views (π = δ × Σ × w_mkt)
                        These are what each asset is expected to return annually
                        based on market cap weights and covariance.
        - posterior_returns: Expected returns AFTER incorporating your views.
                            Shows how views shifted return expectations.
                            Compare with prior_returns to see view impact.

        IMPORTANT: prior_returns and posterior_returns are per-asset annual return
        expectations (e.g., NVDA: 38%, MSFT: 17%), NOT portfolio weights.
        They do NOT and should NOT sum to 100%.

        Other:
        - has_views: Whether views were incorporated (bool)
        - risk_aversion: The δ parameter used (higher = more conservative)
        - period: Data period used for calculation

    Raises:
        ValueError: Invalid tickers, views format, or insufficient data
        Exception: Other errors (MCP handles error responses automatically)
    
    Examples:
        # Absolute view
        Input: tickers=["AAPL", "MSFT", "GOOGL"], period="1Y",
               views={"P": [{"AAPL": 1}], "Q": [0.10]}, confidence=0.7
        
        # Relative view
        Input: tickers=["NVDA", "AAPL", "MSFT"], period="5Y",
               views={"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.30]}, confidence=[0.85]
    """
    # Debug logging to trace parameter values (CRITICAL for debugging!)
    import logging
    logging.warning("=" * 80)
    logging.warning(f"🔍 optimize_portfolio_bl CALLED:")
    logging.warning(f"  📋 tickers = {tickers!r}")
    logging.warning(f"  📊 views = {views!r} (type: {type(views).__name__})")
    logging.warning(f"  🎯 confidence = {confidence!r} (type: {type(confidence).__name__ if confidence else 'None'})")
    logging.warning(f"  📅 start_date = {start_date!r}")
    logging.warning(f"  📅 period = {period!r}")
    logging.warning("=" * 80)

    # Validate inputs
    validators.validate_tickers(tickers)
    validators.validate_risk_aversion(risk_aversion)

    # Note: Ticker order is preserved as provided by user
    # This is important for NumPy P format where indices matter
    logging.warning(f"  🔤 Tickers (order preserved): {tickers}")

    # CRITICAL: Check parameter types first (MCP may swap them!)
    if views is not None:
        if not isinstance(views, dict):
            # Check if views and confidence got swapped
            if isinstance(views, (int, float)) and isinstance(confidence, dict):
                # Swap them back
                logging.warning(f"⚠️ PARAMETER SWAP DETECTED! Swapping views={views} and confidence={confidence}")
                views, confidence = confidence, views
            else:
                raise ValueError(
                    f"views must be a dict or None, got {type(views).__name__}. "
                    f"Did you swap views and confidence?"
                )

    # Parse and validate views if provided
    if views:
        # Parse views to P, Q matrices (handles all three formats)
        P, Q = _parse_views(views, tickers)

        # Normalize confidence to list format
        conf_list = _normalize_confidence(confidence, views, tickers)

    # Resolve date range (handles period vs absolute dates)
    start_date, end_date = validators.resolve_date_range(
        period=period,
        start_date=start_date,
        end_date=end_date
    )

    # Load price data
    prices = data_loader.load_prices(tickers, start_date, end_date)

    # Calculate covariance matrix
    S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()

    # Get market caps automatically (Parquet cache → yfinance → equal weight fallback)
    mcaps = data_loader.get_market_caps(tickers)

    # Calculate risk aversion if not provided
    if risk_aversion is None:
        # Calculate risk aversion using portfolio-based approach (Idzorek method)
        # δ = (E(r) - rf) / σ²_portfolio
        base_risk_aversion = _calculate_portfolio_risk_aversion(
            prices,
            mcaps,
            S,  # Reuse already calculated covariance matrix
            frequency=252,  # Trading days per year
            risk_free_rate=0.02  # 2% annual risk-free rate
        )

        # Adjust based on investment style
        style_multipliers = {
            "aggressive": 0.5,    # δ × 0.5 (high concentration)
            "balanced": 1.0,      # δ × 1.0 (market equilibrium)
            "conservative": 2.0   # δ × 2.0 (high diversification)
        }

        multiplier = style_multipliers.get(investment_style, 1.0)
        risk_aversion = base_risk_aversion * multiplier

        logging.warning(
            f"  📊 Portfolio-based risk aversion (base): {base_risk_aversion:.3f}\n"
            f"  🎨 Investment style: {investment_style} (×{multiplier})\n"
            f"  🎯 Adjusted risk aversion: {risk_aversion:.3f}"
        )

    # Calculate market-implied prior returns
    market_prior = black_litterman.market_implied_prior_returns(
        mcaps, risk_aversion, S
    )

    # Create Black-Litterman model
    if views:
        # Idzorek method: User provides confidence → algorithm reverse-engineers Ω
        # P, Q (matrices) → Explicit view specification
        # conf_list (list) → Per-view confidence → Idzorek calculates optimal Ω

        bl = BlackLittermanModel(
            S,
            pi=market_prior,
            P=P,                     # Pick matrix (converted from dict/NumPy)
            Q=Q,                     # View returns vector
            omega="idzorek",         # Reverse-engineer Ω from confidence!
            view_confidences=conf_list  # Per-view confidence list
        )
        # Get posterior returns
        posterior_rets = bl.bl_returns()
        # Get optimized weights
        weights = bl.bl_weights()
        # Calculate portfolio metrics
        perf = bl.portfolio_performance(verbose=False)
    else:
        # No views: use market equilibrium weights directly
        # Market cap weighted portfolio
        weights = mcaps / mcaps.sum()
        posterior_rets = market_prior
        # Manual performance calculation for no-view case
        portfolio_return = weights.dot(posterior_rets)
        portfolio_variance = weights.dot(S).dot(weights)
        portfolio_vol = portfolio_variance ** 0.5
        sharpe = portfolio_return / portfolio_vol if portfolio_vol > 0 else 0
        perf = (portfolio_return, portfolio_vol, sharpe)

    return {
        "weights": weights,
        "expected_return": perf[0],
        "volatility": perf[1],
        "sharpe_ratio": perf[2],
        "posterior_returns": posterior_rets.to_dict(),
        "prior_returns": market_prior.to_dict(),
        "risk_aversion": risk_aversion,
        "has_views": bool(views),
        "period": {
            "start": start_date,
            "end": end_date or prices.index[-1].strftime("%Y-%m-%d"),
            "days": len(prices)
        }
    }

    # Exceptions propagate to MCP - it handles error responses automatically


# =============================================================================
# Backtest Portfolio Implementation
# =============================================================================

# Strategy preset configurations
STRATEGY_PRESETS = {
    "buy_and_hold": {
        "rebalance_frequency": "none",
        "fees": 0.001,
        "slippage": 0.0005,
        "stop_loss": None,
        "take_profit": None,
        "trailing_stop": False,
        "max_drawdown_limit": None,
    },
    "passive_rebalance": {
        "rebalance_frequency": "monthly",
        "fees": 0.001,
        "slippage": 0.0005,
        "stop_loss": None,
        "take_profit": None,
        "trailing_stop": False,
        "max_drawdown_limit": None,
    },
    "risk_managed": {
        "rebalance_frequency": "monthly",
        "fees": 0.001,
        "slippage": 0.0005,
        "stop_loss": 0.10,
        "take_profit": None,
        "trailing_stop": False,
        "max_drawdown_limit": 0.20,
    },
}


def _calculate_returns_metrics(
    returns: pd.Series,
    risk_free_rate: float = 0.02
) -> dict:
    """
    Calculate all performance metrics from daily returns.

    Args:
        returns: Daily returns series
        risk_free_rate: Annual risk-free rate (default: 2%)

    Returns:
        Dictionary with performance metrics
    """
    if len(returns) == 0:
        return {
            "total_return": 0.0,
            "cagr": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "calmar_ratio": 0.0,
        }

    # Total return
    total_return = (1 + returns).prod() - 1

    # Annualized metrics
    total_days = len(returns)
    years = total_days / 252
    if years <= 0:
        years = total_days / 252  # Minimum

    # CAGR (Compound Annual Growth Rate)
    cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

    # Volatility (annualized)
    volatility = returns.std() * np.sqrt(252)

    # Sharpe ratio
    excess_return = cagr - risk_free_rate
    sharpe = excess_return / volatility if volatility > 0 else 0

    # Sortino ratio (downside deviation)
    negative_returns = returns[returns < 0]
    if len(negative_returns) > 0:
        downside_std = negative_returns.std() * np.sqrt(252)
    else:
        downside_std = volatility
    sortino = excess_return / downside_std if downside_std > 0 else 0

    # Max drawdown
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()

    # Calmar ratio (CAGR / |Max Drawdown|)
    calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0

    return {
        "total_return": float(total_return),
        "cagr": float(cagr),
        "volatility": float(volatility),
        "sharpe_ratio": float(sharpe),
        "sortino_ratio": float(sortino),
        "max_drawdown": float(max_drawdown),
        "calmar_ratio": float(calmar),
    }


def _calculate_benchmark_metrics(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.02
) -> dict:
    """
    Calculate benchmark comparison metrics.

    Args:
        portfolio_returns: Daily portfolio returns
        benchmark_returns: Daily benchmark returns
        risk_free_rate: Annual risk-free rate

    Returns:
        Dictionary with benchmark comparison metrics
    """
    # Align dates
    common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
    if len(common_dates) == 0:
        return {
            "benchmark_return": 0.0,
            "excess_return": 0.0,
            "alpha": 0.0,
            "beta": 1.0,
            "information_ratio": 0.0,
        }

    port_ret = portfolio_returns.loc[common_dates]
    bench_ret = benchmark_returns.loc[common_dates]

    # Total returns
    portfolio_total = (1 + port_ret).prod() - 1
    benchmark_total = (1 + bench_ret).prod() - 1
    excess_return = portfolio_total - benchmark_total

    # Beta (covariance / variance)
    covariance = port_ret.cov(bench_ret)
    benchmark_variance = bench_ret.var()
    beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0

    # Alpha (Jensen's alpha)
    years = len(common_dates) / 252
    if years > 0:
        portfolio_annual = (1 + portfolio_total) ** (1 / years) - 1
        benchmark_annual = (1 + benchmark_total) ** (1 / years) - 1
        alpha = portfolio_annual - (risk_free_rate + beta * (benchmark_annual - risk_free_rate))
    else:
        alpha = 0.0

    # Information ratio (excess return / tracking error)
    tracking_diff = port_ret - bench_ret
    tracking_error = tracking_diff.std() * np.sqrt(252)
    if tracking_error > 0 and years > 0:
        information_ratio = (excess_return / years) / tracking_error
    else:
        information_ratio = 0.0

    return {
        "benchmark_return": float(benchmark_total),
        "excess_return": float(excess_return),
        "alpha": float(alpha),
        "beta": float(beta),
        "information_ratio": float(information_ratio),
    }


def _get_rebalance_dates(
    prices: pd.DataFrame,
    frequency: str
) -> pd.DatetimeIndex:
    """
    Get rebalancing dates based on frequency.

    Args:
        prices: Price DataFrame
        frequency: Rebalancing frequency

    Returns:
        DatetimeIndex of rebalancing dates
    """
    if frequency == "none":
        return pd.DatetimeIndex([prices.index[0]])

    freq_map = {
        "weekly": "W",
        "monthly": "ME",
        "quarterly": "QE",
        "semi-annual": "6ME",
        "annual": "YE",
    }

    pandas_freq = freq_map.get(frequency, "ME")

    # Get end-of-period dates, then find the next trading day
    rebalance_dates = prices.resample(pandas_freq).last().index

    # Filter to only include dates in our price data
    valid_dates = rebalance_dates.intersection(prices.index)

    # If no valid dates, use first date
    if len(valid_dates) == 0:
        return pd.DatetimeIndex([prices.index[0]])

    return valid_dates


def _simulate_portfolio(
    prices: pd.DataFrame,
    target_weights: dict[str, float],
    config: dict,
    initial_capital: float
) -> tuple[pd.Series, dict]:
    """
    Simulate portfolio with rebalancing and risk controls.

    Args:
        prices: Price DataFrame (columns = tickers)
        target_weights: Target allocation weights
        config: Backtest configuration
        initial_capital: Starting capital

    Returns:
        Tuple of (portfolio values Series, metadata dict)
    """
    # Normalize weights
    weight_sum = sum(target_weights.values())
    weights = {k: v / weight_sum for k, v in target_weights.items()}

    # Get config values
    rebalance_frequency = config.get("rebalance_frequency", "monthly")
    fees = config.get("fees", 0.001)
    slippage = config.get("slippage", 0.0005)
    stop_loss = config.get("stop_loss")
    take_profit = config.get("take_profit")
    trailing_stop = config.get("trailing_stop", False)
    max_drawdown_limit = config.get("max_drawdown_limit")

    # Get rebalance dates
    rebalance_dates = _get_rebalance_dates(prices, rebalance_frequency)

    # Initialize tracking variables
    portfolio_values = []
    current_shares = {}
    total_fees_paid = 0.0
    num_rebalances = 0
    total_turnover = 0.0

    # Risk management tracking
    entry_prices = {}  # Track entry prices for stop-loss/take-profit
    highest_prices = {}  # Track highest prices for trailing stop
    peak_portfolio_value = initial_capital
    is_liquidated = False
    liquidation_reason = None

    # Holding period tracking
    holding_start_dates = {}

    for i, date in enumerate(prices.index):
        if is_liquidated:
            # Portfolio was liquidated, maintain cash position
            portfolio_values.append(portfolio_values[-1] if portfolio_values else initial_capital)
            continue

        current_prices = prices.loc[date]

        # Calculate current portfolio value
        if i == 0:
            current_value = initial_capital
        else:
            current_value = sum(
                current_shares.get(t, 0) * current_prices[t]
                for t in weights if t in current_prices
            )

        # Update peak for drawdown calculation
        if current_value > peak_portfolio_value:
            peak_portfolio_value = current_value

        # Check max drawdown limit
        if max_drawdown_limit is not None:
            current_drawdown = (peak_portfolio_value - current_value) / peak_portfolio_value
            if current_drawdown > max_drawdown_limit:
                is_liquidated = True
                liquidation_reason = f"max_drawdown_exceeded ({current_drawdown:.2%})"
                portfolio_values.append(current_value)
                continue

        # Check stop-loss / take-profit for each position
        for ticker in list(current_shares.keys()):
            if current_shares[ticker] <= 0:
                continue

            if ticker not in entry_prices:
                continue

            entry = entry_prices[ticker]
            current = current_prices[ticker]

            # Update highest price for trailing stop
            if ticker not in highest_prices:
                highest_prices[ticker] = current
            else:
                highest_prices[ticker] = max(highest_prices[ticker], current)

            # Calculate return from entry
            if trailing_stop and stop_loss is not None:
                # Trailing stop: compare to highest price
                return_from_high = (current - highest_prices[ticker]) / highest_prices[ticker]
                if return_from_high < -stop_loss:
                    # Sell this position
                    sell_value = current_shares[ticker] * current * (1 - fees - slippage)
                    total_fees_paid += current_shares[ticker] * current * (fees + slippage)
                    current_shares[ticker] = 0
                    del entry_prices[ticker]
                    del highest_prices[ticker]
            else:
                return_from_entry = (current - entry) / entry

                # Stop-loss check
                if stop_loss is not None and return_from_entry < -stop_loss:
                    sell_value = current_shares[ticker] * current * (1 - fees - slippage)
                    total_fees_paid += current_shares[ticker] * current * (fees + slippage)
                    current_shares[ticker] = 0
                    del entry_prices[ticker]

                # Take-profit check
                if take_profit is not None and return_from_entry > take_profit:
                    sell_value = current_shares[ticker] * current * (1 - fees - slippage)
                    total_fees_paid += current_shares[ticker] * current * (fees + slippage)
                    current_shares[ticker] = 0
                    del entry_prices[ticker]

        # Rebalancing
        should_rebalance = (date in rebalance_dates) or (i == 0)

        if should_rebalance and not is_liquidated:
            # Recalculate current value after any stop-loss/take-profit
            current_value = sum(
                current_shares.get(t, 0) * current_prices[t]
                for t in weights if t in current_prices
            )
            if i == 0:
                current_value = initial_capital

            # Calculate turnover
            if current_shares and current_value > 0:
                old_weights = {
                    t: current_shares.get(t, 0) * current_prices[t] / current_value
                    for t in weights if t in current_prices
                }
                turnover = sum(abs(weights[t] - old_weights.get(t, 0)) for t in weights) / 2
                total_turnover += turnover

            # Rebalance to target weights
            for ticker in weights:
                if ticker not in current_prices:
                    continue

                target_value = current_value * weights[ticker]
                current_holding_value = current_shares.get(ticker, 0) * current_prices[ticker]
                trade_value = abs(target_value - current_holding_value)

                # Apply fees and slippage
                if trade_value > 0:
                    total_fees_paid += trade_value * (fees + slippage)

                # Update shares
                new_shares = target_value / current_prices[ticker]
                current_shares[ticker] = new_shares

                # Update entry price for new positions
                if new_shares > 0:
                    entry_prices[ticker] = current_prices[ticker]
                    highest_prices[ticker] = current_prices[ticker]
                    if ticker not in holding_start_dates:
                        holding_start_dates[ticker] = date

            num_rebalances += 1

        # Calculate final portfolio value for the day
        final_value = sum(
            current_shares.get(t, 0) * current_prices[t]
            for t in weights if t in current_prices
        )
        portfolio_values.append(final_value)

    # Create portfolio value series
    portfolio_series = pd.Series(portfolio_values, index=prices.index)

    # Calculate holding periods
    holding_periods = {}
    end_date = prices.index[-1]
    for ticker, start_date in holding_start_dates.items():
        days = (end_date - start_date).days
        holding_periods[ticker] = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "days": days,
            "years": days / 365,
            "is_long_term": days >= 365,  # For tax purposes
        }

    metadata = {
        "total_fees_paid": total_fees_paid,
        "num_rebalances": num_rebalances,
        "turnover": total_turnover,
        "is_liquidated": is_liquidated,
        "liquidation_reason": liquidation_reason,
        "holding_periods": holding_periods,
    }

    return portfolio_series, metadata


def backtest_portfolio(
    tickers: list[str],
    weights: dict[str, float],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    strategy: str = "passive_rebalance",
    benchmark: Optional[str] = "SPY",
    initial_capital: float = 10000.0,
    custom_config: Optional[dict] = None
) -> dict:
    """
    Backtest a portfolio with specified weights.

    This tool evaluates how a portfolio would have performed historically,
    including realistic transaction costs and rebalancing.

    RECOMMENDED WORKFLOW:
    1. First call optimize_portfolio_bl() to get optimal weights
    2. Then call backtest_portfolio() with those weights to validate performance

    Args:
        tickers: List of ticker symbols in the portfolio
        weights: Target weights from optimize_portfolio_bl output
                 Example: {"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25}
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        period: Relative period ("1Y", "3Y", "5Y") - RECOMMENDED
        strategy: Backtesting strategy preset
                 - "buy_and_hold": No rebalancing, baseline comparison
                 - "passive_rebalance": Monthly rebalancing (DEFAULT)
                 - "risk_managed": Monthly rebalancing + stop-loss + drawdown limit
        benchmark: Benchmark ticker for comparison (default: "SPY")
                  Set to None to skip benchmark comparison
        initial_capital: Starting capital (default: 10000)
        custom_config: Advanced config to override strategy preset (dict)
                      See BacktestConfig for available options

    Returns:
        Dictionary containing performance metrics, costs, and benchmark comparison
    """
    import logging
    logging.warning("=" * 80)
    logging.warning(f"🔍 backtest_portfolio CALLED:")
    logging.warning(f"  📋 tickers = {tickers!r}")
    logging.warning(f"  ⚖️ weights = {weights!r}")
    logging.warning(f"  📅 period = {period!r}")
    logging.warning(f"  🎯 strategy = {strategy!r}")
    logging.warning("=" * 80)

    # Validate inputs
    validators.validate_tickers(tickers)

    # Convert weights to dict if pandas Series
    if hasattr(weights, 'to_dict'):
        weights = weights.to_dict()

    if not weights:
        raise ValueError("weights cannot be empty")

    # Check all weight tickers are in tickers list
    missing = set(weights.keys()) - set(tickers)
    if missing:
        raise ValueError(f"Tickers in weights not in tickers list: {missing}")

    # Validate weights are positive
    for ticker, weight in weights.items():
        if weight < 0:
            raise ValueError(f"Weight for {ticker} cannot be negative: {weight}")

    # Get configuration from strategy or custom_config
    if custom_config is not None:
        # Use custom config (override strategy)
        config = {**STRATEGY_PRESETS["passive_rebalance"], **custom_config}
    else:
        # Use strategy preset
        if strategy not in STRATEGY_PRESETS:
            raise ValueError(
                f"Unknown strategy '{strategy}'. "
                f"Available: {list(STRATEGY_PRESETS.keys())}"
            )
        config = STRATEGY_PRESETS[strategy]

    # Resolve date range
    start_date, end_date = validators.resolve_date_range(
        period=period,
        start_date=start_date,
        end_date=end_date
    )

    # Load price data
    all_tickers = list(set(tickers) | ({benchmark} if benchmark else set()))
    prices = data_loader.load_prices(all_tickers, start_date, end_date)

    # Separate benchmark
    benchmark_prices = None
    if benchmark and benchmark in prices.columns:
        benchmark_prices = prices[benchmark]

    # Get portfolio prices only
    portfolio_tickers = [t for t in tickers if t in prices.columns]
    if len(portfolio_tickers) == 0:
        raise ValueError(f"No valid tickers found in data: {tickers}")

    portfolio_prices = prices[portfolio_tickers]

    # Filter weights to only include available tickers
    available_weights = {t: weights[t] for t in portfolio_tickers if t in weights}

    # Simulate portfolio
    portfolio_values, metadata = _simulate_portfolio(
        portfolio_prices,
        available_weights,
        config,
        initial_capital
    )

    # Calculate returns
    portfolio_returns = portfolio_values.pct_change().dropna()

    # Calculate performance metrics
    metrics = _calculate_returns_metrics(portfolio_returns)

    # Add portfolio values
    metrics["initial_capital"] = initial_capital
    metrics["final_value"] = float(portfolio_values.iloc[-1])

    # Add cost and trading info
    metrics["total_fees_paid"] = metadata["total_fees_paid"]
    metrics["num_rebalances"] = metadata["num_rebalances"]
    metrics["turnover"] = metadata["turnover"]

    # Add risk management info
    metrics["is_liquidated"] = metadata["is_liquidated"]
    metrics["liquidation_reason"] = metadata["liquidation_reason"]

    # Add holding periods (for tax calculation)
    metrics["holding_periods"] = metadata["holding_periods"]

    # Benchmark comparison
    if benchmark_prices is not None:
        benchmark_returns = benchmark_prices.pct_change().dropna()
        benchmark_metrics = _calculate_benchmark_metrics(
            portfolio_returns,
            benchmark_returns
        )
        metrics.update(benchmark_metrics)

    # Period info
    metrics["period"] = {
        "start": start_date,
        "end": end_date or portfolio_prices.index[-1].strftime("%Y-%m-%d"),
        "trading_days": len(portfolio_prices),
    }

    # Strategy info
    metrics["strategy"] = strategy
    metrics["config"] = config

    return metrics
