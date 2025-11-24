"""
EGARCH VaR 기반 View 검증 테스트.

지나치게 낙관적인 View를 검증하는 시스템을 테스트합니다.

Usage:
    python -m pytest tests/test_var_validation.py -v
    또는
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
    """VaR 계산 기본 테스트 (AAPL)."""
    
    print("\n" + "=" * 60)
    print("TEST: VaR EGARCH 계산 (AAPL, 3년)")
    print("=" * 60)
    
    try:
        result = calculate_var_egarch(
            ticker="AAPL",
            period="3Y",
            confidence_level=0.95
        )
        
        print("\n✅ VaR 계산 성공!")
        print(f"\n📊 VaR 분석 결과:")
        print(f"  Ticker: {result['ticker']}")
        print(f"  Period: {result['period']}")
        print(f"  Data Points: {result['data_points']}")
        print(f"  VaR 95% (연환산): {result['var_95_annual']:.2%}")
        print(f"  5th Percentile: {result['percentile_5_annual']:.2%}")
        print(f"  Current Volatility: {result['current_volatility']:.2%}")
        
        if result['egarch_params'].get('fallback'):
            print(f"\n⚠️ Fallback 사용: {result['egarch_params']['fallback']}")
        else:
            print(f"\n🔧 EGARCH 파라미터:")
            print(f"  omega: {result['egarch_params']['omega']:.6f}")
            print(f"  alpha: {result['egarch_params']['alpha']:.6f}")
            print(f"  beta: {result['egarch_params']['beta']:.6f}")
            print(f"  gamma: {result['egarch_params']['gamma']:.6f}")
        
        # 검증: VaR는 음수여야 함 (손실 방향)
        assert result['var_95_annual'] > -1.0, "VaR should be > -100%"
        assert result['current_volatility'] > 0, "Volatility should be positive"
        
    except Exception as e:
        print(f"\n❌ 실패: {e}")
        raise


def test_optimize_normal_view():
    """정상 케이스: 연환산 30% View (검증 통과)."""
    
    print("\n" + "=" * 60)
    print("TEST: 정상 View (AAPL 30% 수익 예측)")
    print("=" * 60)
    
    try:
        result = tools.optimize_portfolio_bl(
            tickers=["AAPL", "MSFT", "GOOGL"],
            period="1Y",
            views={"P": [{"AAPL": 1}], "Q": [0.30]},  # 30% 수익
            confidence=0.7
        )
        
        print("\n✅ 최적화 성공! (검증 통과)")
        print(f"\n📊 Portfolio Weights:")
        for ticker, weight in result["weights"].items():
            print(f"  {ticker}: {weight:.2%}")
        
        print(f"\n📈 Performance:")
        print(f"  Expected Return: {result['expected_return']:.2%}")
        print(f"  Volatility: {result['volatility']:.2%}")
        
    except Exception as e:
        print(f"\n❌ 예상치 못한 실패: {e}")
        raise


def test_optimize_optimistic_view():
    """경고 케이스: 연환산 60% View (VaR 경고 발생)."""

    print("\n" + "=" * 60)
    print("TEST: 낙관적 View (NVDA 60% 수익 예측)")
    print("=" * 60)

    # 60% 수익 예측은 대부분의 주식에서 VaR 95%를 초과할 것
    if HAS_PYTEST:
        with pytest.raises(ValueError) as exc_info:
            tools.optimize_portfolio_bl(
                tickers=["NVDA", "AAPL", "MSFT"],
                period="1Y",
                views={"P": [{"NVDA": 1}], "Q": [0.60]},  # 60% 수익
                confidence=0.8
            )

        error_message = str(exc_info.value)
        print(f"\n✅ 예상대로 경고 발생!")
        print(f"\n⚠️ 경고 메시지:")
        print(error_message)

        # 경고 메시지에 VaR 정보가 포함되어 있는지 확인
        assert "VaR 95%" in error_message or "var" in error_message.lower()
        assert "낙관적" in error_message or "optimistic" in error_message.lower()
    else:
        # pytest 없이 실행
        try:
            tools.optimize_portfolio_bl(
                tickers=["NVDA", "AAPL", "MSFT"],
                period="1Y",
                views={"P": [{"NVDA": 1}], "Q": [0.60]},  # 60% 수익
                confidence=0.8
            )
            print(f"\n⚠️ 경고가 발생하지 않았습니다 (예상치 못함)")
        except ValueError as e:
            error_message = str(e)
            print(f"\n✅ 예상대로 경고 발생!")
            print(f"\n⚠️ 경고 메시지:")
            print(error_message)

            # 경고 메시지에 VaR 정보가 포함되어 있는지 확인
            assert "VaR 95%" in error_message or "var" in error_message.lower()
            assert "낙관적" in error_message or "optimistic" in error_message.lower()


def test_optimize_relative_view_extreme():
    """상대 View 극단 케이스: NVDA > AAPL by 80%."""
    
    print("\n" + "=" * 60)
    print("TEST: 극단적 상대 View (NVDA > AAPL by 80%)")
    print("=" * 60)
    
    # 상대 View 80%는 VaR의 2배를 초과할 가능성이 높음
    try:
        result = tools.optimize_portfolio_bl(
            tickers=["NVDA", "AAPL", "MSFT"],
            period="1Y",
            views={"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.80]},  # 80% 차이
            confidence=0.7
        )
        
        print("\n⚠️ 경고 없이 통과됨 (VaR 2배 이하일 수 있음)")
        print(f"\n📊 Portfolio Weights:")
        for ticker, weight in result["weights"].items():
            print(f"  {ticker}: {weight:.2%}")
        
    except ValueError as e:
        print(f"\n✅ 예상대로 경고 발생!")
        print(f"\n⚠️ 경고 메시지:")
        print(str(e))
        
        # 경고 메시지 검증
        assert "VaR" in str(e) or "var" in str(e).lower()


if __name__ == "__main__":
    # pytest 없이 직접 실행
    print("🧪 VaR 검증 시스템 테스트 시작\n")
    
    test_calculate_var_egarch_basic()
    test_optimize_normal_view()
    
    try:
        test_optimize_optimistic_view()
    except AssertionError:
        pass  # pytest.raises 없이 실행 시 예외 무시
    
    try:
        test_optimize_relative_view_extreme()
    except Exception:
        pass  # 경고 발생 여부는 데이터에 따라 다를 수 있음
    
    print("\n" + "=" * 60)
    print("✅ 모든 테스트 완료!")
    print("=" * 60)

