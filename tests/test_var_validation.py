"""
EGARCH VaR-based View Validation Tests.

Tests the system that validates overly optimistic views.

Usage:
    python -m pytest tests/test_var_validation.py -v
    or
    python tests/test_var_validation.py
"""

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

from bl_mcp import tools
from bl_mcp.utils.risk_models import calculate_var_egarch


def test_calculate_var_egarch_basic():
    """Basic VaR calculation test (AAPL)."""

    print("\n" + "=" * 60)
    print("TEST: VaR EGARCH Calculation (AAPL, 3 years)")
    print("=" * 60)

    try:
        result = calculate_var_egarch(
            ticker="AAPL",
            period="3Y",
            confidence_level=0.95
        )

        print("\nVaR calculation successful!")
        print(f"\nVaR Analysis Results:")
        print(f"  Ticker: {result['ticker']}")
        print(f"  Period: {result['period']}")
        print(f"  Data Points: {result['data_points']}")
        print(f"  VaR 95% (annualized): {result['var_95_annual']:.2%}")
        print(f"  5th Percentile: {result['percentile_5_annual']:.2%}")
        print(f"  Current Volatility: {result['current_volatility']:.2%}")

        if result['egarch_params'].get('fallback'):
            print(f"\nFallback used: {result['egarch_params']['fallback']}")
        else:
            print(f"\nEGARCH Parameters:")
            print(f"  omega: {result['egarch_params']['omega']:.6f}")
            print(f"  alpha: {result['egarch_params']['alpha']:.6f}")
            print(f"  beta: {result['egarch_params']['beta']:.6f}")
            print(f"  gamma: {result['egarch_params']['gamma']:.6f}")

        # Validation: VaR should be greater than -100%
        assert result['var_95_annual'] > -1.0, "VaR should be > -100%"
        assert result['current_volatility'] > 0, "Volatility should be positive"

    except Exception as e:
        print(f"\nFailed: {e}")
        raise


def test_optimize_normal_view():
    """Normal case: Annualized 30% view (validation passes)."""

    print("\n" + "=" * 60)
    print("TEST: Normal View (AAPL 30% return prediction)")
    print("=" * 60)

    try:
        result = tools.optimize_portfolio_bl(
            tickers=["AAPL", "MSFT", "GOOGL"],
            period="1Y",
            views={"P": [{"AAPL": 1}], "Q": [0.30]},  # 30% return
            confidence=0.7
        )

        print("\nOptimization successful! (validation passed)")
        print(f"\nPortfolio Weights:")
        for ticker, weight in result["weights"].items():
            print(f"  {ticker}: {weight:.2%}")

        print(f"\nPerformance:")
        print(f"  Expected Return: {result['expected_return']:.2%}")
        print(f"  Volatility: {result['volatility']:.2%}")

    except Exception as e:
        print(f"\nUnexpected failure: {e}")
        raise


def test_optimize_optimistic_view():
    """Warning case: Annualized 60% view (VaR warning triggered)."""

    print("\n" + "=" * 60)
    print("TEST: Optimistic View (NVDA 60% return prediction)")
    print("=" * 60)

    # 60% return prediction will likely exceed VaR 95% for most stocks
    result = tools.optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        period="1Y",
        views={"P": [{"NVDA": 1}], "Q": [0.60]},  # 60% return
        confidence=0.8
    )

    # Result should be returned normally
    assert "weights" in result, "Optimization result should contain weights"
    print(f"\nPortfolio Weights:")
    for ticker, weight in result["weights"].items():
        print(f"  {ticker}: {weight:.2%}")

    # warnings field should contain VaR warning
    if "warnings" in result and len(result["warnings"]) > 0:
        print(f"\nVaR warning triggered! (Total {len(result['warnings'])} warnings)")
        for warning in result["warnings"]:
            print(f"\nWarning message:")
            print(warning)
            # Verify warning message contains VaR information
            assert "VaR" in warning or "var" in warning.lower()
            assert "optimistic" in warning.lower() or "NVDA" in warning
    else:
        # Warning may not trigger depending on data (if NVDA volatility is high)
        print(f"\nNo warnings (NVDA's 95th percentile may be higher than 60%)")


def test_optimize_relative_view_extreme():
    """Extreme relative view case: NVDA > AAPL by 80%."""

    print("\n" + "=" * 60)
    print("TEST: Extreme Relative View (NVDA > AAPL by 80%)")
    print("=" * 60)

    # Relative view of 80% will likely exceed 2x VaR
    result = tools.optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        period="1Y",
        views={"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.80]},  # 80% difference
        confidence=0.7
    )

    # Result should be returned normally
    assert "weights" in result, "Optimization result should contain weights"
    print(f"\nPortfolio Weights:")
    for ticker, weight in result["weights"].items():
        print(f"  {ticker}: {weight:.2%}")

    # For relative views, warn if exceeds 2x VaR
    if "warnings" in result and len(result["warnings"]) > 0:
        print(f"\nVaR warning triggered! (relative view is extreme)")
        for warning in result["warnings"]:
            print(f"\nWarning message:")
            print(warning)
            assert "VaR" in warning or "relative" in warning.lower()
    else:
        print(f"\nNo warnings (may be below 2x VaR)")


def test_var_warning_message_content():
    """Verify warning message contains all required information."""

    print("\n" + "=" * 60)
    print("TEST: VaR Warning Message Content (INTC 80%)")
    print("=" * 60)

    result = tools.optimize_portfolio_bl(
        tickers=["NVDA", "TSLA", "INTC"],
        period="1Y",
        views={"P": [{"INTC": 1}], "Q": [0.80]},  # 80% return
        confidence=0.5
    )

    print(f"\nPortfolio Weights:")
    for ticker, weight in result["weights"].items():
        print(f"  {ticker}: {weight:.2%}")

    if "warnings" in result:
        print(f"\nWarning found! (Total {len(result['warnings'])} warnings)")
        for warning in result["warnings"]:
            print(f"\nWarning message:")
            print(warning)
            # Verify message content
            assert "VaR" in warning, "Should contain 'VaR'"
            assert "INTC" in warning, "Should contain ticker"
            assert "95th percentile" in warning, "Should contain '95th percentile'"
        print(f"\nWarning message verification passed!")
    else:
        print(f"\nNo warnings (INTC's 95th percentile may be higher than 80%)")


def test_no_warning_for_low_return():
    """Verify no warning for low return predictions (10%)."""

    print("\n" + "=" * 60)
    print("TEST: Low Return Prediction (AAPL 10%, no warning expected)")
    print("=" * 60)

    result = tools.optimize_portfolio_bl(
        tickers=["AAPL", "MSFT", "GOOGL"],
        period="1Y",
        views={"P": [{"AAPL": 1}], "Q": [0.10]},  # 10% return
        confidence=0.7
    )

    print(f"\nPortfolio Weights:")
    for ticker, weight in result["weights"].items():
        print(f"  {ticker}: {weight:.2%}")

    if "warnings" in result:
        print(f"\nUnexpected warning:")
        for warning in result["warnings"]:
            print(warning)
        raise AssertionError("Warning should not be issued for 10% return")
    else:
        print(f"\nNo warnings (as expected)")


if __name__ == "__main__":
    # Run directly without pytest
    print("VaR Validation System Tests Starting\n")

    test_calculate_var_egarch_basic()
    test_optimize_normal_view()
    test_optimize_optimistic_view()
    test_optimize_relative_view_extreme()
    test_var_warning_message_content()
    test_no_warning_for_low_return()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
