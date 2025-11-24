"""
Common utilities for download scripts.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import yfinance as yf


def fetch_single_market_cap(ticker: str) -> tuple[str, float | None]:
    """
    Fetch market cap for a single ticker.

    Args:
        ticker: Ticker symbol

    Returns:
        Tuple of (ticker, market_cap or None if failed)
    """
    try:
        data = yf.Ticker(ticker)
        mcap = data.info.get('marketCap')
        return ticker, mcap
    except Exception:
        return ticker, None


def download_market_caps(tickers: list[str], output_dir: Path, max_workers: int = 10) -> dict:
    """
    Download market caps for all tickers using parallel processing.

    Args:
        tickers: List of ticker symbols
        output_dir: Output directory for market_caps.parquet
        max_workers: Number of parallel workers (default: 10)

    Returns:
        Dict with success/failed counts
    """
    print(f"\n{'='*60}")
    print(f"Downloading Market Caps (parallel, {max_workers} workers)")
    print(f"{'='*60}")
    print(f"Tickers: {len(tickers)}")

    mcaps = {}
    failed = []

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_ticker = {
            executor.submit(fetch_single_market_cap, ticker): ticker
            for ticker in tickers
        }

        # Process results as they complete
        for i, future in enumerate(as_completed(future_to_ticker), 1):
            ticker = future_to_ticker[future]
            try:
                ticker, mcap = future.result()
                if mcap is not None:
                    mcaps[ticker] = mcap
                else:
                    failed.append(ticker)
            except Exception:
                failed.append(ticker)

            # Progress update every 50 tickers
            if i % 50 == 0 or i == len(tickers):
                elapsed = time.time() - start_time
                print(f"   Progress: {i}/{len(tickers)} ({elapsed:.1f}s)")

    elapsed = time.time() - start_time

    # Save to Parquet
    if mcaps:
        mcaps_file = output_dir / 'market_caps.parquet'

        # Merge with existing if present
        if mcaps_file.exists():
            try:
                existing_df = pd.read_parquet(mcaps_file)
                existing_mcaps = existing_df['MarketCap'].to_dict()
                existing_mcaps.update(mcaps)
                mcaps = existing_mcaps
            except Exception:
                pass

        df = pd.DataFrame({'MarketCap': pd.Series(mcaps)})
        df.to_parquet(mcaps_file)
        print(f"\n💾 Saved market caps to {mcaps_file}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Market Caps Download Complete!")
    print(f"{'='*60}")
    print(f"✅ Success: {len(mcaps)}/{len(tickers)}")
    print(f"❌ Failed:  {len(failed)}/{len(tickers)}")
    print(f"⏱️  Time:    {elapsed:.1f}s")

    if failed:
        print(f"\n⚠️  Failed tickers: {failed[:10]}{'...' if len(failed) > 10 else ''}")

    return {
        'success': len(mcaps),
        'failed': len(failed),
        'elapsed': elapsed
    }
