"""
Download cryptocurrency historical price data using ccxt and save to Parquet files.

This script:
1. Uses ccxt to fetch OHLCV data from exchanges (default: Binance)
2. Downloads historical data for top cryptocurrencies
3. Saves to individual Parquet files (compatible with existing data format)

Usage:
    python scripts/download_crypto.py --start 2020-01-01
    python scripts/download_crypto.py --exchange binance --limit 50
    python scripts/download_crypto.py --quote BTC  # BTC pairs instead of USDT

Prerequisites:
    uv sync --extra crypto  # or: pip install ccxt
"""

import argparse
import warnings
from datetime import datetime, timedelta
from pathlib import Path
import time

import pandas as pd

try:
    import ccxt
except ImportError:
    print("❌ ccxt not installed. Run: uv sync --extra crypto")
    exit(1)

warnings.filterwarnings('ignore')


# Top 100 cryptocurrencies by market cap (common symbols)
CRYPTO_SYMBOLS = [
    # Top 20
    'BTC', 'ETH', 'BNB', 'XRP', 'SOL', 'ADA', 'DOGE', 'TRX', 'AVAX', 'LINK',
    'TON', 'SHIB', 'DOT', 'BCH', 'NEAR', 'MATIC', 'LTC', 'ICP', 'UNI', 'DAI',

    # 21-40
    'LEO', 'ETC', 'APT', 'ATOM', 'OP', 'FIL', 'XLM', 'HBAR', 'ARB', 'IMX',
    'VET', 'CRO', 'INJ', 'XMR', 'MKR', 'GRT', 'THETA', 'FTM', 'ALGO', 'RUNE',

    # 41-60
    'AAVE', 'FLOW', 'SAND', 'AXS', 'MANA', 'SNX', 'LDO', 'EOS', 'EGLD', 'XTZ',
    'KAVA', 'NEO', 'IOTA', 'CAKE', 'GALA', 'QNT', 'CHZ', 'ZEC', 'KLAY', 'CRV',

    # 61-80
    'COMP', 'ENJ', 'GMT', 'DYDX', 'RPL', 'BLUR', 'CFX', 'LUNC', 'RNDR', 'MINA',
    '1INCH', 'FXS', 'MASK', 'BAT', 'ROSE', 'ZIL', 'ENS', 'CELO', 'DASH', 'WOO',

    # 81-100
    'WAVES', 'AUDIO', 'ANKR', 'ICX', 'SKL', 'STORJ', 'LRC', 'YFI', 'SUSHI', 'UMA',
    'ZRX', 'BAL', 'KNC', 'REN', 'CVC', 'OMG', 'ONT', 'QTUM', 'RVN', 'PERP',
]


# Fallback exchanges in order of preference
FALLBACK_EXCHANGES = ['binance', 'coinbase', 'kraken', 'okx', 'bybit']


def get_exchange(exchange_id: str):
    """
    Initialize exchange instance.

    Args:
        exchange_id: Exchange identifier (binance, coinbase, etc.)

    Returns:
        ccxt exchange instance
    """
    exchange_class = getattr(ccxt, exchange_id, None)
    if not exchange_class:
        raise ValueError(f"Exchange '{exchange_id}' not supported by ccxt")

    exchange = exchange_class({
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
        }
    })

    return exchange


def get_exchanges_with_fallback(primary: str = 'binance') -> list:
    """
    Get list of exchanges with fallback order.

    Args:
        primary: Primary exchange to try first

    Returns:
        List of initialized exchange instances
    """
    exchanges = []

    # Primary first
    try:
        exchanges.append(get_exchange(primary))
    except Exception as e:
        print(f"⚠️  Could not initialize {primary}: {e}")

    # Add fallbacks (excluding primary)
    for ex_id in FALLBACK_EXCHANGES:
        if ex_id != primary:
            try:
                exchanges.append(get_exchange(ex_id))
            except Exception:
                pass

    return exchanges


def fetch_ohlcv_from_exchange(exchange, symbol: str, quote: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch OHLCV data for a symbol from a single exchange.

    Args:
        exchange: ccxt exchange instance
        symbol: Base symbol (e.g., 'BTC')
        quote: Quote currency (e.g., 'USDT')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        DataFrame with OHLCV data
    """
    pair = f"{symbol}/{quote}"

    # Check if pair exists on exchange
    exchange.load_markets()
    if pair not in exchange.markets:
        # Try alternative quote currencies
        alternatives = ['USDT', 'BUSD', 'USD', 'USDC']
        for alt in alternatives:
            alt_pair = f"{symbol}/{alt}"
            if alt_pair in exchange.markets:
                pair = alt_pair
                break
        else:
            return pd.DataFrame()

    # Convert dates to timestamps
    since = exchange.parse8601(f"{start_date}T00:00:00Z")
    end_ts = exchange.parse8601(f"{end_date}T23:59:59Z")

    # Fetch data in batches (most exchanges have limits)
    all_ohlcv = []
    limit = 1000  # Most exchanges support 1000 candles per request
    timeframe = '1d'  # Daily candles

    current_since = since
    while current_since < end_ts:
        try:
            ohlcv = exchange.fetch_ohlcv(pair, timeframe, since=current_since, limit=limit)
            if not ohlcv:
                break

            all_ohlcv.extend(ohlcv)

            # Move to next batch
            last_timestamp = ohlcv[-1][0]
            if last_timestamp == current_since:
                break
            current_since = last_timestamp + 86400000  # +1 day in ms

            # Respect rate limits
            time.sleep(exchange.rateLimit / 1000)

        except Exception as e:
            print(f"⚠️  Error fetching {pair}: {e}")
            break

    if not all_ohlcv:
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index('Date')
    df = df.drop(columns=['timestamp'])

    # Filter by date range
    df = df.loc[start_date:end_date]

    # Remove duplicates
    df = df[~df.index.duplicated(keep='last')]

    return df


def fetch_ohlcv_with_fallback(exchanges: list, symbol: str, quote: str,
                              start_date: str, end_date: str) -> pd.DataFrame:
    """
    Try to fetch OHLCV data from multiple exchanges with fallback.

    Args:
        exchanges: List of ccxt exchange instances to try
        symbol: Base symbol (e.g., 'BTC')
        quote: Quote currency (e.g., 'USDT')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        DataFrame with OHLCV data, or empty DataFrame if all exchanges fail
    """
    for exchange in exchanges:
        try:
            df = fetch_ohlcv_from_exchange(exchange, symbol, quote, start_date, end_date)
            if not df.empty:
                return df
        except Exception:
            continue

    return pd.DataFrame()


def download_crypto_data(exchanges: list, symbol: str, quote: str, start_date: str, end_date: str,
                         output_dir: Path, retry: int = 3) -> str:
    """
    Download crypto data for a single symbol with retry logic and exchange fallback.

    Args:
        exchanges: List of ccxt exchange instances (primary first, then fallbacks)
        symbol: Crypto symbol (e.g., 'BTC')
        quote: Quote currency (e.g., 'USDT')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        output_dir: Output directory
        retry: Number of retry attempts

    Returns:
        str: Status - 'success', 'skip', or 'failed'
    """
    # Use normalized filename (e.g., BTC-USDT.parquet)
    filename = f"{symbol}-{quote}.parquet"
    filepath = output_dir / filename

    for attempt in range(retry):
        try:
            # Check if file exists for incremental update
            if filepath.exists():
                df_existing = pd.read_parquet(filepath)
                if 'Date' in df_existing.columns:
                    df_existing = df_existing.set_index('Date')

                last_date = df_existing.index.max()

                if pd.to_datetime(last_date) >= pd.to_datetime(end_date):
                    print(f"⏭️  {symbol:6s} - Already up to date (skipped)")
                    return 'skip'

                # Incremental update
                start_date_new = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                print(f"📊 {symbol:6s} - Updating from {start_date_new}")
            else:
                start_date_new = start_date
                print(f"📥 {symbol:6s} - Downloading from {start_date}")

            # Fetch OHLCV data with fallback
            df = fetch_ohlcv_with_fallback(exchanges, symbol, quote, start_date_new, end_date)

            if df.empty:
                if filepath.exists():
                    print(f"⏭️  {symbol:6s} - No new data (skipped)")
                    return 'skip'
                else:
                    print(f"⚠️  {symbol:6s} - No data returned from any exchange")
                    return 'failed'

            # Extract Close column only (to match stock data format)
            close_series = df['Close']

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
                print(f"⚠️  {symbol:6s} - Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ {symbol:6s} - Failed after {retry} attempts: {e}")
                return 'failed'

    return 'failed'


def main():
    parser = argparse.ArgumentParser(
        description="Download cryptocurrency historical data using ccxt"
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
        '--exchange',
        default='binance',
        help='Exchange to use (binance, coinbase, kraken, etc.), default: binance'
    )
    parser.add_argument(
        '--quote',
        default='USDT',
        help='Quote currency (USDT, USD, BTC, etc.), default: USDT'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of symbols to download (for testing)'
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
        help='Save crypto symbol list to CSV'
    )

    args = parser.parse_args()

    # Setup
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    start_date = args.start
    end_date = args.end or datetime.now().strftime('%Y-%m-%d')

    symbols = CRYPTO_SYMBOLS.copy()

    # Initialize exchanges with fallback
    exchanges = get_exchanges_with_fallback(args.exchange)
    if not exchanges:
        print(f"❌ Failed to connect to any exchange")
        return

    print(f"✅ Connected to {len(exchanges)} exchange(s): {', '.join(ex.id for ex in exchanges)}")

    # Save symbol list if requested
    if args.save_list:
        list_path = output_dir / 'crypto_symbols.csv'
        pd.DataFrame({'Symbol': symbols, 'Quote': args.quote}).to_csv(list_path, index=False)
        print(f"💾 Saved symbol list to {list_path}")

    # Apply limit if specified
    if args.limit:
        symbols = symbols[:args.limit]
        print(f"📋 Limited to {len(symbols)} symbols for testing")

    print(f"\n{'='*60}")
    print(f"Downloading Crypto data")
    print(f"{'='*60}")
    print(f"Primary Exchange: {args.exchange}")
    print(f"Fallback Exchanges: {', '.join(ex.id for ex in exchanges[1:]) if len(exchanges) > 1 else 'None'}")
    print(f"Quote: {args.quote}")
    print(f"Symbols: {len(symbols)}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Output: {output_dir.absolute()}")
    print(f"{'='*60}\n")

    # Download
    success_count = 0
    skip_count = 0
    failed_symbols = []

    for i, symbol in enumerate(symbols, 1):
        print(f"[{i:3d}/{len(symbols):3d}] ", end='')

        status = download_crypto_data(
            exchanges, symbol, args.quote, start_date, end_date, output_dir
        )

        if status == 'success':
            success_count += 1
        elif status == 'skip':
            skip_count += 1
        else:
            failed_symbols.append(symbol)

        # Rate limiting
        if i < len(symbols):
            time.sleep(args.delay)

    # Summary
    print(f"\n{'='*60}")
    print(f"Download Complete!")
    print(f"{'='*60}")
    print(f"✅ Success:  {success_count}/{len(symbols)} (downloaded)")
    print(f"⏭️  Skipped:  {skip_count}/{len(symbols)} (already up to date)")
    print(f"❌ Failed:   {len(failed_symbols)}/{len(symbols)}")

    if failed_symbols:
        print(f"\n⚠️  Failed symbols:")
        for symbol in failed_symbols:
            print(f"   - {symbol}")

    print(f"\n📁 Data saved to: {output_dir.absolute()}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
