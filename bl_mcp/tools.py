"""Black-Litterman portfolio optimization tools using PyPortfolioOpt."""

from typing import Optional

import numpy as np
import pandas as pd
from pypfopt import black_litterman, expected_returns, risk_models
from pypfopt.black_litterman import BlackLittermanModel

from .utils import data_loader, validators
from .utils.risk_models import calculate_var_egarch


def _calculate_portfolio_risk_aversion(
    prices: pd.DataFrame,
    mcaps: pd.Series,
    S: pd.DataFrame,
    frequency: int = 252,
    risk_free_rate: float = 0.02
) -> float:
    """
    Calculate risk aversion using portfolio-based approach (Idzorek method).

    Formula: δ = (E(r) - rf) / σ²_portfolio
    where σ²_portfolio = w_mkt^T × Σ × w_mkt

    This approach uses the actual portfolio's market cap weights and covariance,
    rather than relying on a single market proxy (e.g., SPY).

    Args:
        prices: Historical price data for portfolio assets
        mcaps: Market capitalizations for each asset
        S: Covariance matrix (annualized, from Ledoit-Wolf shrinkage)
        frequency: Trading days per year (default: 252)
        risk_free_rate: Annual risk-free rate (default: 0.02)

    Returns:
        Risk aversion coefficient (δ)
    """
    # 1. Calculate market cap weights
    w_mkt = mcaps / mcaps.sum()

    # 2. Calculate portfolio variance: w^T × Σ × w
    portfolio_var = float(w_mkt @ S @ w_mkt)

    # 3. Calculate portfolio expected return (market cap weighted average)
    returns = prices.pct_change().dropna()
    mean_returns = returns.mean() * frequency  # Annualized
    portfolio_return = float((w_mkt * mean_returns).sum())

    # 4. Calculate risk aversion: δ = (E(r) - rf) / σ²
    if portfolio_var <= 0:
        return 2.5  # Fallback for edge case

    delta = (portfolio_return - risk_free_rate) / portfolio_var

    # Ensure reasonable bounds (typically 1-10 for equities)
    return max(0.5, min(delta, 15.0))


def _parse_views(views: dict, tickers: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert view formats to P, Q matrices.
    
    Supports two formats:
    1. Dict-based P: {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
       - Absolute view: {"P": [{"AAPL": 1}], "Q": [0.10]}
       - Relative view: {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
    2. NumPy P: {"P": [[1, -1, 0]], "Q": [0.20]}
    
    Args:
        views: Views in P, Q format (dict or NumPy)
        tickers: List of ticker symbols in portfolio
        
    Returns:
        Tuple of (P matrix, Q vector) as numpy arrays
        
    Raises:
        ValueError: If views format is invalid or contains unknown tickers
    """
    # Ensure P, Q format is used
    if "P" not in views or "Q" not in views:
        raise ValueError(
            "Views must use P, Q format. "
            "Examples:\n"
            "  Absolute view: {'P': [{'AAPL': 1}], 'Q': [0.10]}\n"
            "  Relative view: {'P': [{'NVDA': 1, 'AAPL': -1}], 'Q': [0.20]}\n"
            "  NumPy format: {'P': [[1, -1, 0]], 'Q': [0.20]}"
        )
    
    # Parse P and Q
    P_input = views["P"]
    Q = np.array(views["Q"])
    
    # Validate Q
    if Q is None or len(Q) == 0:
        raise ValueError("Q cannot be empty")
    
    # Validate P
    if len(P_input) == 0:
        raise ValueError("P matrix cannot be empty")
    
    if isinstance(P_input[0], dict):
        # Dict-based P: [{"NVDA": 1, "AAPL": -1}, ...]
        P = np.zeros((len(P_input), len(tickers)))
        for i, view_dict in enumerate(P_input):
            for ticker, weight in view_dict.items():
                if ticker not in tickers:
                    raise ValueError(
                        f"Ticker '{ticker}' in P matrix not found in tickers list. "
                        f"Available tickers: {tickers}"
                    )
                j = tickers.index(ticker)
                P[i, j] = weight
    else:
        # NumPy P: [[1, -1, 0], ...]
        P = np.array(P_input)
        
        # Validate dimensions
        if P.shape[1] != len(tickers):
            raise ValueError(
                f"P matrix has {P.shape[1]} columns but there are {len(tickers)} tickers. "
                f"Dimensions must match."
            )
    
    # Validate P and Q dimensions match
    if P.shape[0] != len(Q):
        raise ValueError(
            f"P matrix has {P.shape[0]} rows but Q has {len(Q)} elements. "
            f"Number of views must match."
        )
    
    return P, Q


def _validate_views_optimism(
    views: dict,
    tickers: list[str],
    period: str = "3Y",
    threshold: float = 0.40
) -> list[str]:
    """
    지나치게 낙관적인 View를 검증하고 경고 메시지를 반환합니다.

    연환산 수익률이 threshold(기본 40%)를 초과하는 경우,
    변동성 모델 기반 VaR 분석을 수행하여
    현실적인 수익률 범위를 제시하고 경고 메시지를 반환합니다.

    Args:
        views: P, Q 형식의 View 딕셔너리
        tickers: 티커 리스트
        period: VaR 계산에 사용할 데이터 기간 (기본값: "3Y")
        threshold: 낙관적 View 판단 임계값 (기본값: 0.40 = 40%)

    Returns:
        경고 메시지 리스트 (경고가 없으면 빈 리스트)

    Note:
        경고 메시지를 반환하지만 최적화 프로세스는 중단하지 않습니다.
    """
    import logging

    warnings_list = []  # 경고 메시지를 저장할 리스트

    if not views or "P" not in views or "Q" not in views:
        return warnings_list  # View가 없으면 빈 리스트 반환

    P_input = views["P"]
    Q = np.array(views["Q"])

    logging.warning(f"🔍 VaR 검증 시작: Q = {Q}, threshold = {threshold}")

    # 각 View에 대해 검증
    for i, q_value in enumerate(Q):
        logging.warning(f"  📊 View {i+1}: Q = {q_value:.2%}, abs(Q) = {abs(q_value):.2%}")

        # Q 값이 threshold를 초과하는지 확인
        if abs(q_value) <= threshold:
            logging.warning(f"  ✅ View {i+1} 통과: {abs(q_value):.2%} <= {threshold:.2%}")
            continue

        logging.warning(f"  ⚠️ View {i+1} 임계값 초과: {abs(q_value):.2%} > {threshold:.2%}, VaR 분석 시작")

        # P 매트릭스에서 해당 View의 티커 추출
        if isinstance(P_input[0], dict):
            # Dict 형식: [{"NVDA": 1, "AAPL": -1}]
            view_dict = P_input[i]
            # 절대 View인지 상대 View인지 판단
            # 절대 View: 하나의 티커만 있고 weight가 1
            # 상대 View: 여러 티커가 있거나 weight 합이 0
            is_absolute = len(view_dict) == 1 and list(view_dict.values())[0] == 1

            if is_absolute:
                # 절대 View: 해당 티커에 대해 VaR 분석
                ticker = list(view_dict.keys())[0]
                logging.warning(f"  📈 절대 View 감지: {ticker} = {q_value:.2%}")

                try:
                    logging.warning(f"  🔄 VaR 계산 시작: {ticker}, period={period}")
                    var_result = calculate_var_egarch(ticker, period=period)
                    logging.warning(f"  ✅ VaR 계산 성공: 95th Percentile = {var_result['percentile_95_annual']:.2%}")

                    # 사용자 예측이 95th percentile을 초과하는지 확인
                    if q_value > var_result["percentile_95_annual"]:
                        logging.warning(f"  ⚠️ 낙관적 예측 감지: {q_value:.2%} > {var_result['percentile_95_annual']:.2%}")

                        # 경고 메시지 생성 및 저장
                        warning_msg = (
                            f"⚠️ VaR 경고 (View {i+1}): 지나치게 낙관적인 수익률 예측이 감지되었습니다.\n\n"
                            f"입력된 View: {ticker} {q_value:.1%} 수익 예측 (연환산)\n"
                            f"귀하의 예측({q_value:.1%})은 역사적 95th percentile({var_result['percentile_95_annual']:.1%})을 크게 상회합니다.\n\n"
                            f"{var_result['warning_message']}\n\n"
                            f"포트폴리오 최적화를 계속 진행하지만, 보다 현실적인 수익률을 고려하시기 바랍니다."
                        )
                        warnings_list.append(warning_msg)
                        logging.warning(warning_msg)
                    else:
                        logging.warning(f"  ✅ VaR 검증 통과: {q_value:.2%} <= {var_result['percentile_95_annual']:.2%}")

                except Exception as e:
                    # VaR 계산 실패 시 로그 출력하고 계속 진행
                    logging.error(f"  ❌ VaR 계산 실패: {ticker} - {type(e).__name__}: {e}")
                    logging.error(f"  ⚠️ VaR 검증 스킵됨 (계산 실패)")
                    import traceback
                    logging.error(traceback.format_exc())
            else:
                # 상대 View: 양수 weight를 가진 티커들에 대해 VaR 분석
                # 예: {"NVDA": 1, "AAPL": -1}, Q: 0.50
                # → NVDA가 AAPL 대비 50% 아웃퍼폼
                # 이 경우 NVDA의 절대 수익률이 50%라는 의미는 아니므로
                # 더 보수적으로 접근: 양수 티커의 VaR만 확인
                positive_tickers = [t for t, w in view_dict.items() if w > 0]

                for ticker in positive_tickers:
                    try:
                        var_result = calculate_var_egarch(ticker, period=period)

                        # 상대 View의 경우, Q 값이 95th percentile의 2배를 초과하면 경고
                        # (상대적 차이가 너무 크면 비현실적)
                        if abs(q_value) > var_result["percentile_95_annual"] * 2:
                            warning_msg = (
                                f"⚠️ VaR 경고 (View {i+1}): 상대 View가 지나치게 극단적일 수 있습니다.\n\n"
                                f"입력된 View: {ticker} 관련 상대 View {q_value:.1%}\n"
                                f"이 값은 {ticker}의 역사적 95th percentile({var_result['percentile_95_annual']:.1%})의 2배를 초과합니다.\n\n"
                                f"{var_result['warning_message']}\n\n"
                                f"포트폴리오 최적화를 계속 진행하지만, 보다 현실적인 수익률을 고려하시기 바랍니다."
                            )
                            warnings_list.append(warning_msg)
                            logging.warning(warning_msg)
                    except Exception as e:
                        # 기타 예외는 경고만 출력
                        logging.error(
                            f"VaR calculation failed for {ticker}: {e}. "
                            f"Skipping optimism validation."
                        )
        else:
            # NumPy 형식: [[1, -1, 0]]
            # 이 경우 티커 매핑이 명확하지 않으므로 간단히 Q 값만 확인
            # 절대값이 threshold를 초과하면 경고
            if abs(q_value) > threshold:
                warning_msg = (
                    f"⚠️ VaR 경고 (View {i+1}): 지나치게 낙관적인 수익률 예측이 감지되었습니다.\n\n"
                    f"View {i+1}의 예상 수익률: {q_value:.1%}\n"
                    f"NumPy 형식의 View는 자동 VaR 검증이 불가능합니다.\n"
                    f"이 수익률이 현실적인지 확인하시기 바랍니다."
                )
                warnings_list.append(warning_msg)
                logging.warning(warning_msg)

    return warnings_list


def _normalize_confidence(
    confidence: float | list | None,
    views: dict,
    tickers: list[str]
) -> list[float]:
    """
    Normalize confidence to list format.
    
    Handles confidence input types and converts to list:
    - None → [0.5, 0.5, ...] (default neutral confidence)
    - Float → [value, value, ...] (same confidence for all views)
    - List → validate and return (per-view confidence)
    
    Args:
        confidence: Confidence in float or list format
        views: Views dict (to determine number of views)
        tickers: List of tickers (unused, kept for compatibility)
        
    Returns:
        List of confidence values (one per view)
        
    Raises:
        ValueError: If confidence format is invalid or length doesn't match views
        TypeError: If confidence type is not supported
    """
    # Determine number of views from Q
    num_views = len(views["Q"])
    
    # Normalize to list based on input type
    if confidence is None:
        # Default: neutral confidence
        return [0.5] * num_views
    
    elif isinstance(confidence, (int, float)):
        # Single value: apply to all views
        validated = validators.validate_confidence(confidence)
        return [validated] * num_views
    
    elif isinstance(confidence, list):
        # List: validate length and values
        if len(confidence) != num_views:
            raise ValueError(
                f"Confidence length ({len(confidence)}) must match "
                f"number of views ({num_views})"
            )
        
        # Validate each confidence value
        validated_list = []
        for i, conf in enumerate(confidence):
            validated = validators.validate_confidence(conf)
            validated_list.append(validated)
        return validated_list
    
    else:
        raise TypeError(
            f"Invalid confidence type: {type(confidence).__name__}. "
            f"Expected float, list, or None"
        )


def get_asset_stats(
    tickers: list[str],
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_var: bool = True
) -> dict:
    """
    Get comprehensive statistics for a list of assets.

    This tool provides individual asset metrics along with correlation
    and covariance matrices - useful for understanding asset relationships
    before portfolio optimization.

    Args:
        tickers: List of ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        period: Relative period ("1Y", "6M", "3M") - RECOMMENDED
        start_date: Specific start date (YYYY-MM-DD)
        end_date: Specific end date (YYYY-MM-DD)
        include_var: Include VaR calculation (default: True)
                    Set to False for faster response (skips EGARCH VaR)

    Returns:
        Dictionary containing:
        - assets: Per-asset statistics
        - correlation_matrix: Asset correlations
        - covariance_matrix: Asset covariances (annualized)
        - period: Data period used
    """
    import logging
    logging.warning("=" * 80)
    logging.warning(f"🔍 get_asset_stats CALLED:")
    logging.warning(f"  📋 tickers = {tickers!r}")
    logging.warning(f"  📅 period = {period!r}")
    logging.warning("=" * 80)

    # Validate inputs
    validators.validate_tickers(tickers)

    # Resolve date range
    start_date, end_date = validators.resolve_date_range(
        period=period,
        start_date=start_date,
        end_date=end_date
    )

    # Load price data
    prices = data_loader.load_prices(tickers, start_date, end_date)

    # Calculate daily returns
    returns = prices.pct_change().dropna()

    # Calculate covariance matrix (annualized, Ledoit-Wolf shrinkage)
    S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()

    # Calculate correlation matrix from covariance
    # corr = cov / (std_i * std_j)
    std = np.sqrt(np.diag(S))
    correlation = S / np.outer(std, std)

    # Get market caps
    mcaps = data_loader.get_market_caps(tickers)

    # Risk-free rate for Sharpe calculation
    risk_free_rate = 0.02

    # Calculate per-asset statistics
    assets_stats = {}
    for ticker in tickers:
        ticker_returns = returns[ticker]

        # Current price (most recent)
        current_price = float(prices[ticker].iloc[-1])

        # Annual return (CAGR)
        total_return = (1 + ticker_returns).prod() - 1
        years = len(ticker_returns) / 252
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # Volatility (annualized)
        volatility = float(ticker_returns.std() * np.sqrt(252))

        # Sharpe ratio
        sharpe = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0

        # Market cap
        market_cap = float(mcaps.get(ticker, 0))

        # Historical Maximum Drawdown (MDD)
        ticker_prices = prices[ticker]
        cumulative = ticker_prices / ticker_prices.iloc[0]
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = float(drawdown.min())

        # VaR 95% (EGARCH-based) - optional for performance
        var_95 = None
        percentile_95 = None
        if include_var:
            try:
                # Use the same period as stats, default to "3Y" if not specified
                var_period = period if period else "3Y"
                # EGARCH needs sufficient data, minimum "1Y"
                if var_period in ["1M", "3M", "6M"]:
                    var_period = "1Y"  # Minimum for reliable EGARCH
                var_result = calculate_var_egarch(ticker, period=var_period)
                var_95 = round(var_result.get("var_95_annual", 0), 4)
                percentile_95 = round(var_result.get("percentile_95_annual", 0), 4)
            except Exception as e:
                logging.warning(f"  ⚠️ VaR calculation failed for {ticker}: {e}")

        assets_stats[ticker] = {
            "current_price": round(current_price, 2),
            "annual_return": round(float(annual_return), 4),
            "volatility": round(volatility, 4),
            "sharpe_ratio": round(float(sharpe), 4),
            "max_drawdown": round(max_drawdown, 4),
            "market_cap": market_cap,
            "var_95": var_95,
            "percentile_95": percentile_95,
        }

    # Convert matrices to nested dict format
    correlation_dict = {
        ticker: {
            other: round(float(correlation.loc[ticker, other]), 4)
            for other in tickers
        }
        for ticker in tickers
    }

    covariance_dict = {
        ticker: {
            other: round(float(S.loc[ticker, other]), 6)
            for other in tickers
        }
        for ticker in tickers
    }

    # Add visualization hints for LLMs to create dashboards
    visualization_hint = {
        "mandatory_disclaimer": "이 시각화는 참고용입니다. 투자 결정 전 원본 데이터를 확인하세요.",
        "safety_rules": {
            "must_do": [
                "Use ONLY data from this MCP response",
                "Show raw numbers table alongside every chart",
                "Include disclaimer in dashboard",
                "Correlation heatmap scale: fixed -1 to +1",
                "Keep at least 2 decimal places",
            ],
            "must_not_do": [
                "Fabricate or interpolate missing values",
                "Round aggressively (0.7523 → 0.75 loses precision)",
                "Auto-scale correlation heatmap",
                "Confuse percentage vs decimal (0.75 ≠ 75)",
            ],
        },
        "recommended_charts": [
            "bar_chart",
            "heatmap",
            "scatter_plot",
            "metrics_table",
            "raw_data_table",
        ],
        "bar_chart": {
            "title": "Asset Comparison",
            "data_field": "assets",
            "metrics": ["annual_return", "volatility", "sharpe_ratio", "max_drawdown"],
            "description": "Compare key metrics across all assets",
        },
        "heatmap": {
            "title": "Correlation Matrix",
            "data_field": "correlation_matrix",
            "color_scale": {"min": -1, "max": 1, "colors": ["red", "white", "green"]},
            "description": "Show asset correlations - FIXED scale -1 to +1",
        },
        "scatter_plot": {
            "title": "Risk vs Return",
            "data_field": "assets",
            "x": "volatility",
            "y": "annual_return",
            "label": "ticker",
            "description": "Plot each asset on risk-return space",
        },
        "metrics_table": {
            "title": "Asset Statistics",
            "data_field": "assets",
            "fields": [
                {"key": "current_price", "format": "currency", "label": "Price"},
                {"key": "annual_return", "format": "percent", "label": "Annual Return"},
                {"key": "volatility", "format": "percent", "label": "Volatility"},
                {"key": "sharpe_ratio", "format": "decimal", "label": "Sharpe"},
                {"key": "max_drawdown", "format": "percent", "label": "Max DD"},
                {"key": "var_95", "format": "percent", "label": "VaR 95%"},
                {"key": "percentile_95", "format": "percent", "label": "95th %ile"},
            ],
        },
    }

    # Add VaR-specific chart if VaR was included
    if include_var:
        visualization_hint["recommended_charts"].append("var_bar_chart")
        visualization_hint["var_bar_chart"] = {
            "title": "VaR Comparison",
            "data_field": "assets",
            "metrics": ["var_95", "percentile_95"],
            "description": "Compare VaR and 95th percentile across assets",
        }

    return {
        "assets": assets_stats,
        "correlation_matrix": correlation_dict,
        "covariance_matrix": covariance_dict,
        "period": {
            "start": start_date,
            "end": end_date or prices.index[-1].strftime("%Y-%m-%d"),
            "trading_days": len(prices)
        },
        "_visualization_hint": visualization_hint
    }


def optimize_portfolio_bl(
    tickers: list[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    views: Optional[dict] = None,
    confidence: Optional[float | list] = None,  # Can be float or list
    investment_style: str = "balanced",
    risk_aversion: Optional[float] = None,  # Advanced parameter
    sensitivity_range: Optional[list[float]] = None  # Sensitivity analysis
) -> dict:
    """
    Optimize portfolio using Black-Litterman model.
    
    This is the main optimization tool that combines market equilibrium with your views
    to produce optimal portfolio weights. It uses the Black-Litterman approach:
    - Starts with market-implied equilibrium returns (prior)
    - Incorporates your views with specified confidence (likelihood)
    - Produces posterior returns and optimal weights
    
    Date Range Options (mutually exclusive):
        - Provide 'period' for recent data (RECOMMENDED): "1Y", "3M", "1W"
        - Provide 'start_date' for historical data: "2023-01-01"
        - If both provided, 'start_date' takes precedence
        - If neither provided, defaults to "1Y" (1 year)
    
    Args:
        tickers: List of ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        start_date: Specific start date (YYYY-MM-DD). Use for absolute time ranges.
                   Only use if 'period' is not suitable. Do NOT use with 'period'.
        end_date: Specific end date (YYYY-MM-DD). Defaults to today if not provided.
        period: Relative period from today (e.g., '1M', '2Y').
               Supported: "1D", "7D", "1W", "1M", "3M", "6M", "1Y", "2Y", "5Y"
               Do NOT use with 'start_date'.
        views: Your investment views in P, Q format (optional).
              
              Format: {"P": [...], "Q": [...]}
              
              Examples:
              1. Absolute view (single asset):
                 {"P": [{"AAPL": 1}], "Q": [0.10]}
                 - AAPL expected to return 10%
                 
              2. Relative view:
                 {"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.20]}
                 - NVDA will outperform AAPL by 20%
                 
              3. Multiple views:
                 {"P": [{"NVDA": 1, "AAPL": -1}, {"NVDA": 1, "MSFT": -1}], "Q": [0.20, 0.15]}
                 - NVDA vs AAPL: 20% difference
                 - NVDA vs MSFT: 15% difference
                 
              4. NumPy format (advanced):
                 {"P": [[1, -1, 0]], "Q": [0.20]}
                 - Index-based (NVDA=0, AAPL=1, MSFT=2)
              
              If not provided or None, uses only market equilibrium (no views).
              
        confidence: How confident you are in your views (0.0 to 1.0, default: 0.5).
                   Can be:
                   - Single float: Same confidence for all views. E.g., 0.7 or 70
                   - List: Per-view confidence. E.g., [0.9, 0.8]
                   - None: Defaults to 0.5 (neutral)
                   Only used if views are provided.
                   
                   Confidence scale (Idzorek method):
                   - 0.95 (95%): Very confident
                   - 0.85 (85%): Confident
                   - 0.75 (75%): Quite confident
                   - 0.60 (60%): Somewhat confident
                   - 0.50 (50%): Neutral (default)
                   - 0.30 (30%): Uncertain
                   - 0.10 (10%): Very uncertain
        risk_aversion: Risk aversion parameter (optional, auto-calculated if not provided).
                      Higher values = more conservative (typically 2-3 for equities).
    
    Returns:
        Dictionary containing:

        Portfolio Allocation (THESE ARE WEIGHTS - sum to 100%):
        - weights: How much to invest in each asset (e.g., {"AAPL": 0.4, "MSFT": 0.6})
                  These ALWAYS sum to 100%. Use these for actual portfolio construction.

        Portfolio Performance (metrics for the TOTAL portfolio):
        - expected_return: Annualized expected return of the portfolio (e.g., 0.15 = 15%)
        - volatility: Annualized volatility/risk (e.g., 0.20 = 20%)
        - sharpe_ratio: Risk-adjusted return (expected_return / volatility)

        Individual Asset Expected Returns (NOT weights - do NOT sum to 100%):
        - prior_returns: Market equilibrium returns BEFORE views (π = δ × Σ × w_mkt)
                        These are what each asset is expected to return annually
                        based on market cap weights and covariance.
        - posterior_returns: Expected returns AFTER incorporating your views.
                            Shows how views shifted return expectations.
                            Compare with prior_returns to see view impact.

        IMPORTANT: prior_returns and posterior_returns are per-asset annual return
        expectations (e.g., NVDA: 38%, MSFT: 17%), NOT portfolio weights.
        They do NOT and should NOT sum to 100%.

        Other:
        - has_views: Whether views were incorporated (bool)
        - risk_aversion: The δ parameter used (higher = more conservative)
        - period: Data period used for calculation

    Raises:
        ValueError: Invalid tickers, views format, or insufficient data
        Exception: Other errors (MCP handles error responses automatically)
    
    Examples:
        # Absolute view
        Input: tickers=["AAPL", "MSFT", "GOOGL"], period="1Y",
               views={"P": [{"AAPL": 1}], "Q": [0.10]}, confidence=0.7
        
        # Relative view
        Input: tickers=["NVDA", "AAPL", "MSFT"], period="5Y",
               views={"P": [{"NVDA": 1, "AAPL": -1}], "Q": [0.30]}, confidence=[0.85]
    """
    # Debug logging to trace parameter values (CRITICAL for debugging!)
    import logging
    logging.warning("=" * 80)
    logging.warning(f"🔍 optimize_portfolio_bl CALLED:")
    logging.warning(f"  📋 tickers = {tickers!r}")
    logging.warning(f"  📊 views = {views!r} (type: {type(views).__name__})")
    logging.warning(f"  🎯 confidence = {confidence!r} (type: {type(confidence).__name__ if confidence else 'None'})")
    logging.warning(f"  📅 start_date = {start_date!r}")
    logging.warning(f"  📅 period = {period!r}")
    logging.warning("=" * 80)

    # Validate inputs
    validators.validate_tickers(tickers)
    validators.validate_risk_aversion(risk_aversion)

    # Note: Ticker order is preserved as provided by user
    # This is important for NumPy P format where indices matter
    logging.warning(f"  🔤 Tickers (order preserved): {tickers}")

    # CRITICAL: Check parameter types first (MCP may swap them!)
    if views is not None:
        if not isinstance(views, dict):
            # Check if views and confidence got swapped
            if isinstance(views, (int, float)) and isinstance(confidence, dict):
                # Swap them back
                logging.warning(f"⚠️ PARAMETER SWAP DETECTED! Swapping views={views} and confidence={confidence}")
                views, confidence = confidence, views
            else:
                raise ValueError(
                    f"views must be a dict or None, got {type(views).__name__}. "
                    f"Did you swap views and confidence?"
                )

    # Parse and validate views if provided
    var_warnings = []  # VaR 경고 메시지 저장
    if views:
        # Parse views to P, Q matrices (handles all three formats)
        P, Q = _parse_views(views, tickers)

        # Normalize confidence to list format
        conf_list = _normalize_confidence(confidence, views, tickers)

        # 🚨 NEW: 지나치게 낙관적인 View 검증
        # 연환산 40% 초과 시 EGARCH VaR 분석 수행
        # VaR 계산은 항상 3년 데이터 사용 (포트폴리오 최적화 period와 무관)
        var_warnings = _validate_views_optimism(
            views=views,
            tickers=tickers,
            period="3Y",  # VaR 계산용 기간 (항상 3년 고정)
            threshold=0.40  # 40% 임계값
        )

    # Resolve date range (handles period vs absolute dates)
    start_date, end_date = validators.resolve_date_range(
        period=period,
        start_date=start_date,
        end_date=end_date
    )

    # Load price data
    prices = data_loader.load_prices(tickers, start_date, end_date)

    # Calculate covariance matrix
    S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()

    # Get market caps automatically (Parquet cache → yfinance → equal weight fallback)
    mcaps = data_loader.get_market_caps(tickers)

    # Calculate risk aversion if not provided
    if risk_aversion is None:
        # Calculate risk aversion using portfolio-based approach (Idzorek method)
        # δ = (E(r) - rf) / σ²_portfolio
        base_risk_aversion = _calculate_portfolio_risk_aversion(
            prices,
            mcaps,
            S,  # Reuse already calculated covariance matrix
            frequency=252,  # Trading days per year
            risk_free_rate=0.02  # 2% annual risk-free rate
        )

        # Adjust based on investment style
        style_multipliers = {
            "aggressive": 0.5,    # δ × 0.5 (high concentration)
            "balanced": 1.0,      # δ × 1.0 (market equilibrium)
            "conservative": 2.0   # δ × 2.0 (high diversification)
        }

        multiplier = style_multipliers.get(investment_style, 1.0)
        risk_aversion = base_risk_aversion * multiplier

        logging.warning(
            f"  📊 Portfolio-based risk aversion (base): {base_risk_aversion:.3f}\n"
            f"  🎨 Investment style: {investment_style} (×{multiplier})\n"
            f"  🎯 Adjusted risk aversion: {risk_aversion:.3f}"
        )

    # Calculate market-implied prior returns
    market_prior = black_litterman.market_implied_prior_returns(
        mcaps, risk_aversion, S
    )

    # Create Black-Litterman model
    if views:
        # Idzorek method: User provides confidence → algorithm reverse-engineers Ω
        # P, Q (matrices) → Explicit view specification
        # conf_list (list) → Per-view confidence → Idzorek calculates optimal Ω

        bl = BlackLittermanModel(
            S,
            pi=market_prior,
            P=P,                     # Pick matrix (converted from dict/NumPy)
            Q=Q,                     # View returns vector
            omega="idzorek",         # Reverse-engineer Ω from confidence!
            view_confidences=conf_list  # Per-view confidence list
        )
        # Get posterior returns
        posterior_rets = bl.bl_returns()
        # Get optimized weights
        weights = bl.bl_weights()
        # Calculate portfolio metrics
        perf = bl.portfolio_performance(verbose=False)
    else:
        # No views: use market equilibrium weights directly
        # Market cap weighted portfolio
        weights = mcaps / mcaps.sum()
        posterior_rets = market_prior
        # Manual performance calculation for no-view case
        portfolio_return = weights.dot(posterior_rets)
        portfolio_variance = weights.dot(S).dot(weights)
        portfolio_vol = portfolio_variance ** 0.5
        sharpe = portfolio_return / portfolio_vol if portfolio_vol > 0 else 0
        perf = (portfolio_return, portfolio_vol, sharpe)

    result = {
        "weights": weights.to_dict() if hasattr(weights, 'to_dict') else dict(weights),
        "expected_return": perf[0],
        "volatility": perf[1],
        "sharpe_ratio": perf[2],
        "posterior_returns": posterior_rets.to_dict(),
        "prior_returns": market_prior.to_dict(),
        "risk_aversion": risk_aversion,
        "has_views": bool(views),
        "period": {
            "start": start_date,
            "end": end_date or prices.index[-1].strftime("%Y-%m-%d"),
            "days": len(prices)
        }
    }

    # VaR 경고가 있으면 결과에 포함
    if var_warnings:
        result["warnings"] = var_warnings

    # Sensitivity analysis (different confidence levels)
    if sensitivity_range and views:
        sensitivity_results = []
        for conf_value in sensitivity_range:
            try:
                # Normalize confidence to list format
                sens_conf_list = [conf_value] * len(views["Q"])

                # Create new BL model with different confidence
                sens_bl = BlackLittermanModel(
                    S,
                    pi=market_prior,
                    P=P,
                    Q=Q,
                    omega="idzorek",
                    view_confidences=sens_conf_list
                )
                sens_weights = sens_bl.bl_weights()
                sens_perf = sens_bl.portfolio_performance(verbose=False)

                sensitivity_results.append({
                    "confidence": conf_value,
                    "weights": sens_weights.to_dict() if hasattr(sens_weights, 'to_dict') else dict(sens_weights),
                    "expected_return": round(sens_perf[0], 4),
                    "volatility": round(sens_perf[1], 4),
                    "sharpe_ratio": round(sens_perf[2], 4),
                })
            except Exception as e:
                logging.warning(f"  ⚠️ Sensitivity analysis failed for confidence={conf_value}: {e}")

        result["sensitivity"] = sensitivity_results

    # Add visualization hints for LLMs to create dashboards
    visualization_hint = {
        "mandatory_disclaimer": "이 시각화는 참고용입니다. 투자 결정 전 원본 데이터를 확인하세요.",
        "safety_rules": {
            "must_do": [
                "Use ONLY data from this MCP response",
                "Show raw numbers table alongside every chart",
                "Include disclaimer in dashboard",
                "Verify weights sum to ~1.0 before pie chart",
                "Keep at least 2 decimal places",
            ],
            "must_not_do": [
                "Fabricate or interpolate missing values",
                "Round aggressively (0.4312 → 0.4 loses precision)",
                "Confuse percentage vs decimal (0.43 ≠ 43)",
            ],
        },
        "recommended_charts": [
            "pie_chart",
            "bar_chart",
            "metrics_table",
            "raw_data_table",
        ],
        "pie_chart": {
            "title": "Portfolio Allocation",
            "data_field": "weights",
            "description": "Show weight allocation - verify sum ≈ 1.0",
        },
        "bar_chart": {
            "title": "Prior vs Posterior Returns",
            "data_fields": ["prior_returns", "posterior_returns"],
            "description": "Compare market equilibrium returns vs adjusted returns after views",
        },
        "metrics_table": {
            "title": "Portfolio Metrics",
            "fields": [
                {"key": "expected_return", "format": "percent", "label": "Expected Return"},
                {"key": "volatility", "format": "percent", "label": "Volatility"},
                {"key": "sharpe_ratio", "format": "decimal", "label": "Sharpe Ratio"},
                {"key": "risk_aversion", "format": "decimal", "label": "Risk Aversion (δ)"},
            ],
        },
    }

    # Add sensitivity chart if sensitivity analysis was performed
    if sensitivity_range and views and "sensitivity" in result:
        visualization_hint["recommended_charts"].append("stacked_bar_chart")
        visualization_hint["stacked_bar_chart"] = {
            "title": "Sensitivity Analysis",
            "data_field": "sensitivity",
            "x": "confidence",
            "y": "weights",
            "description": "Show how weights change across different confidence levels",
        }

    # Add risk indicator
    visualization_hint["risk_indicator"] = {
        "title": "Risk Profile",
        "data_field": "risk_aversion",
        "scale": {"min": 1, "max": 15, "low_label": "Aggressive", "high_label": "Conservative"},
        "description": "Visual indicator of risk aversion level",
    }

    result["_visualization_hint"] = visualization_hint

    return result

    # Exceptions propagate to MCP - it handles error responses automatically


# =============================================================================
# Backtest Portfolio Implementation
# =============================================================================

# Strategy preset configurations
STRATEGY_PRESETS = {
    "buy_and_hold": {
        "rebalance_frequency": "none",
        "fees": 0.001,
        "slippage": 0.0005,
        "stop_loss": None,
        "take_profit": None,
        "trailing_stop": False,
        "max_drawdown_limit": None,
    },
    "passive_rebalance": {
        "rebalance_frequency": "monthly",
        "fees": 0.001,
        "slippage": 0.0005,
        "stop_loss": None,
        "take_profit": None,
        "trailing_stop": False,
        "max_drawdown_limit": None,
    },
    "risk_managed": {
        "rebalance_frequency": "monthly",
        "fees": 0.001,
        "slippage": 0.0005,
        "stop_loss": 0.10,
        "take_profit": None,
        "trailing_stop": False,
        "max_drawdown_limit": 0.20,
    },
}


def _calculate_returns_metrics(
    returns: pd.Series,
    risk_free_rate: float = 0.02
) -> dict:
    """
    Calculate all performance metrics from daily returns.

    Args:
        returns: Daily returns series
        risk_free_rate: Annual risk-free rate (default: 2%)

    Returns:
        Dictionary with performance metrics
    """
    if len(returns) == 0:
        return {
            "total_return": 0.0,
            "cagr": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "calmar_ratio": 0.0,
        }

    # Total return
    total_return = (1 + returns).prod() - 1

    # Annualized metrics
    total_days = len(returns)
    years = total_days / 252
    if years <= 0:
        years = total_days / 252  # Minimum

    # CAGR (Compound Annual Growth Rate)
    cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

    # Volatility (annualized)
    volatility = returns.std() * np.sqrt(252)

    # Sharpe ratio
    excess_return = cagr - risk_free_rate
    sharpe = excess_return / volatility if volatility > 0 else 0

    # Sortino ratio (downside deviation)
    negative_returns = returns[returns < 0]
    if len(negative_returns) > 0:
        downside_std = negative_returns.std() * np.sqrt(252)
    else:
        downside_std = volatility
    sortino = excess_return / downside_std if downside_std > 0 else 0

    # Max drawdown
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()

    # Calmar ratio (CAGR / |Max Drawdown|)
    calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0

    return {
        "total_return": float(total_return),
        "cagr": float(cagr),
        "volatility": float(volatility),
        "sharpe_ratio": float(sharpe),
        "sortino_ratio": float(sortino),
        "max_drawdown": float(max_drawdown),
        "calmar_ratio": float(calmar),
    }


def _calculate_benchmark_metrics(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.02
) -> dict:
    """
    Calculate benchmark comparison metrics.

    Args:
        portfolio_returns: Daily portfolio returns
        benchmark_returns: Daily benchmark returns
        risk_free_rate: Annual risk-free rate

    Returns:
        Dictionary with benchmark comparison metrics
    """
    # Align dates
    common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
    if len(common_dates) == 0:
        return {
            "benchmark_return": 0.0,
            "excess_return": 0.0,
            "alpha": 0.0,
            "beta": 1.0,
            "information_ratio": 0.0,
        }

    port_ret = portfolio_returns.loc[common_dates]
    bench_ret = benchmark_returns.loc[common_dates]

    # Total returns
    portfolio_total = (1 + port_ret).prod() - 1
    benchmark_total = (1 + bench_ret).prod() - 1
    excess_return = portfolio_total - benchmark_total

    # Beta (covariance / variance)
    covariance = port_ret.cov(bench_ret)
    benchmark_variance = bench_ret.var()
    beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0

    # Alpha (Jensen's alpha)
    years = len(common_dates) / 252
    if years > 0:
        portfolio_annual = (1 + portfolio_total) ** (1 / years) - 1
        benchmark_annual = (1 + benchmark_total) ** (1 / years) - 1
        alpha = portfolio_annual - (risk_free_rate + beta * (benchmark_annual - risk_free_rate))
    else:
        alpha = 0.0

    # Information ratio (excess return / tracking error)
    tracking_diff = port_ret - bench_ret
    tracking_error = tracking_diff.std() * np.sqrt(252)
    if tracking_error > 0 and years > 0:
        information_ratio = (excess_return / years) / tracking_error
    else:
        information_ratio = 0.0

    return {
        "benchmark_return": float(benchmark_total),
        "excess_return": float(excess_return),
        "alpha": float(alpha),
        "beta": float(beta),
        "information_ratio": float(information_ratio),
    }


def _get_rebalance_dates(
    prices: pd.DataFrame,
    frequency: str
) -> pd.DatetimeIndex:
    """
    Get rebalancing dates based on frequency.

    Args:
        prices: Price DataFrame
        frequency: Rebalancing frequency

    Returns:
        DatetimeIndex of rebalancing dates
    """
    if frequency == "none":
        return pd.DatetimeIndex([prices.index[0]])

    freq_map = {
        "weekly": "W",
        "monthly": "ME",
        "quarterly": "QE",
        "semi-annual": "6ME",
        "annual": "YE",
    }

    pandas_freq = freq_map.get(frequency, "ME")

    # Get end-of-period dates, then find the next trading day
    rebalance_dates = prices.resample(pandas_freq).last().index

    # Filter to only include dates in our price data
    valid_dates = rebalance_dates.intersection(prices.index)

    # If no valid dates, use first date
    if len(valid_dates) == 0:
        return pd.DatetimeIndex([prices.index[0]])

    return valid_dates


def _simulate_portfolio(
    prices: pd.DataFrame,
    target_weights: dict[str, float],
    config: dict,
    initial_capital: float
) -> tuple[pd.Series, dict]:
    """
    Simulate portfolio with rebalancing and risk controls.

    Args:
        prices: Price DataFrame (columns = tickers)
        target_weights: Target allocation weights
        config: Backtest configuration
        initial_capital: Starting capital

    Returns:
        Tuple of (portfolio values Series, metadata dict)
    """
    # Normalize weights
    weight_sum = sum(target_weights.values())
    weights = {k: v / weight_sum for k, v in target_weights.items()}

    # Get config values
    rebalance_frequency = config.get("rebalance_frequency", "monthly")
    fees = config.get("fees", 0.001)
    slippage = config.get("slippage", 0.0005)
    stop_loss = config.get("stop_loss")
    take_profit = config.get("take_profit")
    trailing_stop = config.get("trailing_stop", False)
    max_drawdown_limit = config.get("max_drawdown_limit")

    # Get rebalance dates
    rebalance_dates = _get_rebalance_dates(prices, rebalance_frequency)

    # Initialize tracking variables
    portfolio_values = []
    current_shares = {}
    total_fees_paid = 0.0
    num_rebalances = 0
    total_turnover = 0.0

    # Risk management tracking
    entry_prices = {}  # Track entry prices for stop-loss/take-profit
    highest_prices = {}  # Track highest prices for trailing stop
    peak_portfolio_value = initial_capital
    is_liquidated = False
    liquidation_reason = None

    # Holding period tracking
    holding_start_dates = {}

    for i, date in enumerate(prices.index):
        if is_liquidated:
            # Portfolio was liquidated, maintain cash position
            portfolio_values.append(portfolio_values[-1] if portfolio_values else initial_capital)
            continue

        current_prices = prices.loc[date]

        # Calculate current portfolio value
        if i == 0:
            current_value = initial_capital
        else:
            current_value = sum(
                current_shares.get(t, 0) * current_prices[t]
                for t in weights if t in current_prices
            )

        # Update peak for drawdown calculation
        if current_value > peak_portfolio_value:
            peak_portfolio_value = current_value

        # Check max drawdown limit
        if max_drawdown_limit is not None:
            current_drawdown = (peak_portfolio_value - current_value) / peak_portfolio_value
            if current_drawdown > max_drawdown_limit:
                is_liquidated = True
                liquidation_reason = f"max_drawdown_exceeded ({current_drawdown:.2%})"
                portfolio_values.append(current_value)
                continue

        # Check stop-loss / take-profit for each position
        for ticker in list(current_shares.keys()):
            if current_shares[ticker] <= 0:
                continue

            if ticker not in entry_prices:
                continue

            entry = entry_prices[ticker]
            current = current_prices[ticker]

            # Update highest price for trailing stop
            if ticker not in highest_prices:
                highest_prices[ticker] = current
            else:
                highest_prices[ticker] = max(highest_prices[ticker], current)

            # Calculate return from entry
            if trailing_stop and stop_loss is not None:
                # Trailing stop: compare to highest price
                return_from_high = (current - highest_prices[ticker]) / highest_prices[ticker]
                if return_from_high < -stop_loss:
                    # Sell this position
                    sell_value = current_shares[ticker] * current * (1 - fees - slippage)
                    total_fees_paid += current_shares[ticker] * current * (fees + slippage)
                    current_shares[ticker] = 0
                    del entry_prices[ticker]
                    del highest_prices[ticker]
            else:
                return_from_entry = (current - entry) / entry

                # Stop-loss check
                if stop_loss is not None and return_from_entry < -stop_loss:
                    sell_value = current_shares[ticker] * current * (1 - fees - slippage)
                    total_fees_paid += current_shares[ticker] * current * (fees + slippage)
                    current_shares[ticker] = 0
                    del entry_prices[ticker]

                # Take-profit check
                if take_profit is not None and return_from_entry > take_profit:
                    sell_value = current_shares[ticker] * current * (1 - fees - slippage)
                    total_fees_paid += current_shares[ticker] * current * (fees + slippage)
                    current_shares[ticker] = 0
                    del entry_prices[ticker]

        # Rebalancing
        should_rebalance = (date in rebalance_dates) or (i == 0)

        if should_rebalance and not is_liquidated:
            # Recalculate current value after any stop-loss/take-profit
            current_value = sum(
                current_shares.get(t, 0) * current_prices[t]
                for t in weights if t in current_prices
            )
            if i == 0:
                current_value = initial_capital

            # Calculate turnover
            if current_shares and current_value > 0:
                old_weights = {
                    t: current_shares.get(t, 0) * current_prices[t] / current_value
                    for t in weights if t in current_prices
                }
                turnover = sum(abs(weights[t] - old_weights.get(t, 0)) for t in weights) / 2
                total_turnover += turnover

            # Rebalance to target weights
            for ticker in weights:
                if ticker not in current_prices:
                    continue

                target_value = current_value * weights[ticker]
                current_holding_value = current_shares.get(ticker, 0) * current_prices[ticker]
                trade_value = abs(target_value - current_holding_value)

                # Apply fees and slippage
                if trade_value > 0:
                    total_fees_paid += trade_value * (fees + slippage)

                # Update shares
                new_shares = target_value / current_prices[ticker]
                current_shares[ticker] = new_shares

                # Update entry price for new positions
                if new_shares > 0:
                    entry_prices[ticker] = current_prices[ticker]
                    highest_prices[ticker] = current_prices[ticker]
                    if ticker not in holding_start_dates:
                        holding_start_dates[ticker] = date

            num_rebalances += 1

        # Calculate final portfolio value for the day
        final_value = sum(
            current_shares.get(t, 0) * current_prices[t]
            for t in weights if t in current_prices
        )
        portfolio_values.append(final_value)

    # Create portfolio value series
    portfolio_series = pd.Series(portfolio_values, index=prices.index)

    # Calculate holding periods
    holding_periods = {}
    end_date = prices.index[-1]
    for ticker, start_date in holding_start_dates.items():
        days = (end_date - start_date).days
        holding_periods[ticker] = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "days": days,
            "years": days / 365,
            "is_long_term": days >= 365,  # For tax purposes
        }

    # Calculate drawdown details
    cumulative = portfolio_series / portfolio_series.iloc[0]
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max

    # Find max drawdown details
    max_dd_idx = drawdown.idxmin()
    max_dd_value = drawdown.min()

    # Find drawdown start (peak before max drawdown)
    peak_idx = cumulative.loc[:max_dd_idx].idxmax()

    # Find recovery date (when portfolio returns to peak)
    recovery_idx = None
    recovery_days = None
    after_trough = cumulative.loc[max_dd_idx:]
    recovered = after_trough[after_trough >= cumulative.loc[peak_idx]]
    if len(recovered) > 0:
        recovery_idx = recovered.index[0]
        recovery_days = (recovery_idx - max_dd_idx).days

    drawdown_details = {
        "max_drawdown": float(max_dd_value),
        "max_drawdown_start": peak_idx.strftime("%Y-%m-%d"),
        "max_drawdown_end": max_dd_idx.strftime("%Y-%m-%d"),
        "recovery_date": recovery_idx.strftime("%Y-%m-%d") if recovery_idx else None,
        "recovery_days": recovery_days,
    }

    metadata = {
        "total_fees_paid": total_fees_paid,
        "num_rebalances": num_rebalances,
        "turnover": total_turnover,
        "is_liquidated": is_liquidated,
        "liquidation_reason": liquidation_reason,
        "holding_periods": holding_periods,
        "drawdown_details": drawdown_details,
        "portfolio_series": portfolio_series,  # Pass for timeseries generation
    }

    return portfolio_series, metadata


def backtest_portfolio(
    tickers: list[str],
    weights: dict[str, float],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    strategy: str = "passive_rebalance",
    benchmark: Optional[str] = "SPY",
    initial_capital: float = 10000.0,
    custom_config: Optional[dict] = None,
    compare_strategies: bool = False,
    include_equal_weight: bool = False,
    timeseries_freq: str = "monthly"
) -> dict:
    """
    Backtest a portfolio with specified weights.

    This tool evaluates how a portfolio would have performed historically,
    including realistic transaction costs and rebalancing.

    RECOMMENDED WORKFLOW:
    1. First call optimize_portfolio_bl() to get optimal weights
    2. Then call backtest_portfolio() with those weights to validate performance

    Args:
        tickers: List of ticker symbols in the portfolio
        weights: Target weights from optimize_portfolio_bl output
                 Example: {"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25}
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        period: Relative period ("1Y", "3Y", "5Y") - RECOMMENDED
        strategy: Backtesting strategy preset
                 - "buy_and_hold": No rebalancing, baseline comparison
                 - "passive_rebalance": Monthly rebalancing (DEFAULT)
                 - "risk_managed": Monthly rebalancing + stop-loss + drawdown limit
        benchmark: Benchmark ticker for comparison (default: "SPY")
                  Set to None to skip benchmark comparison
        initial_capital: Starting capital (default: 10000)
        custom_config: Advanced config to override strategy preset (dict)
                      See BacktestConfig for available options
        compare_strategies: If True, compare all strategy presets (default: False)
        include_equal_weight: If True, include equal-weight portfolio comparison (default: False)

    Returns:
        Dictionary containing performance metrics, costs, and benchmark comparison.
        If compare_strategies=True, includes 'comparisons' with results for all strategies.
        If include_equal_weight=True, includes 'equal_weight' comparison.
        Always includes 'timeseries' (monthly sampled) and 'drawdown_details'.
    """
    import logging
    logging.warning("=" * 80)
    logging.warning(f"🔍 backtest_portfolio CALLED:")
    logging.warning(f"  📋 tickers = {tickers!r}")
    logging.warning(f"  ⚖️ weights = {weights!r}")
    logging.warning(f"  📅 period = {period!r}")
    logging.warning(f"  🎯 strategy = {strategy!r}")
    logging.warning("=" * 80)

    # Validate inputs
    validators.validate_tickers(tickers)

    # Convert weights to dict if pandas Series
    if hasattr(weights, 'to_dict'):
        weights = weights.to_dict()

    if not weights:
        raise ValueError("weights cannot be empty")

    # Check all weight tickers are in tickers list
    missing = set(weights.keys()) - set(tickers)
    if missing:
        raise ValueError(f"Tickers in weights not in tickers list: {missing}")

    # Validate weights are positive
    for ticker, weight in weights.items():
        if weight < 0:
            raise ValueError(f"Weight for {ticker} cannot be negative: {weight}")

    # Validate timeseries_freq
    valid_freqs = ["daily", "weekly", "monthly"]
    if timeseries_freq not in valid_freqs:
        raise ValueError(f"timeseries_freq must be one of {valid_freqs}, got '{timeseries_freq}'")

    # Get configuration from strategy or custom_config
    if custom_config is not None:
        # Use custom config (override strategy)
        config = {**STRATEGY_PRESETS["passive_rebalance"], **custom_config}
    else:
        # Use strategy preset
        if strategy not in STRATEGY_PRESETS:
            raise ValueError(
                f"Unknown strategy '{strategy}'. "
                f"Available: {list(STRATEGY_PRESETS.keys())}"
            )
        config = STRATEGY_PRESETS[strategy]

    # Resolve date range
    start_date, end_date = validators.resolve_date_range(
        period=period,
        start_date=start_date,
        end_date=end_date
    )

    # Load price data
    all_tickers = list(set(tickers) | ({benchmark} if benchmark else set()))
    prices = data_loader.load_prices(all_tickers, start_date, end_date)

    # Separate benchmark
    benchmark_prices = None
    if benchmark and benchmark in prices.columns:
        benchmark_prices = prices[benchmark]

    # Get portfolio prices only
    portfolio_tickers = [t for t in tickers if t in prices.columns]
    if len(portfolio_tickers) == 0:
        raise ValueError(f"No valid tickers found in data: {tickers}")

    portfolio_prices = prices[portfolio_tickers]

    # Filter weights to only include available tickers
    available_weights = {t: weights[t] for t in portfolio_tickers if t in weights}

    # Simulate portfolio
    portfolio_values, metadata = _simulate_portfolio(
        portfolio_prices,
        available_weights,
        config,
        initial_capital
    )

    # Calculate returns
    portfolio_returns = portfolio_values.pct_change().dropna()

    # Calculate performance metrics
    metrics = _calculate_returns_metrics(portfolio_returns)

    # Add portfolio values
    metrics["initial_capital"] = initial_capital
    metrics["final_value"] = float(portfolio_values.iloc[-1])

    # Add cost and trading info
    metrics["total_fees_paid"] = metadata["total_fees_paid"]
    metrics["num_rebalances"] = metadata["num_rebalances"]
    metrics["turnover"] = metadata["turnover"]

    # Add risk management info
    metrics["is_liquidated"] = metadata["is_liquidated"]
    metrics["liquidation_reason"] = metadata["liquidation_reason"]

    # Add holding periods (for tax calculation)
    metrics["holding_periods"] = metadata["holding_periods"]

    # Benchmark comparison
    benchmark_series = None
    if benchmark_prices is not None:
        benchmark_returns = benchmark_prices.pct_change().dropna()
        benchmark_metrics = _calculate_benchmark_metrics(
            portfolio_returns,
            benchmark_returns
        )
        metrics.update(benchmark_metrics)
        # Calculate benchmark series for timeseries
        benchmark_series = (1 + benchmark_returns).cumprod() * initial_capital

    # Period info
    metrics["period"] = {
        "start": start_date,
        "end": end_date or portfolio_prices.index[-1].strftime("%Y-%m-%d"),
        "trading_days": len(portfolio_prices),
    }

    # Strategy info
    metrics["strategy"] = strategy
    metrics["config"] = config

    # Add drawdown_details
    metrics["drawdown_details"] = metadata["drawdown_details"]

    # Generate timeseries (configurable frequency)
    portfolio_series = metadata["portfolio_series"]

    # Determine resampling rule and date format
    freq_map = {
        "daily": (None, "%Y-%m-%d"),     # No resampling
        "weekly": ("W-FRI", "%Y-%m-%d"),  # Weekly (Friday)
        "monthly": ("ME", "%Y-%m"),       # Monthly (end)
    }
    resample_rule, date_format = freq_map.get(timeseries_freq, ("ME", "%Y-%m"))

    if resample_rule is None:
        # Daily: no resampling
        sampled_values = portfolio_series
    else:
        sampled_values = portfolio_series.resample(resample_rule).last()

    # Calculate drawdown at each point
    cumulative = portfolio_series / portfolio_series.iloc[0]
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max

    if resample_rule is None:
        sampled_drawdown = drawdown
    else:
        sampled_drawdown = drawdown.resample(resample_rule).last()

    # Resample benchmark if needed
    sampled_benchmark = None
    if benchmark_series is not None:
        if resample_rule is None:
            sampled_benchmark = benchmark_series
        else:
            sampled_benchmark = benchmark_series.resample(resample_rule).last()

    # Build timeseries list
    timeseries = []
    for date in sampled_values.index:
        entry = {
            "date": date.strftime(date_format),
            "value": round(float(sampled_values.loc[date]), 2),
            "drawdown": round(float(sampled_drawdown.loc[date]), 4),
        }
        if sampled_benchmark is not None and date in sampled_benchmark.index:
            entry["benchmark"] = round(float(sampled_benchmark.loc[date]), 2)
        timeseries.append(entry)

    metrics["timeseries"] = timeseries

    # Strategy comparisons
    if compare_strategies:
        comparisons = {}
        for strat_name, strat_config in STRATEGY_PRESETS.items():
            if strat_name == strategy:
                continue  # Skip the primary strategy
            try:
                strat_values, strat_metadata = _simulate_portfolio(
                    portfolio_prices,
                    available_weights,
                    strat_config,
                    initial_capital
                )
                strat_returns = strat_values.pct_change().dropna()
                strat_metrics = _calculate_returns_metrics(strat_returns)
                strat_metrics["final_value"] = float(strat_values.iloc[-1])
                strat_metrics["is_liquidated"] = strat_metadata["is_liquidated"]
                strat_metrics["liquidation_reason"] = strat_metadata["liquidation_reason"]
                comparisons[strat_name] = strat_metrics
            except Exception as e:
                logging.warning(f"  ⚠️ Strategy comparison failed for {strat_name}: {e}")
        metrics["comparisons"] = comparisons

    # Equal weight comparison
    if include_equal_weight:
        try:
            equal_weights = {t: 1.0 / len(available_weights) for t in available_weights}
            eq_values, eq_metadata = _simulate_portfolio(
                portfolio_prices,
                equal_weights,
                config,
                initial_capital
            )
            eq_returns = eq_values.pct_change().dropna()
            eq_metrics = _calculate_returns_metrics(eq_returns)
            eq_metrics["final_value"] = float(eq_values.iloc[-1])
            eq_metrics["weights"] = equal_weights
            metrics["equal_weight"] = eq_metrics
        except Exception as e:
            logging.warning(f"  ⚠️ Equal weight comparison failed: {e}")

    # Add visualization hints for LLMs to create dashboards
    visualization_hint = {
        "mandatory_disclaimer": "이 시각화는 참고용입니다. 투자 결정 전 원본 데이터를 확인하세요.",
        "safety_rules": {
            "must_do": [
                "Use ONLY data from this MCP response",
                "Show raw numbers table alongside every chart",
                "Include disclaimer in dashboard",
                "Drawdowns MUST be visually prominent (red area below 0)",
                "Keep at least 2 decimal places",
            ],
            "must_not_do": [
                "Fabricate or interpolate missing timeseries points",
                "Round aggressively (15.23% → 15% loses precision)",
                "Hide drawdown troughs or flatten Y-axis",
                "Confuse percentage vs decimal (0.15 ≠ 15)",
            ],
        },
        "recommended_charts": [
            "line_chart",
            "area_chart",
            "metrics_table",
            "pie_chart",
            "raw_data_table",
        ],
        "line_chart": {
            "title": "Portfolio Performance",
            "data_field": "timeseries",
            "x": "date",
            "y": ["value", "benchmark"],
            "description": "Compare portfolio value vs benchmark over time",
        },
        "area_chart": {
            "title": "Drawdown",
            "data_field": "timeseries",
            "x": "date",
            "y": "drawdown",
            "description": "Show drawdown as RED area below 0 - MUST be visible",
        },
        "metrics_table": {
            "title": "Key Metrics",
            "fields": [
                {"key": "sharpe_ratio", "format": "decimal", "label": "Sharpe Ratio"},
                {"key": "cagr", "format": "percent", "label": "CAGR"},
                {"key": "max_drawdown", "format": "percent", "label": "Max Drawdown"},
                {"key": "volatility", "format": "percent", "label": "Volatility"},
                {"key": "initial_capital", "format": "currency", "label": "Initial Capital"},
                {"key": "final_value", "format": "currency", "label": "Final Value"},
                {"key": "total_fees_paid", "format": "currency", "label": "Total Fees"},
            ],
        },
        "pie_chart": {
            "title": "Portfolio Allocation",
            "data_field": "weights",
            "description": "Show weight allocation by ticker (use input weights)",
        },
    }

    # Add bar_chart hint if compare_strategies is enabled
    if compare_strategies:
        visualization_hint["recommended_charts"].append("bar_chart")
        visualization_hint["bar_chart"] = {
            "title": "Strategy Comparison",
            "data_field": "comparisons",
            "metrics": ["sharpe_ratio", "total_return", "max_drawdown"],
            "description": "Compare performance across different strategies",
        }
        # Scale guidance for mixed-scale metrics (radar chart issue)
        visualization_hint["scale_guidance"] = {
            "ratio_metrics": {
                "keys": ["sharpe_ratio", "sortino_ratio", "calmar_ratio"],
                "typical_range": [-1, 3],
                "description": "Risk-adjusted ratios. Good: >1, Excellent: >2",
            },
            "percent_metrics": {
                "keys": ["total_return", "cagr", "volatility", "max_drawdown"],
                "typical_range": [-50, 100],
                "description": "Percentage values. Display as % with 1-2 decimals",
            },
            "radar_chart_warning": (
                "AVOID radar charts when mixing ratio_metrics with percent_metrics. "
                "Ratios (0-3 range) get crushed when normalized with percentages (0-100%). "
                "Instead: use grouped bar charts OR separate radar charts per metric type."
            ),
        }

    metrics["_visualization_hint"] = visualization_hint

    return metrics
