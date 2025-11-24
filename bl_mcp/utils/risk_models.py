"""EGARCH-based VaR calculation and risk modeling utilities."""

import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from arch import arch_model

from . import data_loader
from .validators import parse_period


def calculate_var_egarch(
    ticker: str,
    period: str = "3Y",
    confidence_level: float = 0.95
) -> dict:
    """
    Calculate VaR 95% using EGARCH(1,1) model.

    Provides a realistic return range based on historical data
    to validate overly optimistic views.

    Args:
        ticker: Target ticker for analysis (e.g., "NVDA")
        period: Data period (default: "3Y" - 3 years of daily data)
        confidence_level: VaR confidence level (default: 0.95 = 95%)

    Returns:
        Dictionary containing:
        - var_95_annual: Annualized VaR 95% value (e.g., 0.35 = 35% return)
        - percentile_5_annual: Annualized 5th percentile return
        - current_volatility: Current annualized volatility
        - egarch_params: EGARCH(1,1) model parameters
        - warning_message: Warning message to display to user
        - data_points: Number of data points used

    Raises:
        ValueError: When data is insufficient or calculation is not possible
    """
    # 1. Load price data
    import logging

    try:
        # Convert period to start_date
        period_delta = parse_period(period)
        end_date = datetime.now()
        start_date = end_date - period_delta

        logging.warning(f"Loading VaR data: ticker={ticker}, period={period}")
        logging.warning(f"  Requested period: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

        # First, search in large dataset files (sp500_prices.parquet, etc.)
        price_series = None
        data_dir = data_loader.DEFAULT_DATA_DIR

        # Attempt 1: Load from sp500_prices.parquet
        sp500_path = Path(data_dir) / "sp500_prices.parquet"
        logging.warning(f"  sp500_prices.parquet exists: {sp500_path.exists()}")

        if sp500_path.exists():
            try:
                df = pd.read_parquet(sp500_path)
                logging.warning(f"  Parquet file loaded: {len(df)} rows, {len(df.columns)} tickers")

                if ticker in df.columns:
                    price_series = df[ticker].loc[start_date.strftime("%Y-%m-%d"):end_date.strftime("%Y-%m-%d")].dropna()
                    logging.warning(f"  {ticker} data found: {len(price_series)} days")
                    if len(price_series) > 0:
                        logging.warning(f"  Actual data period: {price_series.index[0]} ~ {price_series.index[-1]}")
                else:
                    logging.warning(f"  {ticker} not found in sp500_prices.parquet")
            except Exception as e:
                logging.warning(f"  Parquet load failed: {type(e).__name__}: {e}")

        # Attempt 2: Individual ticker file or yfinance (existing method)
        if price_series is None or len(price_series) < 252:
            logging.warning(f"  Fallback: calling load_prices() (individual file or yfinance)")
            prices = data_loader.load_prices(
                [ticker],
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )

            if ticker not in prices.columns:
                raise ValueError(
                    f"Ticker {ticker} not found in price data.\n"
                    f"Insufficient data for VaR calculation. Run 'make download-data' to download data."
                )

            price_series = prices[ticker].dropna()
            logging.warning(f"  load_prices() succeeded: {len(price_series)} days")

    except Exception as e:
        logging.error(f"  Data load failed: {type(e).__name__}: {e}")
        raise ValueError(
            f"Failed to load price data for {ticker}: {e}\n"
            f"Insufficient data for VaR calculation. Run 'make download-data' to download data."
        )

    # Check minimum data requirements (at least 1 year = 252 trading days)
    if len(price_series) < 252:
        raise ValueError(
            f"Insufficient data for {ticker}: {len(price_series)} days. "
            f"At least 252 days (1 year) required for reliable VaR estimation.\n"
            f"Insufficient data for VaR calculation. Run 'make download-data' to download data."
        )

    # 2. Calculate daily returns
    returns = price_series.pct_change().dropna()

    if len(returns) < 100:
        raise ValueError(
            f"Insufficient return data for {ticker}: {len(returns)} days. "
            f"At least 100 days required."
        )

    # 3. Fit EGARCH(1,1) model
    try:
        # Convert returns to percentage (arch package prefers percentage units)
        returns_pct = returns * 100

        # Create EGARCH(1,1) model
        # mean='Zero': Assume zero mean (volatility modeling, not return prediction)
        # vol='EGARCH': Exponential GARCH (captures asymmetric volatility)
        # p=1, q=1: EGARCH(1,1)
        model = arch_model(
            returns_pct,
            mean='Zero',
            vol='EGARCH',
            p=1,
            q=1,
            rescale=False
        )

        # Fit model (suppress warnings)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = model.fit(disp='off', show_warning=False)

        # Extract EGARCH parameters
        egarch_params = {
            "omega": float(result.params.get('omega', 0)),
            "alpha": float(result.params.get('alpha[1]', 0)),
            "beta": float(result.params.get('beta[1]', 0)),
            "gamma": float(result.params.get('gamma[1]', 0))
        }

        # Conditional volatility
        conditional_vol = result.conditional_volatility
        current_vol_daily = conditional_vol.iloc[-1] / 100  # Convert from percentage to decimal

        # VaR calculation: 5th percentile assuming normal distribution (downside risk)
        # VaR_95% = sigma x z_0.05 (z_0.05 ~ -1.645 for 95% confidence)
        z_score_5 = -1.645  # 5th percentile
        var_daily = current_vol_daily * z_score_5

        # Annualization (correct formula: multiply by sqrt(252))
        var_annual = var_daily * np.sqrt(252)
        current_vol_annual = current_vol_daily * np.sqrt(252)

        # Percentile calculation (based on historical data)
        percentile_5_daily = np.percentile(returns, 5)
        percentile_95_daily = np.percentile(returns, 95)

        # Annualization (simple scaling: percentile * sqrt(252))
        # Compound calculation (1 + r)^252 - 1 is not used as it over-amplifies extreme values
        percentile_5_annual = percentile_5_daily * np.sqrt(252)
        percentile_95_annual = percentile_95_daily * np.sqrt(252)

        use_fallback = False

    except Exception as e:
        # Fallback on EGARCH fitting failure: Use historical volatility
        import logging
        logging.warning(
            f"  EGARCH model fitting failed: {type(e).__name__}: {e}"
        )
        logging.warning(f"  Fallback: using historical volatility")

        current_vol_daily = returns.std()
        current_vol_annual = current_vol_daily * np.sqrt(252)

        z_score_5 = -1.645
        var_daily = current_vol_daily * z_score_5
        var_annual = var_daily * np.sqrt(252)

        percentile_5_daily = np.percentile(returns, 5)
        percentile_95_daily = np.percentile(returns, 95)

        percentile_5_annual = (1 + percentile_5_daily) ** 252 - 1
        percentile_95_annual = (1 + percentile_95_daily) ** 252 - 1

        egarch_params = {
            "omega": None,
            "alpha": None,
            "beta": None,
            "gamma": None,
            "fallback": "historical_volatility"
        }

        use_fallback = True

    # 4. Generate warning message
    model_name = "volatility model" if not use_fallback else "historical volatility"
    warning_message = (
        f"Warning: Optimistic return prediction detected.\n\n"
        f"VaR analysis based on {model_name} (recent {period} data):\n"
        f"- 95th Percentile return: {percentile_95_annual:.1%} (annualized)\n"
        f"- Current volatility: {current_vol_annual:.1%}\n\n"
        f"Please consider more realistic returns."
    )

    return {
        "var_95_annual": float(var_annual),
        "percentile_5_annual": float(percentile_5_annual),
        "percentile_95_annual": float(percentile_95_annual),
        "current_volatility": float(current_vol_annual),
        "egarch_params": egarch_params,
        "warning_message": warning_message,
        "data_points": len(returns),
        "ticker": ticker,
        "period": period
    }
