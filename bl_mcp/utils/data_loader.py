"""Data loading utilities for Black-Litterman MCP server."""

import os
import tarfile
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf


def get_default_data_dir() -> str:
    """
    Get the default data directory path.

    Priority:
    1. BL_DATA_DIR environment variable (explicit override)
    2. ~/.black-litterman/data (user home directory - always writable)

    This ensures the MCP server works even when run from read-only
    locations like Claude Desktop (which runs from root /).
    """
    # Check environment variable first
    env_dir = os.getenv("BL_DATA_DIR")
    if env_dir:
        return env_dir

    # Use home directory (always writable)
    home_data_dir = os.path.expanduser("~/.black-litterman/data")
    return home_data_dir


# Default data directory - used throughout the module
DEFAULT_DATA_DIR = get_default_data_dir()


# Dataset configurations
DATASET_CONFIGS = {
    "snp500": {
        "release_tag": "data-snp500-latest",
        "fallback_tag": "data-v1.0",  # Legacy tag
        "description": "S&P 500 stocks",
    },
    "nasdaq100": {
        "release_tag": "data-nasdaq100-latest",
        "description": "NASDAQ 100 stocks",
    },
    "etf": {
        "release_tag": "data-etf-latest",
        "description": "Popular ETFs",
    },
    "crypto": {
        "release_tag": "data-crypto-latest",
        "description": "Top 100 cryptocurrencies",
    },
}

GITHUB_RELEASE_BASE = "https://github.com/irresi/bl-view-mcp/releases/download"


def ensure_data_available(data_dir: str | None = None, dataset: str = "snp500") -> None:
    """
    Ensure data is available by downloading from GitHub Release if needed.

    This function checks if data files exist, and if not, automatically downloads
    the pre-packaged data from GitHub Release. This enables zero-configuration
    setup for MCP server users.

    Args:
        data_dir: Directory to store data files
        dataset: Dataset to download ("snp500", "nyse", "etf", "crypto")

    Note:
        Downloads data.tar.gz from GitHub Release on first run.
        Data is cached locally for subsequent runs.
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
    data_path = Path(data_dir)

    # Check if data directory exists and has parquet files
    if data_path.exists() and list(data_path.glob("*.parquet")):
        return  # Data already available

    # Get dataset config
    config = DATASET_CONFIGS.get(dataset, DATASET_CONFIGS["snp500"])
    description = config.get("description", dataset)

    print(f"📥 First run detected. Downloading {description} data from GitHub Release...")
    print("   This is a one-time download...")

    # Create data directory
    data_path.mkdir(parents=True, exist_ok=True)

    # Try primary release tag, then fallback
    release_tags = [config["release_tag"]]
    if "fallback_tag" in config:
        release_tags.append(config["fallback_tag"])

    # Use temp file in parent directory of data_path (writable location)
    tar_path = data_path.parent / "data.tar.gz"
    download_success = False

    def _download_progress(block_num: int, block_size: int, total_size: int) -> None:
        """Report download progress to prevent LLM timeout."""
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 // total_size)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            # Print progress every 10%
            if block_num == 0 or percent % 10 == 0:
                print(f"   Downloading: {mb_downloaded:.1f}/{mb_total:.1f} MB ({percent}%)")

    for tag in release_tags:
        release_url = f"{GITHUB_RELEASE_BASE}/{tag}/data.tar.gz"
        try:
            print(f"   Trying {release_url}...")
            urllib.request.urlretrieve(release_url, str(tar_path), reporthook=_download_progress)
            download_success = True
            break
        except Exception as e:
            print(f"   ⚠️  Failed with tag '{tag}': {e}")
            continue

    if not download_success:
        print(f"❌ Could not download {dataset} data from any release tag.")
        print(f"   Please run 'make data-{dataset}' to download from source.")
        raise RuntimeError(f"Failed to download {dataset} data")

    try:
        # Extract tar.gz to parent directory (tar contains 'data/' folder)
        print("   Extracting files...")
        with tarfile.open(str(tar_path), "r:gz") as tar:
            tar.extractall(str(data_path.parent))

        # Clean up tar file
        tar_path.unlink()

        # Verify download
        file_count = len(list(data_path.glob("*.parquet")))
        print(f"✅ Successfully downloaded {file_count} data files!")

    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        raise


def _fetch_and_save_ticker(ticker: str, data_dir: str | None = None) -> bool:
    """
    Fetch ticker data from yfinance and save to Parquet.

    Args:
        ticker: Ticker symbol (e.g., "AAPL", "MSFT", "NVDA")
        data_dir: Directory to save Parquet file

    Returns:
        True if successful, False otherwise
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
    try:
        print(f"📥 Downloading {ticker} data from yfinance...")
        data = yf.download(ticker, period="10y", progress=False)

        if data.empty:
            return False

        # Save to Parquet
        data_path = Path(data_dir)
        data_path.mkdir(parents=True, exist_ok=True)
        file_path = data_path / f"{ticker}.parquet"
        data.to_parquet(file_path)
        print(f"✅ Saved {ticker} data to {file_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {ticker}: {e}")
        return False


def load_prices(
    tickers: list[str],
    start_date: str,
    end_date: Optional[str] = None,
    data_dir: str | None = None
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
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
    # Ensure data is available (auto-download on first run)
    ensure_data_available(data_dir)
    
    data_path = Path(data_dir)
    all_prices = {}
    
    for ticker in tickers:
        file_path = data_path / f"{ticker}.parquet"
        
        if not file_path.exists():
            # Try to download from yfinance
            if not _fetch_and_save_ticker(ticker, data_dir):
                raise FileNotFoundError(
                    f"Data file not found for {ticker} and failed to download. "
                    f"Please check the ticker symbol."
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
    market_cap_file: str | None = None
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
    if market_cap_file is None:
        market_cap_file = f"{DEFAULT_DATA_DIR}/market_caps.parquet"
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


# Custom ticker tracking file
CUSTOM_TICKERS_FILE = "data/custom_tickers.json"


def save_custom_price_data(
    ticker: str,
    prices: list[dict],
    source: str = "user",
    data_dir: str | None = None
) -> dict:
    """
    Save custom price data uploaded by user or external MCP.

    Args:
        ticker: Ticker symbol
        prices: List of {"date": "YYYY-MM-DD", "close": float}
        source: Source identifier for audit
        data_dir: Directory to save data

    Returns:
        Result dict with success status and metadata
    """
    import json

    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR

    # Validate input
    if not prices:
        raise ValueError("prices list cannot be empty")

    if len(prices) < 10:
        raise ValueError(
            f"Minimum 10 data points required, got {len(prices)}. "
            "For reliable optimization, 60+ days recommended."
        )

    # Parse and validate prices
    records = []
    for i, p in enumerate(prices):
        if "date" not in p or "close" not in p:
            raise ValueError(
                f"Record {i} missing required fields. "
                "Each record must have 'date' and 'close' keys."
            )
        try:
            date = pd.to_datetime(p["date"])
            close = float(p["close"])
            records.append({"Date": date, "Close": close})
        except Exception as e:
            raise ValueError(f"Invalid data at record {i}: {e}")

    # Create DataFrame
    df = pd.DataFrame(records)
    df = df.set_index("Date")
    df = df.sort_index()

    # Save to Parquet
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    file_path = data_path / f"{ticker}.parquet"
    df.to_parquet(file_path)

    # Track custom ticker
    _register_custom_ticker(ticker, source, data_dir)

    return {
        "ticker": ticker,
        "records": len(df),
        "date_range": {
            "start": df.index.min().strftime("%Y-%m-%d"),
            "end": df.index.max().strftime("%Y-%m-%d")
        },
        "file_path": str(file_path),
        "source": source
    }


def load_and_save_from_file(
    ticker: str,
    file_path: str,
    date_column: str = "date",
    close_column: str = "close",
    source: str = "file",
    data_dir: str | None = None
) -> dict:
    """
    Load price data from external file and save to internal format.

    Args:
        ticker: Ticker symbol to use
        file_path: Path to CSV or Parquet file
        date_column: Column name for dates
        close_column: Column name for close prices
        source: Source identifier
        data_dir: Directory to save data

    Returns:
        Result dict with success status and metadata
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Load based on file extension
    if file_path.suffix.lower() == ".parquet":
        df = pd.read_parquet(file_path)
    elif file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
    else:
        raise ValueError(
            f"Unsupported file format: {file_path.suffix}. "
            "Supported: .csv, .parquet"
        )

    # Find columns (case-insensitive)
    columns_lower = {c.lower(): c for c in df.columns}

    date_col = columns_lower.get(date_column.lower())
    close_col = columns_lower.get(close_column.lower())

    if date_col is None:
        raise ValueError(
            f"Date column '{date_column}' not found. "
            f"Available columns: {list(df.columns)}"
        )
    if close_col is None:
        raise ValueError(
            f"Close column '{close_column}' not found. "
            f"Available columns: {list(df.columns)}"
        )

    # Convert to standard format
    prices = [
        {"date": str(row[date_col]), "close": float(row[close_col])}
        for _, row in df.iterrows()
    ]

    return save_custom_price_data(ticker, prices, source, data_dir)


def _register_custom_ticker(
    ticker: str,
    source: str,
    data_dir: str | None = None
) -> None:
    """Register a custom ticker in tracking file."""
    import json
    from datetime import datetime

    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR

    tracking_file = Path(data_dir) / "custom_tickers.json"

    # Load existing
    custom_tickers = {}
    if tracking_file.exists():
        try:
            with open(tracking_file) as f:
                custom_tickers = json.load(f)
        except Exception:
            pass

    # Add/update ticker
    custom_tickers[ticker] = {
        "source": source,
        "uploaded_at": datetime.now().isoformat()
    }

    # Save
    tracking_file.parent.mkdir(parents=True, exist_ok=True)
    with open(tracking_file, "w") as f:
        json.dump(custom_tickers, f, indent=2)


def list_tickers(
    dataset: str | None = None,
    search: str | None = None,
    data_dir: str | None = None
) -> dict:
    """
    List available tickers.

    Args:
        dataset: Filter by dataset ("snp500", "nasdaq100", "etf", "crypto", "custom")
        search: Search pattern (case-insensitive)
        data_dir: Data directory

    Returns:
        Dict with tickers list and metadata
    """
    import json

    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR

    data_path = Path(data_dir)

    # Get all parquet files
    all_tickers = []
    if data_path.exists():
        all_tickers = [
            f.stem for f in data_path.glob("*.parquet")
            if not f.stem.startswith(".")
            and f.stem != "market_caps"
        ]

    # Load custom tickers list
    custom_tickers = {}
    tracking_file = data_path / "custom_tickers.json"
    if tracking_file.exists():
        try:
            with open(tracking_file) as f:
                custom_tickers = json.load(f)
        except Exception:
            pass

    custom_ticker_list = list(custom_tickers.keys())

    # Filter by dataset
    result_tickers = all_tickers

    if dataset == "custom":
        result_tickers = custom_ticker_list
    elif dataset is not None:
        # For specific datasets, we'd need a mapping
        # For now, exclude custom tickers for non-custom datasets
        result_tickers = [t for t in all_tickers if t not in custom_ticker_list]

    # Apply search filter
    if search:
        search_lower = search.lower()
        result_tickers = [t for t in result_tickers if search_lower in t.lower()]

    # Sort alphabetically
    result_tickers = sorted(result_tickers)

    return {
        "tickers": result_tickers,
        "count": len(result_tickers),
        "datasets": list(DATASET_CONFIGS.keys()) + ["custom"],
        "custom_tickers": custom_ticker_list,
        "custom_count": len(custom_ticker_list)
    }
