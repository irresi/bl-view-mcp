"""
Download S&P 500 historical price data using yfinance and save to Parquet files.

This script:
1. Fetches the current S&P 500 constituents from Wikipedia
2. Downloads historical data for each ticker
3. Saves to individual Parquet files

Usage:
    python scripts/download_sp500.py --start 2020-01-01
    python scripts/download_sp500.py --start 2023-01-01 --limit 50
"""

import argparse
import warnings
from datetime import datetime
from pathlib import Path
import time

import pandas as pd
import yfinance as yf

warnings.filterwarnings('ignore')


def get_sp500_tickers():
    """
    Fetch S&P 500 tickers from Wikipedia using custom session.
    
    Returns:
        tuple: (tickers list, info DataFrame or None)
    """
    
    # Wikipedia 직접 접근 with Session
    try:
        from io import StringIO
        import sys
        import os
        
        # bl_mcp.utils.session 모듈 import
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from bl_mcp.utils.session import create_session
        
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        
        # 세션 생성 (랜덤 User-Agent 자동 설정)
        session = create_session()
        
        # Session을 사용해서 HTML 가져오기
        response = session.get(url)
        response.raise_for_status()
        
        # HTML을 pandas로 파싱 (테이블 1이 S&P 500 리스트)
        df = pd.read_html(StringIO(response.text))[1]
        
        # 컬럼명 정리
        cols_ren = {
            'Security': 'Name',
            'GICS Sector': 'Sector',
            'GICS Sub-Industry': 'Industry'
        }
        df = df.rename(columns=cols_ren)
        df = df[['Symbol', 'Name', 'Sector', 'Industry']]
        df['Symbol'] = df['Symbol'].str.replace('.', '-', regex=False)
        
        tickers = df['Symbol'].tolist()
        print(f"✅ Found {len(tickers)} S&P 500 tickers from Wikipedia")
        
        return tickers, df
        
    except Exception as e:
        print(f"❌ Wikipedia also failed: {e}")
        print("Using hardcoded fallback ticker list...")
        
        # Fallback: 주요 S&P 500 종목 리스트
        sp500_tickers = [
        'AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'ADBE', 'CRM', 'ACN', 'CSCO', 'AMD',
        'INTC', 'IBM', 'QCOM', 'TXN', 'INTU', 'AMAT', 'MU', 'LRCX', 'KLAC', 'SNPS',
        'CDNS', 'MCHP', 'FTNT', 'PANW', 'ADSK', 'ANSS', 'APH', 'MSI', 'TEL', 'ADI',
        
        # Communication Services
        'GOOGL', 'GOOG', 'META', 'NFLX', 'DIS', 'CMCSA', 'VZ', 'T', 'TMUS', 'CHTR',
        'EA', 'TTWO', 'LYV', 'OMC', 'IPG', 'FOXA', 'FOX', 'MTCH', 'PARA', 'NWSA',
        
        # Consumer Discretionary
        'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'LOW', 'TJX', 'BKNG', 'ABNB',
        'MAR', 'GM', 'F', 'HLT', 'ORLY', 'AZO', 'CMG', 'YUM', 'DHI', 'LEN',
        'ROST', 'EBAY', 'APTV', 'TSCO', 'DPZ', 'GRMN', 'DECK', 'ULTA', 'BBY', 'GPC',
        
        # Consumer Staples
        'WMT', 'PG', 'COST', 'KO', 'PEP', 'PM', 'MO', 'MDLZ', 'CL', 'GIS',
        'KMB', 'STZ', 'SYY', 'KHC', 'HSY', 'K', 'CHD', 'CLX', 'TSN', 'CAG',
        
        # Financials
        'BRK-B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'MS', 'GS', 'SPGI', 'BLK',
        'C', 'SCHW', 'AXP', 'CB', 'PGR', 'MMC', 'AON', 'ICE', 'CME', 'USB',
        'PNC', 'TFC', 'COF', 'AIG', 'MET', 'PRU', 'AFL', 'ALL', 'TRV', 'AJG',
        
        # Healthcare
        'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'PFE', 'BMY',
        'AMGN', 'ISRG', 'VRTX', 'CVS', 'GILD', 'CI', 'ELV', 'HCA', 'REGN', 'MCK',
        'BSX', 'ZTS', 'MDT', 'SYK', 'HUM', 'IQV', 'BDX', 'IDXX', 'COR', 'A',
        
        # Industrials
        'BA', 'CAT', 'HON', 'RTX', 'UNP', 'DE', 'LMT', 'GE', 'UPS', 'ADP',
        'MMM', 'ETN', 'ITW', 'EMR', 'GD', 'NOC', 'FDX', 'CSX', 'NSC', 'WM',
        'PCAR', 'JCI', 'TDG', 'CMI', 'PH', 'CARR', 'OTIS', 'ODFL', 'VRSK', 'PAYX',
        
        # Energy
        'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'WMB',
        'HAL', 'HES', 'KMI', 'FANG', 'DVN', 'BKR', 'TRGP', 'EQT', 'OKE', 'CTRA',
        
        # Materials
        'LIN', 'APD', 'ECL', 'SHW', 'FCX', 'NEM', 'DOW', 'DD', 'NUE', 'PPG',
        'VMC', 'MLM', 'CTVA', 'ALB', 'BALL', 'AVY', 'CF', 'MOS', 'FMC', 'EMN',
        
        # Utilities
        'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'XEL', 'PEG', 'ED',
        'WEC', 'ES', 'DTE', 'FE', 'ETR', 'AWK', 'PPL', 'AEE', 'CNP', 'CMS',
        
        # Real Estate
        'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'SPG', 'O', 'WELL', 'DLR', 'VICI',
        'AVB', 'EQR', 'SBAC', 'VTR', 'EXR', 'INVH', 'MAA', 'ARE', 'UDR', 'ESS',
    ]
    
    # 중복 제거
    sp500_tickers = list(dict.fromkeys(sp500_tickers))  # 순서 유지하며 중복 제거
    
    print(f"✅ Loaded {len(sp500_tickers)} S&P 500 tickers")
    
    return sp500_tickers, None


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
                # 업데이트 시도했는데 새 데이터 없음 = skip (이미 최신)
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
                    # Single column DataFrame
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
        description="Download S&P 500 historical data"
    )
    parser.add_argument(
        '--start',
        default=None,
        help='Start date (YYYY-MM-DD), default: None (all available historical data)'
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
        help='Save S&P 500 ticker list to CSV'
    )
    
    args = parser.parse_args()
    
    # Setup
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    start_date = args.start or "all available data"
    end_date = args.end or datetime.now().strftime('%Y-%m-%d')
    
    # Get S&P 500 tickers
    tickers, info_df = get_sp500_tickers()
    
    # Save ticker list if requested
    if args.save_list and info_df is not None:
        list_path = output_dir / 'sp500_tickers.csv'
        info_df.to_csv(list_path, index=False)
        print(f"💾 Saved ticker list to {list_path}")
    
    # Apply limit if specified
    if args.limit:
        tickers = tickers[:args.limit]
        print(f"📋 Limited to {len(tickers)} tickers for testing")
    
    print(f"\n{'='*60}")
    print(f"Downloading S&P 500 data")
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
        else:  # 'failed'
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
