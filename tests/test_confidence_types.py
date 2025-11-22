"""
Test confidence parameter type handling.

This verifies that confidence accepts various input types (int, float, string)
and normalizes them correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bl_mcp.utils.validators import validate_confidence


def test_confidence_types():
    """Test various confidence input types."""
    
    print("Testing confidence type handling...\n")
    
    test_cases = [
        # Decimal format (0.0 - 1.0)
        ("Integer 1", 1, 1.0),
        ("Integer 0", 0, 0.0),
        ("Float 0.5", 0.5, 0.5),
        ("Float 0.7", 0.7, 0.7),
        ("Float 1.0", 1.0, 1.0),
        
        # String decimal
        ("String '1'", "1", 1.0),
        ("String '0'", "0", 0.0),
        ("String '0.5'", "0.5", 0.5),
        ("String '0.7'", "0.7", 0.7),
        
        # Percentage (0 - 100)
        ("Percentage 100", 100, 1.0),
        ("Percentage 70", 70, 0.7),
        ("Percentage 50", 50, 0.5),
        ("Percentage 80", 80, 0.8),
        ("Percentage 90", 90, 0.9),
        
        # Percentage strings
        ("String '100%'", "100%", 1.0),
        ("String '70%'", "70%", 0.7),
        ("String '50%'", "50%", 0.5),
        ("String '80 %'", "80 %", 0.8),
        
        # Natural language equivalent percentages (improved scale)
        ("Very confident (95%)", 95, 0.95),
        ("Confident (85%)", 85, 0.85),
        ("Quite confident (75%)", 75, 0.75),
        ("Somewhat confident (60%)", 60, 0.6),
        ("Neutral (50%)", 50, 0.5),
        ("Uncertain (30%)", 30, 0.3),
        ("Very uncertain (10%)", 10, 0.1),
    ]
    
    passed = 0
    failed = 0
    
    for name, input_val, expected in test_cases:
        try:
            result = validate_confidence(input_val)
            if result == expected:
                print(f"✅ {name}: {input_val} ({type(input_val).__name__}) → {result}")
                passed += 1
            else:
                print(f"❌ {name}: Expected {expected}, got {result}")
                failed += 1
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}\n")
    
    # Test invalid cases
    print("Testing invalid inputs...\n")
    
    invalid_cases = [
        ("Out of range: 1.5", 1.5),
        ("Out of range: -0.5", -0.5),
        ("Out of range: 2", 2),
        ("Out of range: 150%", 150),
        ("Out of range: 101%", "101%"),
        ("Out of range: -10%", -10),
        ("Non-numeric string", "abc"),
        ("None type", None),
    ]
    
    for name, input_val in invalid_cases:
        try:
            result = validate_confidence(input_val)
            print(f"❌ {name}: Should have failed but got {result}")
        except ValueError as e:
            print(f"✅ {name}: Correctly rejected - {e}")
        except Exception as e:
            print(f"⚠️  {name}: Unexpected error - {e}")
    
    print(f"\n{'='*50}")
    print("Test complete!")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    test_confidence_types()
