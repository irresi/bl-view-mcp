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
    print("TEST: Basic Portfolio Optimization")
    print("=" * 60)
    
    result = tools.optimize_portfolio_bl(
        tickers=["AAPL", "MSFT", "GOOGL"],
        start_date="2023-01-01"
    )
    
    if result["success"]:
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
    else:
        print(f"\n❌ Failed: {result['error']}")


def test_optimize_with_views():
    """Test optimization with investor views."""
    
    print("\n" + "=" * 60)
    print("TEST: Optimization with Views (AAPL +10%, 70% confidence)")
    print("=" * 60)
    
    result = tools.optimize_portfolio_bl(
        tickers=["AAPL", "MSFT", "GOOGL"],
        start_date="2023-01-01",
        views={"AAPL": 0.10},  # Expect 10% return
        confidence=0.7
    )
    
    if result["success"]:
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
        
    else:
        print(f"\n❌ Failed: {result['error']}")


def test_expected_returns():
    """Test expected returns calculation."""
    
    print("\n" + "=" * 60)
    print("TEST: Expected Returns Calculation")
    print("=" * 60)
    
    result = tools.calculate_expected_returns(
        tickers=["AAPL", "MSFT", "GOOGL"],
        start_date="2023-01-01"
    )
    
    if result["success"]:
        print("\n✅ Success!")
        print(f"\n📊 Expected Returns:")
        for ticker, ret in result["expected_returns"].items():
            print(f"  {ticker}: {ret:.2%}")
    else:
        print(f"\n❌ Failed: {result['error']}")
        if 'traceback' in result:
            print(f"\n{result['traceback']}")


def test_covariance():
    """Test covariance matrix calculation."""
    
    print("\n" + "=" * 60)
    print("TEST: Covariance Matrix Calculation")
    print("=" * 60)
    
    result = tools.calculate_covariance_matrix(
        tickers=["AAPL", "MSFT", "GOOGL"],
        start_date="2023-01-01"
    )
    
    if result["success"]:
        print("\n✅ Success!")
        print(f"\n📊 Covariance Matrix (volatilities):")
        for ticker in result["tickers"]:
            vol = result["covariance_matrix"][ticker][ticker] ** 0.5
            print(f"  {ticker}: {vol:.2%}")
    else:
        print(f"\n❌ Failed: {result['error']}")


if __name__ == "__main__":
    print("\n🧪 Black-Litterman Tools - Simple Tests\n")
    
    test_expected_returns()
    test_covariance()
    test_optimize_basic()
    test_optimize_with_views()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60 + "\n")
