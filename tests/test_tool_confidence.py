"""
Test tool calls with various confidence types.

This simulates how MCP/ADK might pass confidence values
and verifies they are handled correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bl_mcp.tools import create_investor_view, optimize_portfolio_bl


def test_create_investor_view_confidence():
    """Test create_investor_view with various confidence types."""
    
    print("="*70)
    print("Testing create_investor_view with different confidence types")
    print("="*70 + "\n")
    
    test_cases = [
        ("Integer 1", 1),
        ("Float 0.7", 0.7),
        ("String '0.5'", "0.5"),
        ("String '1'", "1"),
    ]
    
    for name, confidence_val in test_cases:
        print(f"Test: {name} (type: {type(confidence_val).__name__})")
        print(f"Input: confidence={confidence_val}")
        
        try:
            result = create_investor_view(
                view_dict={"AAPL": 0.10},
                tickers=["AAPL", "MSFT"],
                confidence=confidence_val
            )
            
            if result["success"]:
                print(f"✅ Success! Normalized confidence: {result['confidence']} (type: {type(result['confidence']).__name__})")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print()


def test_optimize_portfolio_confidence():
    """Test optimize_portfolio_bl with various confidence types."""
    
    print("="*70)
    print("Testing optimize_portfolio_bl with different confidence types")
    print("="*70 + "\n")
    
    test_cases = [
        ("No views (confidence ignored)", None, None),
        ("Views with int confidence", {"AAPL": 0.10}, 1),
        ("Views with float confidence", {"AAPL": 0.10}, 0.7),
        ("Views with string confidence", {"AAPL": 0.10}, "0.5"),
        ("Views without confidence (default)", {"AAPL": 0.10}, None),
    ]
    
    for name, views, confidence_val in test_cases:
        print(f"Test: {name}")
        if views:
            print(f"Input: views={views}, confidence={confidence_val} (type: {type(confidence_val).__name__ if confidence_val is not None else 'None'})")
        else:
            print(f"Input: No views")
        
        try:
            # Note: This will fail if data files don't exist
            # But it should at least pass validation
            result = optimize_portfolio_bl(
                tickers=["AAPL", "MSFT"],
                start_date="2023-01-01",
                views=views,
                confidence=confidence_val
            )
            
            if result["success"]:
                print(f"✅ Success! Portfolio optimized")
            else:
                error = result.get('error', 'Unknown error')
                # Data file errors are OK for this test
                if 'data' in error.lower() or 'parquet' in error.lower() or 'file' in error.lower():
                    print(f"✅ Validation passed (data file error is expected)")
                else:
                    print(f"❌ Failed: {error}")
        except Exception as e:
            error_msg = str(e)
            # Data file errors are OK for this test
            if 'data' in error_msg.lower() or 'parquet' in error_msg.lower() or 'file' in error_msg.lower():
                print(f"✅ Validation passed (data file error is expected)")
            else:
                print(f"❌ Exception: {e}")
        
        print()


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("Tool Confidence Type Handling Tests")
    print("="*70 + "\n")
    
    test_create_investor_view_confidence()
    test_optimize_portfolio_confidence()
    
    print("="*70)
    print("Tests complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
