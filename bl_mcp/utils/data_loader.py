"""Data loading utilities for Black-Litterman MCP server."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf


def load_prices(
    tickers: list[str],
    start_date: str,
    end_date: Optional[str] = None,
    data_dir: str = "data"
) -> pd.DataFrame:
    """
    Load price data from Parquet files.
    
    Args:
        tickers: List of ticker symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), defaults to most recent date
        data_dir: Directory containing Parquet files
    
    Returns:
        DataFrame with tickers as columns and dates as index
        
    Raises:
        FileNotFoundError: If data file doesn't exist
        ValueError: If no data available for date range
    """
    data_path = Path(data_dir)
    all_prices = {}
    
    for ticker in tickers:
        file_path = data_path / f"{ticker}.parquet"
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"Data file not found for {ticker}. "
                f"Please run data collection script first."
            )
        
        # Load Parquet file
        df = pd.read_parquet(file_path)
        
        # Handle MultiIndex columns (from yfinance)
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten: take only Close prices
            df = df[('Close', ticker)] if ('Close', ticker) in df.columns else df['Close']
        elif 'Close' in df.columns:
            df = df['Close']
        
        # Set Date as index if it's a column
        if 'Date' in df.index.names or df.index.name == 'Date':
            pass  # Already has Date as index
        elif hasattr(df, 'index') and isinstance(df.index, pd.DatetimeIndex):
            pass  # Already DatetimeIndex
        else:
            df.index = pd.to_datetime(df.index)
        
        # Now df should be a Series with DatetimeIndex
        # Filter by date range
        df = df.loc[start_date:end_date] if end_date else df.loc[start_date:]
        
        if df.empty:
            raise ValueError(
                f"No data available for {ticker} in date range "
                f"{start_date} to {end_date or 'present'}"
            )
        
        # Store the Close price Series
        all_prices[ticker] = df
    
    # Combine into single DataFrame (pandas will align on index)
    prices_df = pd.DataFrame(all_prices)
    
    # Ensure we have DatetimeIndex
    if not isinstance(prices_df.index, pd.DatetimeIndex):
        prices_df.index = pd.to_datetime(prices_df.index)
    
    # Drop any rows with missing data
    prices_df = prices_df.dropna()
    
    if prices_df.empty:
        raise ValueError(
            f"No overlapping data for tickers {tickers} "
            f"in date range {start_date} to {end_date or 'present'}"
        )
    
    return prices_df


def load_market_caps(
    tickers: list[str],
    market_cap_file: str = "data/market_caps.parquet"
) -> pd.Series:
    """
    Load market capitalization data.
    
    Args:
        tickers: List of ticker symbols
        market_cap_file: Path to market cap Parquet file
    
    Returns:
        Series with tickers as index and market caps as values
        
    Raises:
        FileNotFoundError: If market cap file doesn't exist
        ValueError: If tickers not found in market cap data
    """
    market_cap_path = Path(market_cap_file)
    
    if not market_cap_path.exists():
        raise FileNotFoundError(
            f"Market cap file not found: {market_cap_file}. "
            f"Using equal weights as fallback."
        )
    
    # Load market caps
    mcaps_df = pd.read_parquet(market_cap_path)
    
    # Filter for requested tickers
    missing_tickers = set(tickers) - set(mcaps_df.index)
    if missing_tickers:
        raise ValueError(
            f"Market caps not found for tickers: {missing_tickers}"
        )
    
    return mcaps_df.loc[tickers, "MarketCap"]
