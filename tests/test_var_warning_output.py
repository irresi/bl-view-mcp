"""
VaR 경고 메시지가 반환값에 포함되는지 테스트

이 테스트는 80% 수익률 예측을 입력했을 때:
1. VaR 경고가 트리거되는지
2. 경고 메시지가 반환값의 "warnings" 필드에 포함되는지
3. 경고 메시지에 필요한 정보가 모두 포함되어 있는지
를 확인합니다.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bl_mcp import tools


def test_var_warning_in_output():
    """80% 수익률 예측 시 VaR 경고가 반환값에 포함되는지 테스트"""
    
    print("\n" + "="*80)
    print("VaR 경고 출력 테스트")
    print("="*80)
    
    # 80% 수익률 예측 (명백히 40% 임계값 초과)
    tickers = ["NVDA", "TSLA", "INTC"]
    views = {"P": [{"INTC": 1}], "Q": [0.80]}  # INTC 80% 수익 예측
    confidence = 0.5
    
    print(f"\n📊 입력 정보:")
    print(f"  Tickers: {tickers}")
    print(f"  Views: {views}")
    print(f"  Confidence: {confidence}")
    
    # 최적화 실행
    print(f"\n🔄 포트폴리오 최적화 실행 중...")
    result = tools.optimize_portfolio_bl(
        tickers=tickers,
        period="1Y",
        views=views,
        confidence=confidence
    )
    
    # 결과 확인
    print(f"\n✅ 최적화 완료!")
    print(f"\n📈 포트폴리오 구성:")
    for ticker, weight in result["weights"].items():
        print(f"  {ticker}: {weight:.2%}")
    
    print(f"\n📊 성과 지표:")
    print(f"  기대 수익률: {result['expected_return']:.2%}")
    print(f"  변동성: {result['volatility']:.2%}")
    print(f"  샤프 비율: {result['sharpe_ratio']:.2f}")
    
    # VaR 경고 확인
    print(f"\n" + "="*80)
    print("VaR 경고 검증")
    print("="*80)
    
    if "warnings" in result:
        print(f"\n✅ 경고 필드 발견! (총 {len(result['warnings'])}개)")
        
        for i, warning in enumerate(result["warnings"], 1):
            print(f"\n⚠️ 경고 {i}:")
            print("-" * 80)
            print(warning)
            print("-" * 80)
            
            # 경고 메시지 내용 검증
            assert "VaR 경고" in warning, "경고 메시지에 'VaR 경고'가 포함되어야 함"
            assert "INTC" in warning, "경고 메시지에 티커(INTC)가 포함되어야 함"
            assert "80" in warning or "0.8" in warning, "경고 메시지에 예측 수익률(80%)이 포함되어야 함"
            assert "95th percentile" in warning, "경고 메시지에 '95th percentile'이 포함되어야 함"
            
        print(f"\n✅ 모든 경고 메시지 검증 통과!")
        
    else:
        print(f"\n❌ 실패: 'warnings' 필드가 결과에 없습니다!")
        print(f"\n결과 키: {list(result.keys())}")
        raise AssertionError("VaR 경고가 반환값에 포함되지 않았습니다.")
    
    print(f"\n" + "="*80)
    print("테스트 성공! ✅")
    print("="*80)


def test_no_warning_for_low_return():
    """낮은 수익률 예측 시 경고가 없는지 테스트"""
    
    print("\n" + "="*80)
    print("낮은 수익률 예측 테스트 (경고 없어야 함)")
    print("="*80)
    
    # 10% 수익률 예측 (40% 임계값 미만)
    tickers = ["AAPL", "MSFT", "GOOGL"]
    views = {"P": [{"AAPL": 1}], "Q": [0.10]}  # AAPL 10% 수익 예측
    
    print(f"\n📊 입력 정보:")
    print(f"  Tickers: {tickers}")
    print(f"  Views: {views}")
    
    # 최적화 실행
    print(f"\n🔄 포트폴리오 최적화 실행 중...")
    result = tools.optimize_portfolio_bl(
        tickers=tickers,
        period="1Y",
        views=views,
        confidence=0.7
    )
    
    # 경고 확인
    if "warnings" in result:
        print(f"\n⚠️ 예상치 못한 경고 발생:")
        for warning in result["warnings"]:
            print(warning)
        raise AssertionError("10% 수익률 예측에서 경고가 발생하면 안 됩니다.")
    else:
        print(f"\n✅ 경고 없음 (정상)")
    
    print(f"\n" + "="*80)
    print("테스트 성공! ✅")
    print("="*80)


if __name__ == "__main__":
    test_var_warning_in_output()
    test_no_warning_for_low_return()
    print(f"\n🎉 모든 테스트 통과!")

