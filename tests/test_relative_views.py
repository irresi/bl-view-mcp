"""
Comprehensive tests for relative view support in Black-Litterman model.

Tests the unified view interface with dict-based P matrix support.
"""

import pytest
from bl_mcp import tools


class TestAbsoluteViewsBackwardCompatibility:
    """Test that existing absolute view format still works (backward compatible)."""
    
    def test_absolute_views_single_confidence(self):
        """Test absolute views with single float confidence."""
        result = tools.optimize_portfolio_bl(
            tickers=["AAPL", "MSFT", "GOOGL"],
            period="1Y",
            views={"AAPL": 0.10},
            confidence=0.7
        )
        assert result["success"]
        assert "weights" in result
        assert result["has_views"]
    
    def test_absolute_views_dict_confidence(self):
        """Test absolute views with dict confidence (per-ticker)."""
        result = tools.optimize_portfolio_bl(
            tickers=["AAPL", "MSFT", "GOOGL"],
            period="1Y",
            views={"AAPL": 0.10, "MSFT": 0.05},
            confidence={"AAPL": 0.9, "MSFT": 0.6}
        )
        assert result["success"]
        assert "weights" in result
    
    def test_absolute_views_no_confidence(self):
        """Test absolute views with default confidence (0.5)."""
        result = tools.optimize_portfolio_bl(
            tickers=["AAPL", "MSFT", "GOOGL"],
            period="1Y",
            views={"AAPL": 0.10},
            confidence=None
        )
        assert result["success"]


class TestDictBasedPMatrix:
    """Test new dict-based P matrix format for relative views."""
    
    def test_relative_view_single(self):
        """Test single relative view: NVDA vs AAPL."""
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={
                "P": [{"NVDA": 1, "AAPL": -1}],
                "Q": [0.20]
            },
            confidence=[0.9]
        )
        assert result["success"]
        assert "weights" in result
    
    def test_relative_view_multiple(self):
        """Test multiple relative views."""
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
    
    def test_relative_view_complex_weights(self):
        """Test relative view with complex weights."""
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={
                "P": [{"NVDA": 0.5, "AAPL": -0.3, "MSFT": -0.2}],
                "Q": [0.10]
            },
            confidence=[0.7]
        )
        assert result["success"]
    
    def test_dict_p_with_float_confidence(self):
        """Test dict-based P with single float confidence (auto-convert to list)."""
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
    
    def test_dict_p_no_confidence(self):
        """Test dict-based P with default confidence."""
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={
                "P": [{"NVDA": 1, "AAPL": -1}],
                "Q": [0.20]
            },
            confidence=None
        )
        assert result["success"]


class TestNumPyPMatrix:
    """Test NumPy array P matrix format (advanced users)."""
    
    def test_numpy_p_single_view(self):
        """Test NumPy P matrix with single view."""
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={
                "P": [[1, -1, 0]],  # NVDA - AAPL
                "Q": [0.20]
            },
            confidence=[0.9]
        )
        assert result["success"]
    
    def test_numpy_p_multiple_views(self):
        """Test NumPy P matrix with multiple views."""
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={
                "P": [
                    [1, -1, 0],   # NVDA - AAPL
                    [1, 0, -1]    # NVDA - MSFT
                ],
                "Q": [0.20, 0.15]
            },
            confidence=[0.9, 0.8]
        )
        assert result["success"]
    
    def test_numpy_p_absolute_view(self):
        """Test NumPy P for absolute view (pick single asset)."""
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={
                "P": [[1, 0, 0]],  # Select NVDA only
                "Q": [0.30]
            },
            confidence=[0.85]
        )
        assert result["success"]


class TestConfidenceNormalization:
    """Test all confidence format conversions."""
    
    def test_confidence_none_to_list(self):
        """Test None confidence converts to [0.5, ...]."""
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={"AAPL": 0.10},
            confidence=None
        )
        assert result["success"]
    
    def test_confidence_float_to_list(self):
        """Test float confidence converts to [value, ...]."""
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={"AAPL": 0.10, "MSFT": 0.05},
            confidence=0.75
        )
        assert result["success"]
    
    def test_confidence_dict_to_list_absolute(self):
        """Test dict confidence converts to list for absolute views."""
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={"AAPL": 0.10, "MSFT": 0.05},
            confidence={"AAPL": 0.9, "MSFT": 0.6}
        )
        assert result["success"]
    
    def test_confidence_list_passthrough(self):
        """Test list confidence is validated and passed through."""
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={
                "P": [{"NVDA": 1, "AAPL": -1}],
                "Q": [0.20]
            },
            confidence=[0.85]
        )
        assert result["success"]
    
    def test_confidence_percentage_input(self):
        """Test percentage input (70 → 0.7)."""
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={"AAPL": 0.10},
            confidence=85  # Percentage
        )
        assert result["success"]


class TestValidationErrors:
    """Test validation catches all error cases."""
    
    def test_error_unknown_ticker_absolute(self):
        """Test error when ticker not in tickers list (absolute views)."""
        with pytest.raises(ValueError, match="not found in tickers list"):
            tools.optimize_portfolio_bl(
                tickers=["AAPL", "MSFT"],
                period="1Y",
                views={"UNKNOWN": 0.10},
                confidence=0.7
            )
    
    def test_error_unknown_ticker_dict_p(self):
        """Test error when ticker not in tickers list (dict-based P)."""
        with pytest.raises(ValueError, match="not found in tickers list"):
            tools.optimize_portfolio_bl(
                tickers=["AAPL", "MSFT"],
                period="1Y",
                views={
                    "P": [{"UNKNOWN": 1, "AAPL": -1}],
                    "Q": [0.20]
                },
                confidence=[0.8]
            )
    
    def test_error_confidence_length_mismatch(self):
        """Test error when confidence length doesn't match Q length."""
        with pytest.raises(ValueError, match="must match number of views"):
            tools.optimize_portfolio_bl(
                tickers=["NVDA", "AAPL", "MSFT"],
                period="1Y",
                views={
                    "P": [{"NVDA": 1, "AAPL": -1}],
                    "Q": [0.20]
                },
                confidence=[0.9, 0.8]  # 2 confidences for 1 view
            )
    
    def test_error_missing_q(self):
        """Test error when Q is missing with P."""
        with pytest.raises(ValueError, match="Q is required"):
            tools.optimize_portfolio_bl(
                tickers=["NVDA", "AAPL", "MSFT"],
                period="1Y",
                views={
                    "P": [{"NVDA": 1, "AAPL": -1}]
                },
                confidence=[0.8]
            )
    
    def test_error_p_q_dimension_mismatch(self):
        """Test error when P rows don't match Q length."""
        with pytest.raises(ValueError, match="Number of views must match"):
            tools.optimize_portfolio_bl(
                tickers=["NVDA", "AAPL", "MSFT"],
                period="1Y",
                views={
                    "P": [
                        {"NVDA": 1, "AAPL": -1},
                        {"NVDA": 1, "MSFT": -1}
                    ],
                    "Q": [0.20]  # Only 1 Q for 2 P rows
                },
                confidence=[0.9, 0.8]
            )
    
    def test_error_numpy_p_column_mismatch(self):
        """Test error when NumPy P columns don't match ticker count."""
        with pytest.raises(ValueError, match="Dimensions must match"):
            tools.optimize_portfolio_bl(
                tickers=["NVDA", "AAPL", "MSFT"],
                period="1Y",
                views={
                    "P": [[1, -1]],  # Only 2 columns but 3 tickers
                    "Q": [0.20]
                },
                confidence=[0.9]
            )
    
    def test_error_dict_confidence_with_p_q(self):
        """Test error when using dict confidence with P, Q views."""
        with pytest.raises(ValueError, match="not supported for P, Q views"):
            tools.optimize_portfolio_bl(
                tickers=["NVDA", "AAPL", "MSFT"],
                period="1Y",
                views={
                    "P": [{"NVDA": 1, "AAPL": -1}],
                    "Q": [0.20]
                },
                confidence={"NVDA": 0.9}  # Dict not allowed with P, Q
            )
    
    def test_error_missing_confidence_for_view(self):
        """Test error when dict confidence missing a ticker."""
        with pytest.raises(ValueError, match="Missing confidence"):
            tools.optimize_portfolio_bl(
                tickers=["NVDA", "AAPL", "MSFT"],
                period="1Y",
                views={"AAPL": 0.10, "MSFT": 0.05},
                confidence={"AAPL": 0.9}  # Missing MSFT
            )


class TestEquivalence:
    """Test that equivalent views produce similar results."""
    
    def test_absolute_vs_dict_p_equivalence(self):
        """Test absolute view dict equivalent to dict-based P."""
        # Absolute view
        result1 = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={"AAPL": 0.10},
            confidence=0.8
        )
        
        # Equivalent dict-based P
        result2 = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={
                "P": [{"AAPL": 1}],
                "Q": [0.10]
            },
            confidence=[0.8]
        )
        
        assert result1["success"] and result2["success"]
        # Weights should be very similar (allowing for numerical differences)
        for ticker in ["NVDA", "AAPL", "MSFT"]:
            assert abs(result1["weights"][ticker] - result2["weights"][ticker]) < 0.01
    
    def test_dict_p_vs_numpy_p_equivalence(self):
        """Test dict-based P equivalent to NumPy P."""
        # Dict-based P
        result1 = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={
                "P": [{"NVDA": 1, "AAPL": -1}],
                "Q": [0.20]
            },
            confidence=[0.9]
        )
        
        # NumPy P (NVDA=0, AAPL=1, MSFT=2)
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
        # Weights should be identical
        for ticker in ["NVDA", "AAPL", "MSFT"]:
            assert abs(result1["weights"][ticker] - result2["weights"][ticker]) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
