"""
Simple test runner for relative views (no pytest required).
Run with: python tests/test_relative_views_simple.py
"""

from bl_mcp import tools


def test_absolute_views_p_q_format():
    """Test absolute views using P, Q format."""
    print("\n✅ Testing absolute views (P, Q format)...")
    
    result = tools.optimize_portfolio_bl(
        tickers=["AAPL", "MSFT", "GOOGL"],
        period="1Y",
        views={"P": [{"AAPL": 1}], "Q": [0.10]},
        confidence=0.7
    )
    assert result["success"], f"Failed: {result.get('error')}"
    assert "weights" in result
    print("  ✓ Single absolute view works")
    
    result = tools.optimize_portfolio_bl(
        tickers=["AAPL", "MSFT", "GOOGL"],
        period="1Y",
        views={"P": [{"AAPL": 1}, {"MSFT": 1}], "Q": [0.10, 0.05]},
        confidence=[0.9, 0.6]
    )
    assert result["success"]
    print("  ✓ Multiple absolute views work")


def test_dict_based_p_matrix():
    """Test new dict-based P matrix for relative views."""
    print("\n✅ Testing dict-based P matrix (relative views)...")
    
    # Single relative view
    result = tools.optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        period="1Y",
        views={
            "P": [{"NVDA": 1, "AAPL": -1}],
            "Q": [0.20]
        },
        confidence=[0.9]
    )
    assert result["success"], f"Failed: {result.get('error')}"
    print("  ✓ Single relative view works")
    
    # Multiple relative views
    result = tools.optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        period="1Y",
        views={
            "P": [
                {"NVDA": 1, "AAPL": -1},
                {"NVDA": 1, "MSFT": -1}
            ],
            "Q": [0.20, 0.15]
        },
        confidence=[0.9, 0.8]
    )
    assert result["success"]
    print("  ✓ Multiple relative views work")
    
    # Float confidence auto-converts
    result = tools.optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        period="1Y",
        views={
            "P": [{"NVDA": 1, "AAPL": -1}],
            "Q": [0.20]
        },
        confidence=0.8  # Single float
    )
    assert result["success"]
    print("  ✓ Float confidence auto-converts to list")


def test_numpy_p_matrix():
    """Test NumPy P matrix format."""
    print("\n✅ Testing NumPy P matrix...")
    
    result = tools.optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        period="1Y",
        views={
            "P": [[1, -1, 0]],  # NVDA - AAPL
            "Q": [0.20]
        },
        confidence=[0.9]
    )
    assert result["success"], f"Failed: {result.get('error')}"
    print("  ✓ NumPy P matrix works")


def test_validation_errors():
    """Test that validation catches errors."""
    print("\n✅ Testing validation errors...")
    
    # Old format rejected
    result = tools.optimize_portfolio_bl(
        tickers=["AAPL", "MSFT"],
        period="1Y",
        views={"AAPL": 0.10},
        confidence=0.7
    )
    assert not result["success"], "Should have failed"
    assert "must use P, Q format" in result["error"]
    print("  ✓ Old dict format rejected")
    
    # Unknown ticker in P matrix
    result = tools.optimize_portfolio_bl(
        tickers=["AAPL", "MSFT"],
        period="1Y",
        views={"P": [{"UNKNOWN": 1}], "Q": [0.10]},
        confidence=0.7
    )
    assert not result["success"], "Should have failed"
    assert "not found in tickers list" in result["error"]
    print("  ✓ Unknown ticker detected")
    
    # Confidence length mismatch
    result = tools.optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        period="1Y",
        views={
            "P": [{"NVDA": 1, "AAPL": -1}],
            "Q": [0.20]
        },
        confidence=[0.9, 0.8]  # 2 for 1 view
    )
    assert not result["success"]
    assert "must match number of views" in result["error"]
    print("  ✓ Confidence length mismatch detected")
    
    # Missing Q
    result = tools.optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        period="1Y",
        views={
            "P": [{"NVDA": 1, "AAPL": -1}]
        },
        confidence=[0.8]
    )
    assert not result["success"], f"Should have failed but got: {result}"
    assert "Q is required" in result["error"] or "'Q'" in result["error"], f"Unexpected error: {result['error']}"
    print("  ✓ Missing Q detected")
    
    # Dict confidence rejected
    result = tools.optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        period="1Y",
        views={
            "P": [{"NVDA": 1, "AAPL": -1}],
            "Q": [0.20]
        },
        confidence={"NVDA": 0.9}
    )
    assert not result["success"]
    assert "Invalid confidence type" in result["error"]
    print("  ✓ Dict confidence rejected")


def test_equivalence():
    """Test that equivalent views produce similar results."""
    print("\n✅ Testing equivalence...")
    
    # Dict-based P vs NumPy P
    result1 = tools.optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        period="1Y",
        views={
            "P": [{"NVDA": 1, "AAPL": -1}],
            "Q": [0.20]
        },
        confidence=[0.9]
    )
    
    result2 = tools.optimize_portfolio_bl(
        tickers=["NVDA", "AAPL", "MSFT"],
        period="1Y",
        views={
            "P": [[1, -1, 0]],
            "Q": [0.20]
        },
        confidence=[0.9]
    )
    
    assert result1["success"] and result2["success"]
    for ticker in ["NVDA", "AAPL", "MSFT"]:
        diff = abs(result1["weights"][ticker] - result2["weights"][ticker])
        assert diff < 0.001, f"Weights differ too much for {ticker}: {diff}"
    print("  ✓ Dict-based P == NumPy P")


if __name__ == "__main__":
    print("="*60)
    print("🧪 RELATIVE VIEW SUPPORT TESTS")
    print("="*60)
    
    try:
        test_absolute_views_p_q_format()
        test_dict_based_p_matrix()
        test_numpy_p_matrix()
        test_validation_errors()
        test_equivalence()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
