"""EGARCH 기반 VaR 계산 및 리스크 모델링 유틸리티."""

import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from arch import arch_model

from . import data_loader
from .validators import parse_period


def calculate_var_egarch(
    ticker: str,
    period: str = "3Y",
    confidence_level: float = 0.95
) -> dict:
    """
    EGARCH(1,1) 모델을 사용하여 VaR 95% 계산.
    
    지나치게 낙관적인 View를 검증하기 위해 역사적 데이터 기반으로
    현실적인 수익률 범위를 제시합니다.
    
    Args:
        ticker: 분석 대상 티커 (예: "NVDA")
        period: 데이터 기간 (기본값: "3Y" - 3개년 일별 데이터)
        confidence_level: VaR 신뢰수준 (기본값: 0.95 = 95%)
        
    Returns:
        Dictionary containing:
        - var_95_annual: 연환산 VaR 95% 값 (예: 0.35 = 35% 수익)
        - percentile_5_annual: 연환산 5th percentile 수익률
        - current_volatility: 현재 연환산 변동성
        - egarch_params: EGARCH(1,1) 모델 파라미터
        - warning_message: 사용자에게 표시할 경고 메시지
        - data_points: 사용된 데이터 포인트 수
        
    Raises:
        ValueError: 데이터 부족 또는 계산 불가능한 경우
    """
    # 1. 가격 데이터 로드
    import logging

    try:
        # period를 start_date로 변환
        period_delta = parse_period(period)
        end_date = datetime.now()
        start_date = end_date - period_delta

        logging.warning(f"🔍 VaR 데이터 로딩: ticker={ticker}, period={period}")
        logging.warning(f"  📅 요청 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

        # 먼저 대형 데이터셋 파일에서 찾기 (sp500_prices.parquet 등)
        price_series = None
        data_dir = data_loader.DEFAULT_DATA_DIR

        # 시도 1: sp500_prices.parquet에서 로드
        sp500_path = Path(data_dir) / "sp500_prices.parquet"
        logging.warning(f"  📂 sp500_prices.parquet 존재 여부: {sp500_path.exists()}")

        if sp500_path.exists():
            try:
                df = pd.read_parquet(sp500_path)
                logging.warning(f"  📊 Parquet 파일 로드 성공: {len(df)} rows, {len(df.columns)} tickers")

                if ticker in df.columns:
                    price_series = df[ticker].loc[start_date.strftime("%Y-%m-%d"):end_date.strftime("%Y-%m-%d")].dropna()
                    logging.warning(f"  ✅ {ticker} 데이터 발견: {len(price_series)} days")
                    if len(price_series) > 0:
                        logging.warning(f"  📅 실제 데이터 기간: {price_series.index[0]} ~ {price_series.index[-1]}")
                else:
                    logging.warning(f"  ⚠️ {ticker} not found in sp500_prices.parquet")
            except Exception as e:
                logging.warning(f"  ❌ Parquet 로드 실패: {type(e).__name__}: {e}")

        # 시도 2: 개별 티커 파일 또는 yfinance (기존 방식)
        if price_series is None or len(price_series) < 252:
            logging.warning(f"  🔄 Fallback: load_prices() 호출 (개별 파일 또는 yfinance)")
            prices = data_loader.load_prices(
                [ticker],
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )

            if ticker not in prices.columns:
                raise ValueError(
                    f"Ticker {ticker} not found in price data.\n"
                    f"VaR 계산을 위한 데이터가 부족합니다. 'make download-data'를 실행하여 데이터를 다운로드하세요."
                )

            price_series = prices[ticker].dropna()
            logging.warning(f"  ✅ load_prices() 성공: {len(price_series)} days")

    except Exception as e:
        logging.error(f"  ❌ 데이터 로드 실패: {type(e).__name__}: {e}")
        raise ValueError(
            f"Failed to load price data for {ticker}: {e}\n"
            f"VaR 계산을 위한 데이터가 부족합니다. 'make download-data'를 실행하여 데이터를 다운로드하세요."
        )

    # 최소 데이터 요구사항 확인 (최소 1년 = 252 거래일)
    if len(price_series) < 252:
        raise ValueError(
            f"Insufficient data for {ticker}: {len(price_series)} days. "
            f"At least 252 days (1 year) required for reliable VaR estimation.\n"
            f"VaR 계산을 위한 데이터가 부족합니다. 'make download-data'를 실행하여 데이터를 다운로드하세요."
        )
    
    # 2. 일별 수익률 계산
    returns = price_series.pct_change().dropna()
    
    if len(returns) < 100:
        raise ValueError(
            f"Insufficient return data for {ticker}: {len(returns)} days. "
            f"At least 100 days required."
        )
    
    # 3. EGARCH(1,1) 모델 적합
    try:
        # returns를 백분율로 변환 (arch 패키지는 백분율 단위 선호)
        returns_pct = returns * 100
        
        # EGARCH(1,1) 모델 생성
        # mean='Zero': 평균 0 가정 (수익률 예측이 아닌 변동성 모델링)
        # vol='EGARCH': Exponential GARCH (비대칭 변동성 포착)
        # p=1, q=1: EGARCH(1,1)
        model = arch_model(
            returns_pct,
            mean='Zero',
            vol='EGARCH',
            p=1,
            q=1,
            rescale=False
        )
        
        # 모델 적합 (경고 억제)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = model.fit(disp='off', show_warning=False)
        
        # EGARCH 파라미터 추출
        egarch_params = {
            "omega": float(result.params.get('omega', 0)),
            "alpha": float(result.params.get('alpha[1]', 0)),
            "beta": float(result.params.get('beta[1]', 0)),
            "gamma": float(result.params.get('gamma[1]', 0))
        }
        
        # 조건부 변동성 (conditional volatility)
        conditional_vol = result.conditional_volatility
        current_vol_daily = conditional_vol.iloc[-1] / 100  # 백분율에서 소수로 변환

        # VaR 계산: 정규분포 가정하에 5th percentile (하방 리스크)
        # VaR_95% = σ × z_0.05 (z_0.05 ≈ -1.645 for 95% confidence)
        z_score_5 = -1.645  # 5th percentile
        var_daily = current_vol_daily * z_score_5

        # 연환산 변환 (올바른 공식: sqrt(252) 곱하기)
        var_annual = var_daily * np.sqrt(252)
        current_vol_annual = current_vol_daily * np.sqrt(252)

        # Percentile 계산 (역사적 데이터 기반)
        percentile_5_daily = np.percentile(returns, 5)
        percentile_95_daily = np.percentile(returns, 95)

        # 연환산 변환 (단순 스케일링: percentile * sqrt(252))
        # 복리 계산 (1 + r)^252 - 1은 극단값에서 과도하게 증폭되므로 사용하지 않음
        percentile_5_annual = percentile_5_daily * np.sqrt(252)
        percentile_95_annual = percentile_95_daily * np.sqrt(252)

        use_fallback = False
        
    except Exception as e:
        # EGARCH 적합 실패 시 Fallback: 역사적 변동성 사용
        import logging
        logging.warning(
            f"  ⚠️ EGARCH 모델 적합 실패: {type(e).__name__}: {e}"
        )
        logging.warning(f"  🔄 Fallback: 역사적 변동성 사용")

        current_vol_daily = returns.std()
        current_vol_annual = current_vol_daily * np.sqrt(252)

        z_score_5 = -1.645
        var_daily = current_vol_daily * z_score_5
        var_annual = var_daily * np.sqrt(252)

        percentile_5_daily = np.percentile(returns, 5)
        percentile_95_daily = np.percentile(returns, 95)

        percentile_5_annual = (1 + percentile_5_daily) ** 252 - 1
        percentile_95_annual = (1 + percentile_95_daily) ** 252 - 1

        egarch_params = {
            "omega": None,
            "alpha": None,
            "beta": None,
            "gamma": None,
            "fallback": "historical_volatility"
        }

        use_fallback = True
    
    # 4. 경고 메시지 생성
    model_name = "변동성 모델" if not use_fallback else "역사적 변동성"
    warning_message = (
        f"⚠️ 낙관적인 수익률 예측이 감지되었습니다.\n\n"
        f"{model_name} 기반 VaR 분석 결과 (최근 {period} 데이터):\n"
        f"- 95th Percentile 수익률: {percentile_95_annual:.1%} (연환산)\n"
        f"- 현재 변동성: {current_vol_annual:.1%}\n\n"
        f"보다 현실적인 수익률을 고려하시기 바랍니다."
    )

    return {
        "var_95_annual": float(var_annual),
        "percentile_5_annual": float(percentile_5_annual),
        "percentile_95_annual": float(percentile_95_annual),
        "current_volatility": float(current_vol_annual),
        "egarch_params": egarch_params,
        "warning_message": warning_message,
        "data_points": len(returns),
        "ticker": ticker,
        "period": period
    }

