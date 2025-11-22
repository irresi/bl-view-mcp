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


def _fetch_market_caps_from_yfinance(tickers: list[str]) -> dict[str, float | None]:
    """
    Fetch market caps from yfinance API.

    Args:
        tickers: List of ticker symbols

    Returns:
        Dict mapping ticker to market cap (None if failed)
    """
    mcaps = {}
    for ticker in tickers:
        try:
            data = yf.Ticker(ticker)
            mcaps[ticker] = data.info.get('marketCap')
        except Exception:
            mcaps[ticker] = None
    return mcaps


def _save_market_caps_to_parquet(
    mcaps: dict[str, float],
    market_cap_file: str = "data/market_caps.parquet"
) -> None:
    """
    Save market caps to Parquet file for caching.

    Args:
        mcaps: Dict mapping ticker to market cap
        market_cap_file: Path to save Parquet file
    """
    market_cap_path = Path(market_cap_file)

    # Load existing data if available
    existing_data = {}
    if market_cap_path.exists():
        try:
            existing_df = pd.read_parquet(market_cap_path)
            existing_data = existing_df['MarketCap'].to_dict()
        except Exception:
            pass

    # Merge with new data
    existing_data.update(mcaps)

    # Save to Parquet
    df = pd.DataFrame({
        'MarketCap': pd.Series(existing_data)
    })
    market_cap_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(market_cap_path)


def get_market_caps(
    tickers: list[str],
    market_cap_file: str = "data/market_caps.parquet"
) -> pd.Series:
    """
    Get market capitalization data with automatic fallback.

    Tries to load from Parquet cache first, then fetches from yfinance
    for missing tickers. Falls back to equal weight if all else fails.

    Args:
        tickers: List of ticker symbols
        market_cap_file: Path to market cap Parquet file

    Returns:
        Series with tickers as index and market caps as values
    """
    market_cap_path = Path(market_cap_file)
    mcaps = {}
    missing_tickers = list(tickers)

    # Step 1: Try loading from Parquet cache
    if market_cap_path.exists():
        try:
            mcaps_df = pd.read_parquet(market_cap_path)
            for ticker in tickers:
                if ticker in mcaps_df.index:
                    mcaps[ticker] = mcaps_df.loc[ticker, 'MarketCap']
                    missing_tickers.remove(ticker)
        except Exception:
            pass

    # Step 2: Fetch missing tickers from yfinance
    if missing_tickers:
        print(f"📥 Fetching market caps from yfinance: {missing_tickers}")
        fetched = _fetch_market_caps_from_yfinance(missing_tickers)

        # Separate successful and failed fetches
        successful = {k: v for k, v in fetched.items() if v is not None}
        failed = [k for k, v in fetched.items() if v is None]

        # Add successful fetches
        mcaps.update(successful)

        # Cache successful fetches to Parquet
        if successful:
            _save_market_caps_to_parquet(successful, market_cap_file)

        # Step 3: Use equal weight for failed tickers
        if failed:
            print(f"⚠️ Could not fetch market caps for: {failed}. Using equal weight.")
            # Use median of available market caps, or 1.0 if none available
            if mcaps:
                median_mcap = pd.Series(mcaps).median()
                for ticker in failed:
                    mcaps[ticker] = median_mcap
            else:
                for ticker in failed:
                    mcaps[ticker] = 1.0

    # Ensure all tickers have values (defensive)
    for ticker in tickers:
        if ticker not in mcaps:
            mcaps[ticker] = 1.0

    # Return as Series in original ticker order
    return pd.Series({ticker: mcaps[ticker] for ticker in tickers})
