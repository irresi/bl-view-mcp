"""
Simple test script for Black-Litterman MCP Tools.

Tests the tools directly without MCP server or agent.
Good for quick debugging.

Usage:
    python test_simple.py
"""

from bl_mcp import tools


def test_optimize_basic():
    """Test basic optimization without views."""

    print("=" * 60)
    print("TEST: Basic Portfolio Optimization (No Views)")
    print("=" * 60)

    try:
        result = tools.optimize_portfolio_bl(
            tickers=["AAPL", "MSFT", "GOOGL"],
            period="1Y"
        )

        print("\n✅ Success!")
        print(f"\n📊 Portfolio Weights:")
        for ticker, weight in result["weights"].items():
            print(f"  {ticker}: {weight:.2%}")

        print(f"\n📈 Performance:")
        print(f"  Expected Return: {result['expected_return']:.2%}")
        print(f"  Volatility: {result['volatility']:.2%}")
        print(f"  Sharpe Ratio: {result['sharpe_ratio']:.2f}")

        print(f"\n📅 Data Period:")
        print(f"  {result['period']['start']} to {result['period']['end']}")
        print(f"  {result['period']['days']} trading days")
    except Exception as e:
        print(f"\n❌ Failed: {e}")


def test_optimize_with_absolute_view():
    """Test optimization with absolute view (P, Q format)."""

    print("\n" + "=" * 60)
    print("TEST: Optimization with Absolute View (AAPL +10%)")
    print("=" * 60)

    try:
        result = tools.optimize_portfolio_bl(
            tickers=["AAPL", "MSFT", "GOOGL"],
            period="1Y",
            views={"P": [{"AAPL": 1}], "Q": [0.10]},  # AAPL will return 10%
            confidence=0.7
        )

        print("\n✅ Success!")
        print(f"\n📊 Portfolio Weights:")
        for ticker, weight in result["weights"].items():
            print(f"  {ticker}: {weight:.2%}")

        print(f"\n📈 Performance:")
        print(f"  Expected Return: {result['expected_return']:.2%}")
        print(f"  Volatility: {result['volatility']:.2%}")
        print(f"  Sharpe Ratio: {result['sharpe_ratio']:.2f}")

        print(f"\n🎯 View Impact:")
        print(f"  AAPL Prior Return: {result['prior_returns']['AAPL']:.2%}")
        print(f"  AAPL Posterior Return: {result['posterior_returns']['AAPL']:.2%}")
    except Exception as e:
        print(f"\n❌ Failed: {e}")


def test_optimize_with_relative_view():
    """Test optimization with relative view (P, Q format)."""

    print("\n" + "=" * 60)
    print("TEST: Optimization with Relative View (NVDA > AAPL by 20%)")
    print("=" * 60)

    try:
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]},  # NVDA outperforms AAPL by 20%
            confidence=0.85
        )

        print("\n✅ Success!")
        print(f"\n📊 Portfolio Weights:")
        for ticker, weight in result["weights"].items():
            print(f"  {ticker}: {weight:.2%}")

        print(f"\n📈 Performance:")
        print(f"  Expected Return: {result['expected_return']:.2%}")
        print(f"  Volatility: {result['volatility']:.2%}")
        print(f"  Sharpe Ratio: {result['sharpe_ratio']:.2f}")

        print(f"\n🎯 View Impact (Relative: NVDA - AAPL = 20%):")
        print(f"  NVDA Posterior: {result['posterior_returns']['NVDA']:.2%}")
        print(f"  AAPL Posterior: {result['posterior_returns']['AAPL']:.2%}")
        diff = result['posterior_returns']['NVDA'] - result['posterior_returns']['AAPL']
        print(f"  Difference: {diff:.2%}")
    except Exception as e:
        print(f"\n❌ Failed: {e}")


def test_optimize_with_numpy_p():
    """Test optimization with NumPy P format."""

    print("\n" + "=" * 60)
    print("TEST: Optimization with NumPy P Format")
    print("=" * 60)

    try:
        # Tickers order: AAPL=0, MSFT=1, GOOGL=2
        # View: AAPL will return 15%
        result = tools.optimize_portfolio_bl(
            tickers=["AAPL", "MSFT", "GOOGL"],
            period="1Y",
            views={"P": [[1, 0, 0]], "Q": [0.15]},  # First ticker (AAPL) = 15%
            confidence=0.8
        )

        print("\n✅ Success!")
        print(f"\n📊 Portfolio Weights (ticker order preserved):")
        for ticker, weight in result["weights"].items():
            print(f"  {ticker}: {weight:.2%}")

        print(f"\n🎯 View Impact (NumPy P: [1, 0, 0] → AAPL):")
        print(f"  AAPL Posterior: {result['posterior_returns']['AAPL']:.2%}")
    except Exception as e:
        print(f"\n❌ Failed: {e}")


def test_investment_styles():
    """Test different investment styles."""

    print("\n" + "=" * 60)
    print("TEST: Investment Styles (aggressive/balanced/conservative)")
    print("=" * 60)

    for style in ["aggressive", "balanced", "conservative"]:
        try:
            result = tools.optimize_portfolio_bl(
                tickers=["AAPL", "MSFT", "GOOGL"],
                period="1Y",
                investment_style=style
            )

            weights_str = ", ".join([f"{t}: {w:.1%}" for t, w in result["weights"].items()])
            print(f"\n  {style.upper()}: {weights_str}")
            print(f"    Risk Aversion: {result['risk_aversion']:.3f}")
        except Exception as e:
            print(f"\n  {style.upper()}: ❌ {e}")


def test_multiple_views():
    """Test optimization with multiple views."""

    print("\n" + "=" * 60)
    print("TEST: Multiple Views with Per-View Confidence")
    print("=" * 60)

    try:
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT", "GOOGL"],
            period="1Y",
            views={
                "P": [
                    {"NVDA": 1, "AAPL": -1},  # NVDA > AAPL by 25%
                    {"GOOGL": 1}               # GOOGL absolute 12%
                ],
                "Q": [0.25, 0.12]
            },
            confidence=[0.9, 0.6]  # Per-view confidence
        )

        print("\n✅ Success!")
        print(f"\n📊 Portfolio Weights:")
        for ticker, weight in result["weights"].items():
            print(f"  {ticker}: {weight:.2%}")

        print(f"\n🎯 Posterior Returns:")
        for ticker, ret in result['posterior_returns'].items():
            print(f"  {ticker}: {ret:.2%}")
    except Exception as e:
        print(f"\n❌ Failed: {e}")


def test_upload_price_data():
    """Test custom price data upload."""

    print("\n" + "=" * 60)
    print("TEST: Upload Custom Price Data")
    print("=" * 60)

    from bl_mcp.utils import data_loader
    import tempfile
    import os

    try:
        # Generate fake price data (100 days)
        import datetime
        prices = []
        base_price = 100.0
        start_date = datetime.date(2024, 1, 1)

        for i in range(100):
            date = start_date + datetime.timedelta(days=i)
            # Skip weekends
            if date.weekday() >= 5:
                continue
            # Random walk
            base_price *= (1 + (hash(str(date)) % 100 - 50) / 1000)
            prices.append({
                "date": date.strftime("%Y-%m-%d"),
                "close": round(base_price, 2)
            })

        # Use temp directory for test
        with tempfile.TemporaryDirectory() as tmpdir:
            result = data_loader.save_custom_price_data(
                ticker="TEST_CUSTOM",
                prices=prices,
                source="test",
                data_dir=tmpdir
            )

            print("\n✅ Upload Success!")
            print(f"  Ticker: {result['ticker']}")
            print(f"  Records: {result['records']}")
            print(f"  Date Range: {result['date_range']['start']} to {result['date_range']['end']}")
            print(f"  File: {result['file_path']}")

            # Test list_tickers
            tickers_result = data_loader.list_tickers(data_dir=tmpdir)
            print(f"\n📋 Available Tickers: {tickers_result['tickers']}")
            print(f"  Custom Tickers: {tickers_result['custom_tickers']}")

    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()


def test_list_available_tickers():
    """Test listing available tickers."""

    print("\n" + "=" * 60)
    print("TEST: List Available Tickers")
    print("=" * 60)

    from bl_mcp.utils import data_loader

    try:
        result = data_loader.list_tickers()

        print("\n✅ Success!")
        print(f"  Total Tickers: {result['count']}")
        print(f"  Available Datasets: {result['datasets']}")
        print(f"  Custom Tickers: {result['custom_count']}")

        if result['count'] > 0:
            print(f"\n  Sample Tickers (first 10):")
            for ticker in result['tickers'][:10]:
                print(f"    - {ticker}")

        # Test search
        search_result = data_loader.list_tickers(search="AAPL")
        print(f"\n  Search 'AAPL': {search_result['tickers']}")

    except Exception as e:
        print(f"\n❌ Failed: {e}")


if __name__ == "__main__":
    print("\n🧪 Black-Litterman Tools - Simple Tests\n")

    test_optimize_basic()
    test_optimize_with_absolute_view()
    test_optimize_with_relative_view()
    test_optimize_with_numpy_p()
    test_investment_styles()
    test_multiple_views()
    test_upload_price_data()
    test_list_available_tickers()

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60 + "\n")
