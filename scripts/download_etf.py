"""
Download ETF historical price data using yfinance and save to Parquet files.

This script:
1. Uses a curated list of popular ETFs
2. Downloads historical data for each ticker
3. Saves to individual Parquet files

Usage:
    python scripts/download_etf.py --start 2020-01-01
    python scripts/download_etf.py --start 2023-01-01 --limit 50
"""

import argparse
import warnings
from datetime import datetime
from pathlib import Path
import time

import pandas as pd
import yfinance as yf

warnings.filterwarnings('ignore')


# Popular ETFs by category (curated list ~150 ETFs)
# Focus on high-liquidity, popular ETFs for portfolio optimization
ETF_TICKERS = [
    # === EQUITY - US Broad Market (most popular by 2024 flows) ===
    'VOO', 'SPY', 'IVV', 'VTI', 'QQQ', 'QQQM', 'IWM', 'IJH', 'IJR',
    'SPLG', 'SCHB', 'ITOT', 'VV', 'VB', 'VXF',

    # === EQUITY - US Sector ===
    'XLK', 'XLF', 'XLV', 'XLE', 'XLI', 'XLY', 'XLP', 'XLU', 'XLB', 'XLRE', 'XLC',
    'VGT', 'VFH', 'VHT', 'VDE', 'VIS', 'VCR', 'VDC', 'VPU', 'VAW',

    # === EQUITY - US Growth & Value ===
    'VUG', 'IWF', 'SCHG', 'VTV', 'IWD', 'SCHV', 'SPYG', 'SPYV',

    # === EQUITY - International Developed ===
    'VEA', 'IEFA', 'EFA', 'VXUS', 'VGK', 'EWJ', 'EWU', 'EWG',

    # === EQUITY - Emerging Markets ===
    'VWO', 'IEMG', 'EEM', 'FXI', 'MCHI', 'INDA', 'EWZ', 'EWT', 'EWY',

    # === BONDS - US Aggregate ===
    'BND', 'AGG', 'SCHZ', 'BNDX',

    # === BONDS - Treasury ===
    'SHY', 'IEF', 'TLT', 'GOVT', 'SGOV', 'VGSH', 'VGIT', 'VGLT', 'SHV',

    # === BONDS - Corporate ===
    'LQD', 'VCIT', 'VCSH', 'VCLT', 'IGIB', 'IGLB',

    # === BONDS - High Yield ===
    'HYG', 'JNK', 'USHY', 'SHYG',

    # === BONDS - TIPS & Municipal ===
    'TIP', 'VTIP', 'MUB', 'VTEB',

    # === COMMODITIES - Precious Metals ===
    'GLD', 'IAU', 'GLDM', 'SLV', 'GDX', 'GDXJ',

    # === COMMODITIES - Energy & Broad ===
    'USO', 'UNG', 'DBC', 'PDBC', 'GSG',

    # === REAL ESTATE ===
    'VNQ', 'SCHH', 'IYR', 'XLRE', 'REM',

    # === DIVIDEND & INCOME ===
    'VIG', 'SCHD', 'VYM', 'DVY', 'HDV', 'JEPI', 'JEPQ', 'DIVO',

    # === THEMATIC - Tech & Semiconductor ===
    'SOXX', 'SMH', 'IGV', 'SKYY', 'CLOU',

    # === THEMATIC - Biotech & Healthcare ===
    'XBI', 'IBB', 'ARKG',

    # === THEMATIC - Crypto (Spot Bitcoin ETFs 2024) ===
    'IBIT', 'FBTC', 'GBTC', 'BITO',

    # === THEMATIC - Clean Energy & ESG ===
    'ICLN', 'TAN', 'QCLN', 'ESGU', 'ESGV',

    # === FACTOR ETFs ===
    'MTUM', 'QUAL', 'VLUE', 'USMV', 'SPLV',

    # === LEVERAGED (use with caution) ===
    'TQQQ', 'SQQQ', 'UPRO', 'SPXU', 'SOXL', 'SOXS',

    # === MULTI-ASSET / ALLOCATION ===
    'AOR', 'AOA', 'AOK',
]

# Remove duplicates while preserving order
ETF_TICKERS = list(dict.fromkeys(ETF_TICKERS))


def download_ticker_data(ticker, start_date, end_date, output_dir, retry=3):
    """
    Download data for a single ticker with retry logic.

    Args:
        ticker: Ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        output_dir: Output directory
        retry: Number of retry attempts

    Returns:
        str: Status - 'success', 'skip', or 'failed'
    """
    filepath = output_dir / f"{ticker}.parquet"

    for attempt in range(retry):
        try:
            # Check if file exists
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

                # Incremental update
                start_date_new = (last_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                print(f"📊 {ticker:6s} - Updating from {start_date_new}")
            else:
                start_date_new = start_date
                print(f"📥 {ticker:6s} - Downloading from {start_date}")

            # Download
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

            # Handle MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df = df['Close']

            # Extract Close column
            if isinstance(df, pd.DataFrame):
                if 'Close' in df.columns:
                    close_series = df['Close']
                else:
                    close_series = df.iloc[:, 0]
            else:
                close_series = df

            # Ensure DatetimeIndex
            if not isinstance(close_series.index, pd.DatetimeIndex):
                close_series.index = pd.to_datetime(close_series.index)

            # Merge with existing data
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

            # Save as DataFrame
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
        description="Download ETF historical data"
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
        help='Save ETF ticker list to CSV'
    )

    args = parser.parse_args()

    # Setup
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    start_date = args.start
    end_date = args.end or datetime.now().strftime('%Y-%m-%d')

    tickers = ETF_TICKERS.copy()

    # Save ticker list if requested
    if args.save_list:
        list_path = output_dir / 'etf_tickers.csv'
        pd.DataFrame({'Symbol': tickers}).to_csv(list_path, index=False)
        print(f"💾 Saved ticker list to {list_path}")

    # Apply limit if specified
    if args.limit:
        tickers = tickers[:args.limit]
        print(f"📋 Limited to {len(tickers)} tickers for testing")

    print(f"\n{'='*60}")
    print(f"Downloading ETF data")
    print(f"{'='*60}")
    print(f"Tickers: {len(tickers)}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Output: {output_dir.absolute()}")
    print(f"{'='*60}\n")

    # Download
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

        # Rate limiting
        if i < len(tickers):
            time.sleep(args.delay)

    # Summary
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
