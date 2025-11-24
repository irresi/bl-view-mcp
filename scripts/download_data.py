"""
Download historical price data using yfinance and save to Parquet files.

Usage:
    python scripts/download_data.py --tickers AAPL MSFT GOOGL
    python scripts/download_data.py --tickers AAPL MSFT --start 2023-01-01
"""

import argparse
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

warnings.filterwarnings('ignore')


def get_last_date_from_parquet(filepath: Path) -> str | None:
    """Get the last date from existing Parquet file for incremental updates."""
    if not filepath.exists():
        return None
    
    try:
        df = pd.read_parquet(filepath)
        if df.empty or df.index.empty:
            return None
        
        # Assume index is DatetimeIndex
        last_date = df.index.max()
        # Start from next day
        return (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
    except Exception as e:
        print(f"Warning: Could not read existing file {filepath}: {e}")
        return None


def download_and_save(
    ticker: str,
    start_date: str,
    end_date: str,
    output_dir: Path,
    use_session: bool = False
) -> bool:
    """Download data for a single ticker and save to Parquet."""
    
    filepath = output_dir / f"{ticker}.parquet"
    
    # Check for existing data
    existing_start = get_last_date_from_parquet(filepath)
    if existing_start:
        print(f"{ticker}: Found existing data, updating from {existing_start}")
        start_date = existing_start
    
    # Skip if already up to date
    if existing_start and existing_start >= end_date:
        print(f"{ticker}: Already up to date")
        return True
    
    try:
        # Download data
        print(f"{ticker}: Downloading {start_date} to {end_date}...")
        
        # Optional: Use curl_cffi session to avoid rate limits
        # Requires: pip install curl-cffi
        session = None
        if use_session:
            try:
                from curl_cffi.requests import Session
                session = Session(impersonate="chrome110")
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
            except ImportError:
                print("Warning: curl-cffi not installed, using default yfinance session")
        
        df = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            progress=False,
            session=session
        )
        
        if df.empty:
            print(f"{ticker}: No data returned")
            return False
        
        # Ensure DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Append to existing data if present
        if filepath.exists():
            existing_df = pd.read_parquet(filepath)
            df = pd.concat([existing_df, df])
            # Remove duplicates, keep last
            df = df[~df.index.duplicated(keep='last')]
            df = df.sort_index()
            print(f"{ticker}: Added {len(df) - len(existing_df)} new rows")
        else:
            print(f"{ticker}: Saved {len(df)} rows")
        
        # Save to Parquet
        df.to_parquet(filepath, engine='pyarrow')
        return True
        
    except Exception as e:
        print(f"{ticker}: Error - {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download historical price data and save to Parquet files"
    )
    parser.add_argument(
        '--tickers',
        nargs='+',
        required=True,
        help='Ticker symbols (e.g., AAPL MSFT GOOGL)'
    )
    parser.add_argument(
        '--start',
        default='1980-01-01',
        help='Start date (YYYY-MM-DD), default: 1980-01-01 (maximum historical data)'
    )
    parser.add_argument(
        '--end',
        default=None,
        help='End date (YYYY-MM-DD), default: today'
    )
    parser.add_argument(
        '--output',
        default='data',
        help='Output directory, default: data/'
    )
    parser.add_argument(
        '--use-session',
        action='store_true',
        help='Use curl_cffi session to avoid rate limits (requires curl-cffi)'
    )
    
    args = parser.parse_args()
    
    # Setup
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    end_date = args.end or datetime.now().strftime('%Y-%m-%d')
    
    print(f"Downloading {len(args.tickers)} tickers from {args.start} to {end_date}")
    print(f"Output directory: {output_dir.absolute()}")
    print("-" * 60)
    
    # Download each ticker
    success_count = 0
    for ticker in args.tickers:
        if download_and_save(
            ticker,
            args.start,
            end_date,
            output_dir,
            args.use_session
        ):
            success_count += 1
    
    print("-" * 60)
    print(f"Completed: {success_count}/{len(args.tickers)} successful")


if __name__ == "__main__":
    main()
