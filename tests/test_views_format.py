"""
Test views parameter format validation.

This verifies that views must be a dictionary and rejects invalid formats.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bl_mcp.utils.validators import validate_view_dict


def test_valid_views():
    """Test valid views formats."""
    
    print("="*70)
    print("Testing VALID views formats")
    print("="*70 + "\n")
    
    valid_cases = [
        ("Single view", {"AAPL": 0.10}, ["AAPL", "MSFT"]),
        ("Multiple views", {"AAPL": 0.10, "MSFT": 0.05}, ["AAPL", "MSFT", "GOOGL"]),
        ("Negative return", {"AAPL": -0.05}, ["AAPL", "MSFT"]),
        ("High return", {"AAPL": 0.50}, ["AAPL", "MSFT"]),
        ("Integer value", {"AAPL": 1}, ["AAPL", "MSFT"]),  # Will be treated as 100% return
    ]
    
    passed = 0
    failed = 0
    
    for name, view_dict, tickers in valid_cases:
        try:
            validate_view_dict(view_dict, tickers)
            print(f"✅ {name}: {view_dict}")
            passed += 1
        except Exception as e:
            print(f"❌ {name}: {e}")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed\n")
    return passed, failed


def test_invalid_views():
    """Test invalid views formats."""
    
    print("="*70)
    print("Testing INVALID views formats (should be rejected)")
    print("="*70 + "\n")
    
    invalid_cases = [
        ("Float number (not dict)", 0.10, ["AAPL", "MSFT"]),
        ("String (not dict)", "AAPL", ["AAPL", "MSFT"]),
        ("List (not dict)", ["AAPL", 0.10], ["AAPL", "MSFT"]),
        ("Empty dict", {}, ["AAPL", "MSFT"]),
        ("Invalid ticker", {"TSLA": 0.10}, ["AAPL", "MSFT"]),
        ("Non-numeric value", {"AAPL": "high"}, ["AAPL", "MSFT"]),
        ("Extreme return", {"AAPL": 15.0}, ["AAPL", "MSFT"]),  # 1500% is unreasonable
    ]
    
    passed = 0
    failed = 0
    
    for name, view_dict, tickers in invalid_cases:
        try:
            validate_view_dict(view_dict, tickers)
            print(f"❌ {name}: Should have been rejected but passed!")
            failed += 1
        except ValueError as e:
            print(f"✅ {name}: Correctly rejected")
            print(f"   Error: {str(e)[:100]}...")
            passed += 1
        except Exception as e:
            print(f"⚠️  {name}: Unexpected error: {e}")
            failed += 1
    
    print(f"\n{passed} correctly rejected, {failed} incorrectly accepted\n")
    return passed, failed


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("Views Parameter Format Validation Tests")
    print("="*70 + "\n")
    
    valid_passed, valid_failed = test_valid_views()
    invalid_passed, invalid_failed = test_invalid_views()
    
    print("="*70)
    print("Summary")
    print("="*70)
    print(f"Valid cases: {valid_passed} passed, {valid_failed} failed")
    print(f"Invalid cases: {invalid_passed} rejected, {invalid_failed} accepted")
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if (valid_failed == 0 and invalid_failed == 0) else '❌ SOME TESTS FAILED'}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
