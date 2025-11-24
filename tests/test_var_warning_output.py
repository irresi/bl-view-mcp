"""
Test that VaR warning messages are included in return values.

This test verifies that when an 80% return prediction is input:
1. VaR warning is triggered
2. Warning message is included in the "warnings" field of the return value
3. Warning message contains all necessary information
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bl_mcp import tools


def test_var_warning_in_output():
    """Test that VaR warning is included in output for 80% return prediction"""

    print("\n" + "="*80)
    print("VaR Warning Output Test")
    print("="*80)

    # 80% return prediction (clearly exceeds 40% threshold)
    tickers = ["NVDA", "TSLA", "INTC"]
    views = {"P": [{"INTC": 1}], "Q": [0.80]}  # INTC 80% return prediction
    confidence = 0.5

    print(f"\nInput Information:")
    print(f"  Tickers: {tickers}")
    print(f"  Views: {views}")
    print(f"  Confidence: {confidence}")

    # Run optimization
    print(f"\nRunning portfolio optimization...")
    result = tools.optimize_portfolio_bl(
        tickers=tickers,
        period="1Y",
        views=views,
        confidence=confidence
    )

    # Check results
    print(f"\nOptimization complete!")
    print(f"\nPortfolio allocation:")
    for ticker, weight in result["weights"].items():
        print(f"  {ticker}: {weight:.2%}")

    print(f"\nPerformance metrics:")
    print(f"  Expected return: {result['expected_return']:.2%}")
    print(f"  Volatility: {result['volatility']:.2%}")
    print(f"  Sharpe ratio: {result['sharpe_ratio']:.2f}")

    # Verify VaR warning
    print(f"\n" + "="*80)
    print("VaR Warning Verification")
    print("="*80)

    if "warnings" in result:
        print(f"\nWarning field found! (Total {len(result['warnings'])} warnings)")

        for i, warning in enumerate(result["warnings"], 1):
            print(f"\nWarning {i}:")
            print("-" * 80)
            print(warning)
            print("-" * 80)

            # Verify warning message content
            assert "VaR" in warning, "Warning message should contain 'VaR'"
            assert "INTC" in warning, "Warning message should contain ticker (INTC)"
            assert "80" in warning or "0.8" in warning, "Warning message should contain predicted return (80%)"
            assert "95th percentile" in warning, "Warning message should contain '95th percentile'"

        print(f"\nAll warning message verifications passed!")

    else:
        print(f"\nFailed: 'warnings' field not found in result!")
        print(f"\nResult keys: {list(result.keys())}")
        raise AssertionError("VaR warning was not included in return value.")

    print(f"\n" + "="*80)
    print("Test passed!")
    print("="*80)


def test_no_warning_for_low_return():
    """Test that no warning is issued for low return predictions"""

    print("\n" + "="*80)
    print("Low Return Prediction Test (should have no warning)")
    print("="*80)

    # 10% return prediction (below 40% threshold)
    tickers = ["AAPL", "MSFT", "GOOGL"]
    views = {"P": [{"AAPL": 1}], "Q": [0.10]}  # AAPL 10% return prediction

    print(f"\nInput Information:")
    print(f"  Tickers: {tickers}")
    print(f"  Views: {views}")

    # Run optimization
    print(f"\nRunning portfolio optimization...")
    result = tools.optimize_portfolio_bl(
        tickers=tickers,
        period="1Y",
        views=views,
        confidence=0.7
    )

    # Check for warnings
    if "warnings" in result:
        print(f"\nUnexpected warning occurred:")
        for warning in result["warnings"]:
            print(warning)
        raise AssertionError("Warning should not be issued for 10% return prediction.")
    else:
        print(f"\nNo warnings (as expected)")

    print(f"\n" + "="*80)
    print("Test passed!")
    print("="*80)


if __name__ == "__main__":
    test_var_warning_in_output()
    test_no_warning_for_low_return()
    print(f"\nAll tests passed!")
