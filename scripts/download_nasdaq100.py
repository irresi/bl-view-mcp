"""
Download NASDAQ 100 historical price data using yfinance and save to Parquet files.

This script:
1. Fetches the current NASDAQ 100 constituents from Wikipedia
2. Downloads historical data for each ticker
3. Saves to individual Parquet files

Usage:
    python scripts/download_nasdaq100.py --start 2020-01-01
    python scripts/download_nasdaq100.py --start 2023-01-01 --limit 50
"""

import argparse
import warnings
from datetime import datetime
from pathlib import Path
import time

import pandas as pd
import yfinance as yf

warnings.filterwarnings('ignore')


def get_nasdaq100_tickers():
    """
    Fetch NASDAQ 100 tickers from Wikipedia using custom session.

    Returns:
        tuple: (tickers list, info DataFrame or None)
    """

    try:
        from io import StringIO
        import sys
        import os

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from bl_mcp.utils.session import create_session

        url = 'https://en.wikipedia.org/wiki/Nasdaq-100'

        session = create_session()
        response = session.get(url)
        response.raise_for_status()

        # Parse HTML tables - NASDAQ 100 components table
        tables = pd.read_html(StringIO(response.text))

        # Find the table with 'Ticker' or 'Symbol' column
        df = None
        for table in tables:
            cols = [str(c).lower() for c in table.columns]
            if 'ticker' in cols or 'symbol' in cols:
                df = table
                break

        if df is None:
            raise ValueError("Could not find NASDAQ 100 components table")

        # Normalize column names
        df.columns = [str(c).strip() for c in df.columns]

        # Find ticker column
        ticker_col = None
        for col in df.columns:
            if col.lower() in ['ticker', 'symbol']:
                ticker_col = col
                break

        if ticker_col is None:
            raise ValueError("Could not find ticker column")

        tickers = df[ticker_col].tolist()
        # Clean tickers (remove any NaN, whitespace)
        tickers = [str(t).strip() for t in tickers if pd.notna(t) and str(t).strip()]

        print(f"✅ Found {len(tickers)} NASDAQ 100 tickers from Wikipedia")

        return tickers, df

    except Exception as e:
        print(f"❌ Wikipedia fetch failed: {e}")
        print("Using hardcoded fallback ticker list...")

        # Fallback: NASDAQ 100 tickers (as of 2024)
        nasdaq100_tickers = [
            # Top 20
            'NVDA', 'AAPL', 'MSFT', 'AMZN', 'META', 'GOOGL', 'GOOG', 'AVGO', 'TSLA', 'NFLX',
            'COST', 'ASML', 'PLTR', 'AMD', 'CSCO', 'AZN', 'TMUS', 'MU', 'PEP', 'ISRG',
            # 21-40
            'LIN', 'INTU', 'AMGN', 'LRCX', 'AMAT', 'QCOM', 'INTC', 'GILD', 'BKNG', 'TXN',
            'KLAC', 'ARM', 'ADBE', 'PANW', 'CRWD', 'HON', 'ADI', 'VRTX', 'CEG', 'ADP',
            # 41-60
            'CMCSA', 'MELI', 'SBUX', 'ORLY', 'CDNS', 'MAR', 'REGN', 'CTAS', 'MDLZ', 'SNPS',
            'MNST', 'ABNB', 'MRVL', 'AEP', 'CSX', 'ADSK', 'WDAY', 'FTNT', 'IDXX', 'PYPL',
            # 61-80
            'ROST', 'DDOG', 'PCAR', 'EA', 'BKR', 'NXPI', 'ROP', 'XEL', 'EXC', 'FAST',
            'ZS', 'TTWO', 'FANG', 'AXON', 'PAYX', 'CPRT', 'TEAM', 'KDP', 'CTSH', 'GEHC',
            # 81-101
            'VRSK', 'KHC', 'CHTR', 'CSGP', 'ODFL', 'MCHP', 'BIIB', 'DXCM', 'LULU', 'TTD',
            'GFS', 'ON', 'CDW', 'SHOP', 'PDD', 'APP', 'DASH', 'TRI', 'WBD', 'MSTR', 'CCEP',
        ]

        # Remove duplicates
        nasdaq100_tickers = list(dict.fromkeys(nasdaq100_tickers))

        print(f"✅ Loaded {len(nasdaq100_tickers)} NASDAQ 100 tickers (fallback)")

        return nasdaq100_tickers, None


def download_ticker_data(ticker, start_date, end_date, output_dir, retry=3):
    """
    Download data for a single ticker with retry logic.
    """
    filepath = output_dir / f"{ticker}.parquet"

    for attempt in range(retry):
        try:
            if filepath.exists():
                df_existing = pd.read_parquet(filepath)
                if isinstance(df_existing.columns, pd.MultiIndex):
                    df_existing = df_existing['Close']
                if 'Date' in df_existing.columns:
                    df_existing = df_existing.set_index('Date')

                last_date = df_existing.index.max()

                if pd.to_datetime(last_date) >= pd.to_datetime(end_date):
                    print(f"⏭️  {ticker:6s} - Already up to date (skipped)")
                    return 'skip'

                start_date_new = (last_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                print(f"📊 {ticker:6s} - Updating from {start_date_new}")
            else:
                start_date_new = start_date
                print(f"📥 {ticker:6s} - Downloading from {start_date}")

            df = yf.download(
                ticker,
                start=start_date_new,
                end=end_date,
                progress=False
            )

            if df.empty:
                if filepath.exists():
                    print(f"⏭️  {ticker:6s} - No new data (skipped)")
                    return 'skip'
                else:
                    print(f"⚠️  {ticker:6s} - No data returned")
                    return 'failed'

            if isinstance(df.columns, pd.MultiIndex):
                df = df['Close']

            if isinstance(df, pd.DataFrame):
                if 'Close' in df.columns:
                    close_series = df['Close']
                else:
                    close_series = df.iloc[:, 0]
            else:
                close_series = df

            if not isinstance(close_series.index, pd.DatetimeIndex):
                close_series.index = pd.to_datetime(close_series.index)

            if filepath.exists():
                df_existing = pd.read_parquet(filepath)
                if 'Date' in df_existing.columns:
                    df_existing = df_existing.set_index('Date')

                if 'Close' in df_existing.columns:
                    existing_series = df_existing['Close']
                else:
                    existing_series = df_existing.iloc[:, 0]

                close_series = pd.concat([existing_series, close_series])
                close_series = close_series[~close_series.index.duplicated(keep='last')]
                close_series = close_series.sort_index()

            df_to_save = close_series.to_frame(name='Close')
            df_to_save.to_parquet(filepath, engine='pyarrow')

            return 'success'

        except Exception as e:
            if attempt < retry - 1:
                wait_time = (attempt + 1) * 2
                print(f"⚠️  {ticker:6s} - Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ {ticker:6s} - Failed after {retry} attempts: {e}")
                return 'failed'

    return 'failed'


def main():
    parser = argparse.ArgumentParser(
        description="Download NASDAQ 100 historical data"
    )
    parser.add_argument(
        '--start',
        default='2020-01-01',
        help='Start date (YYYY-MM-DD), default: 2020-01-01'
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
        '--limit',
        type=int,
        default=None,
        help='Limit number of tickers to download (for testing)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between requests in seconds (default: 0.5)'
    )
    parser.add_argument(
        '--save-list',
        action='store_true',
        help='Save NASDAQ 100 ticker list to CSV'
    )

    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    start_date = args.start
    end_date = args.end or datetime.now().strftime('%Y-%m-%d')

    tickers, info_df = get_nasdaq100_tickers()

    if args.save_list and info_df is not None:
        list_path = output_dir / 'nasdaq100_tickers.csv'
        info_df.to_csv(list_path, index=False)
        print(f"💾 Saved ticker list to {list_path}")

    if args.limit:
        tickers = tickers[:args.limit]
        print(f"📋 Limited to {len(tickers)} tickers for testing")

    print(f"\n{'='*60}")
    print(f"Downloading NASDAQ 100 data")
    print(f"{'='*60}")
    print(f"Tickers: {len(tickers)}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Output: {output_dir.absolute()}")
    print(f"{'='*60}\n")

    success_count = 0
    skip_count = 0
    failed_tickers = []

    for i, ticker in enumerate(tickers, 1):
        print(f"[{i:3d}/{len(tickers):3d}] ", end='')

        status = download_ticker_data(ticker, args.start, end_date, output_dir)

        if status == 'success':
            success_count += 1
        elif status == 'skip':
            skip_count += 1
        else:
            failed_tickers.append(ticker)

        if i < len(tickers):
            time.sleep(args.delay)

    print(f"\n{'='*60}")
    print(f"Download Complete!")
    print(f"{'='*60}")
    print(f"✅ Success:  {success_count}/{len(tickers)} (downloaded)")
    print(f"⏭️  Skipped:  {skip_count}/{len(tickers)} (already up to date)")
    print(f"❌ Failed:   {len(failed_tickers)}/{len(tickers)}")

    if failed_tickers:
        print(f"\n⚠️  Failed tickers:")
        for ticker in failed_tickers:
            print(f"   - {ticker}")

    print(f"\n📁 Data saved to: {output_dir.absolute()}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
