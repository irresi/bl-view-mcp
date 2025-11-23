"""Tests for backtest_portfolio functionality."""

import pytest
from bl_mcp import tools


class TestBacktestBasic:
    """Basic backtest functionality tests."""

    def test_backtest_buy_and_hold(self):
        """Test basic buy and hold strategy."""
        result = tools.backtest_portfolio(
            tickers=["AAPL", "MSFT", "GOOGL"],
            weights={"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25},
            period="1Y",
            strategy="buy_and_hold",
            benchmark="SPY"
        )

        # Check required output fields
        assert "total_return" in result
        assert "cagr" in result
        assert "volatility" in result
        assert "sharpe_ratio" in result
        assert "sortino_ratio" in result
        assert "max_drawdown" in result
        assert "calmar_ratio" in result

        # Check value metrics
        assert "initial_capital" in result
        assert "final_value" in result
        assert result["initial_capital"] == 10000.0

        # Check cost metrics
        assert "total_fees_paid" in result
        assert "num_rebalances" in result
        assert result["num_rebalances"] == 1  # Only initial allocation

        # Check period info
        assert "period" in result
        assert "trading_days" in result["period"]

    def test_backtest_passive_rebalance(self):
        """Test passive rebalancing strategy (default)."""
        result = tools.backtest_portfolio(
            tickers=["AAPL", "MSFT"],
            weights={"AAPL": 0.6, "MSFT": 0.4},
            period="1Y",
            strategy="passive_rebalance"
        )

        # Monthly rebalancing should have ~12 rebalances
        assert result["num_rebalances"] >= 1
        assert result["num_rebalances"] <= 15  # Allow some variance

        # Check strategy is recorded
        assert result["strategy"] == "passive_rebalance"

    def test_backtest_risk_managed(self):
        """Test risk-managed strategy with stop-loss."""
        result = tools.backtest_portfolio(
            tickers=["AAPL", "MSFT", "GOOGL"],
            weights={"AAPL": 0.5, "MSFT": 0.3, "GOOGL": 0.2},
            period="2Y",
            strategy="risk_managed"
        )

        # Check risk management info
        assert "is_liquidated" in result
        assert "liquidation_reason" in result
        assert result["strategy"] == "risk_managed"

        # Check config has stop_loss
        assert result["config"]["stop_loss"] == 0.10
        assert result["config"]["max_drawdown_limit"] == 0.20


class TestBacktestBenchmark:
    """Benchmark comparison tests."""

    def test_benchmark_metrics(self):
        """Test benchmark comparison metrics."""
        result = tools.backtest_portfolio(
            tickers=["AAPL", "MSFT"],
            weights={"AAPL": 0.5, "MSFT": 0.5},
            period="1Y",
            benchmark="SPY"
        )

        # Check benchmark metrics
        assert "benchmark_return" in result
        assert "excess_return" in result
        assert "alpha" in result
        assert "beta" in result
        assert "information_ratio" in result

    def test_no_benchmark(self):
        """Test backtest without benchmark."""
        result = tools.backtest_portfolio(
            tickers=["AAPL", "MSFT"],
            weights={"AAPL": 0.5, "MSFT": 0.5},
            period="1Y",
            benchmark=None
        )

        # Should not have benchmark metrics
        assert "benchmark_return" not in result


class TestBacktestCustomConfig:
    """Custom configuration tests."""

    def test_custom_rebalance_frequency(self):
        """Test custom rebalancing frequency."""
        result = tools.backtest_portfolio(
            tickers=["AAPL", "MSFT"],
            weights={"AAPL": 0.5, "MSFT": 0.5},
            period="1Y",
            custom_config={
                "rebalance_frequency": "quarterly",
                "fees": 0.002,
                "slippage": 0.001
            }
        )

        # Check config is applied
        assert result["config"]["rebalance_frequency"] == "quarterly"
        assert result["config"]["fees"] == 0.002
        assert result["config"]["slippage"] == 0.001

        # Quarterly rebalancing should have fewer rebalances
        assert result["num_rebalances"] <= 5

    def test_custom_stop_loss(self):
        """Test custom stop-loss configuration."""
        result = tools.backtest_portfolio(
            tickers=["AAPL", "MSFT"],
            weights={"AAPL": 0.6, "MSFT": 0.4},
            period="1Y",
            custom_config={
                "stop_loss": 0.05,  # 5% stop loss
                "max_drawdown_limit": 0.15
            }
        )

        assert result["config"]["stop_loss"] == 0.05
        assert result["config"]["max_drawdown_limit"] == 0.15


class TestBacktestValidation:
    """Input validation tests."""

    def test_empty_weights_error(self):
        """Test error on empty weights."""
        with pytest.raises(ValueError, match="weights cannot be empty"):
            tools.backtest_portfolio(
                tickers=["AAPL", "MSFT"],
                weights={},
                period="1Y"
            )

    def test_missing_ticker_in_weights(self):
        """Test error when weight ticker not in tickers list."""
        with pytest.raises(ValueError, match="not in tickers list"):
            tools.backtest_portfolio(
                tickers=["AAPL", "MSFT"],
                weights={"AAPL": 0.5, "GOOGL": 0.5},  # GOOGL not in tickers
                period="1Y"
            )

    def test_negative_weight_error(self):
        """Test error on negative weights."""
        with pytest.raises(ValueError, match="cannot be negative"):
            tools.backtest_portfolio(
                tickers=["AAPL", "MSFT"],
                weights={"AAPL": 0.5, "MSFT": -0.1},
                period="1Y"
            )

    def test_invalid_strategy_error(self):
        """Test error on invalid strategy."""
        with pytest.raises(ValueError, match="Unknown strategy"):
            tools.backtest_portfolio(
                tickers=["AAPL", "MSFT"],
                weights={"AAPL": 0.5, "MSFT": 0.5},
                period="1Y",
                strategy="invalid_strategy"
            )


class TestBacktestHoldingPeriods:
    """Holding period tracking tests."""

    def test_holding_periods_output(self):
        """Test holding periods are tracked."""
        result = tools.backtest_portfolio(
            tickers=["AAPL", "MSFT"],
            weights={"AAPL": 0.5, "MSFT": 0.5},
            period="2Y",
            strategy="buy_and_hold"
        )

        assert "holding_periods" in result
        holding_periods = result["holding_periods"]

        # Should have entry for each ticker
        for ticker in ["AAPL", "MSFT"]:
            if ticker in holding_periods:
                hp = holding_periods[ticker]
                assert "start_date" in hp
                assert "end_date" in hp
                assert "days" in hp
                assert "is_long_term" in hp


class TestBacktestIntegration:
    """Integration tests with optimize_portfolio_bl."""

    def test_optimize_then_backtest(self):
        """Test typical workflow: optimize -> backtest."""
        # Step 1: Optimize portfolio
        bl_result = tools.optimize_portfolio_bl(
            tickers=["AAPL", "MSFT", "GOOGL"],
            period="1Y"
        )

        assert "weights" in bl_result

        # Step 2: Backtest the optimized weights
        backtest_result = tools.backtest_portfolio(
            tickers=["AAPL", "MSFT", "GOOGL"],
            weights=bl_result["weights"],
            period="2Y",
            strategy="passive_rebalance"
        )

        # Verify backtest completed successfully
        assert "total_return" in backtest_result
        assert "sharpe_ratio" in backtest_result
        assert backtest_result["final_value"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
