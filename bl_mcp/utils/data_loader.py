"""Data loading utilities for Black-Litterman MCP server."""

import tarfile
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf


def ensure_data_available(data_dir: str = "data") -> None:
    """
    Ensure data is available by downloading from GitHub Release if needed.
    
    This function checks if data files exist, and if not, automatically downloads
    the pre-packaged data from GitHub Release. This enables zero-configuration
    setup for MCP server users.
    
    Args:
        data_dir: Directory to store data files
        
    Note:
        Downloads ~49MB data.tar.gz from GitHub Release on first run.
        Data is cached locally for subsequent runs.
    """
    data_path = Path(data_dir)
    
    # Check if data directory exists and has parquet files
    if data_path.exists() and list(data_path.glob("*.parquet")):
        return  # Data already available
    
    print("📥 First run detected. Downloading data from GitHub Release...")
    print("   This is a one-time download (~49MB, 503 stock files)...")
    
    # Create data directory
    data_path.mkdir(parents=True, exist_ok=True)
    
    # GitHub Release URL
    release_url = "https://github.com/irresi/bl-view-mcp/releases/download/data-v1.0/data.tar.gz"
    tar_path = "data.tar.gz"
    
    try:
        # Download tar.gz file
        print(f"   Downloading from {release_url}...")
        urllib.request.urlretrieve(release_url, tar_path)
        
        # Extract tar.gz
        print("   Extracting files...")
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(".")
        
        # Clean up tar file
        Path(tar_path).unlink()
        
        # Verify download
        file_count = len(list(data_path.glob("*.parquet")))
        print(f"✅ Successfully downloaded {file_count} data files!")
        
    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        print("   Please run 'make download-data' manually or check your internet connection.")
        raise


def load_prices(
    tickers: list[str],
    start_date: str,
    end_date: Optional[str] = None,
    data_dir: str = "data"
) -> pd.DataFrame:
    """
    Load price data from Parquet files.
    
    Automatically downloads data from GitHub Release on first run if not available.
    
    Args:
        tickers: List of ticker symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), defaults to most recent date
        data_dir: Directory containing Parquet files
    
    Returns:
        DataFrame with tickers as columns and dates as index
        
    Raises:
        FileNotFoundError: If data file doesn't exist after download attempt
        ValueError: If no data available for date range
    """
    # Ensure data is available (auto-download on first run)
    ensure_data_available(data_dir)
    
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
