"""Black-Litterman portfolio optimization tools using PyPortfolioOpt."""

from typing import Optional

import pandas as pd
from pypfopt import black_litterman, expected_returns, risk_models
from pypfopt.black_litterman import BlackLittermanModel

from .utils import data_loader, validators


def calculate_expected_returns(
    tickers: list[str],
    start_date: str,
    end_date: Optional[str] = None,
    method: str = "historical_mean"
) -> dict:
    """
    Calculate expected returns for assets.
    
    Args:
        tickers: List of ticker symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), defaults to most recent
        method: Calculation method ("historical_mean" or "ema")
    
    Returns:
        Dict with success status and expected returns
    """
    try:
        # Validate inputs
        validators.validate_tickers(tickers)
        validators.validate_date_range(start_date, end_date)
        
        # Load price data
        prices = data_loader.load_prices(tickers, start_date, end_date)
        
        # Calculate expected returns using PyPortfolioOpt
        if method == "historical_mean":
            mu = expected_returns.mean_historical_return(prices)
        elif method == "ema":
            mu = expected_returns.ema_historical_return(prices)
        else:
            raise ValueError(
                f"Unknown method: {method}. "
                f"Use 'historical_mean' or 'ema'"
            )
        
        return {
            "success": True,
            "tickers": tickers,
            "expected_returns": mu.to_dict(),
            "method": method,
            "period": {
                "start": start_date,
                "end": end_date or prices.index[-1].strftime("%Y-%m-%d"),
                "days": len(prices)
            }
        }
    
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }


def calculate_covariance_matrix(
    tickers: list[str],
    start_date: str,
    end_date: Optional[str] = None,
    method: str = "ledoit_wolf"
) -> dict:
    """
    Calculate covariance matrix for assets.
    
    Args:
        tickers: List of ticker symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), defaults to most recent
        method: Calculation method ("ledoit_wolf", "sample", or "exp")
    
    Returns:
        Dict with success status and covariance matrix
    """
    try:
        # Validate inputs
        validators.validate_tickers(tickers)
        validators.validate_date_range(start_date, end_date)
        
        # Load price data
        prices = data_loader.load_prices(tickers, start_date, end_date)
        
        # Calculate covariance matrix using PyPortfolioOpt
        if method == "ledoit_wolf":
            S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()
        elif method == "sample":
            S = risk_models.sample_cov(prices)
        elif method == "exp":
            S = risk_models.exp_cov(prices)
        else:
            raise ValueError(
                f"Unknown method: {method}. "
                f"Use 'ledoit_wolf', 'sample', or 'exp'"
            )
        
        return {
            "success": True,
            "tickers": tickers,
            "covariance_matrix": S.to_dict(),
            "method": method,
            "period": {
                "start": start_date,
                "end": end_date or prices.index[-1].strftime("%Y-%m-%d"),
                "days": len(prices)
            }
        }
    
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }


def create_investor_view(
    view_dict: dict,
    tickers: list[str],
    confidence: float = 0.5
) -> dict:
    """
    Create investor views for Black-Litterman model.
    
    Uses PyPortfolioOpt's absolute_views format - simply pass a dict!
    
    Args:
        view_dict: Dictionary mapping tickers to expected returns
                  Example: {"AAPL": 0.10, "MSFT": -0.05}
        tickers: List of all valid ticker symbols
        confidence: Confidence level (0.0 to 1.0)
    
    Returns:
        Dict with success status and view information
    """
    try:
        # Validate inputs
        validators.validate_tickers(tickers)
        validators.validate_view_dict(view_dict, tickers)
        validators.validate_confidence(confidence)
        
        return {
            "success": True,
            "views": view_dict,
            "confidence": confidence,
            "num_views": len(view_dict),
            "note": "Use these views with optimize_portfolio_bl"
        }
    
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }


def optimize_portfolio_bl(
    tickers: list[str],
    start_date: str,
    end_date: Optional[str] = None,
    market_caps: Optional[dict] = None,
    views: Optional[dict] = None,
    confidence: float = 0.5,
    risk_aversion: Optional[float] = None
) -> dict:
    """
    Optimize portfolio using Black-Litterman model.
    
    This function wraps PyPortfolioOpt's BlackLittermanModel:
    - Uses market-implied prior returns
    - Applies Idzorek's method for view confidences
    - Returns optimized portfolio weights
    
    Args:
        tickers: List of ticker symbols
        start_date: Start date for historical data (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), defaults to most recent
        market_caps: Dict of market capitalizations (optional, will use equal if not provided)
        views: Investor views dict {"AAPL": 0.10, ...} (optional)
        confidence: Confidence level for views (0.0 to 1.0)
        risk_aversion: Risk aversion parameter (auto-calculated if not provided)
    
    Returns:
        Dict with success status and portfolio weights
    """
    try:
        # Validate inputs
        validators.validate_tickers(tickers)
        validators.validate_date_range(start_date, end_date)
        validators.validate_confidence(confidence)
        validators.validate_risk_aversion(risk_aversion)
        
        if views:
            validators.validate_view_dict(views, tickers)
        
        # Load price data
        prices = data_loader.load_prices(tickers, start_date, end_date)
        
        # Calculate covariance matrix
        S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()
        
        # Handle market caps
        if market_caps is None:
            # Use equal market caps if not provided
            market_caps = {ticker: 1.0 for ticker in tickers}
        
        # Convert to Series with explicit index
        mcaps = pd.Series(market_caps, index=tickers)
        
        # Calculate risk aversion if not provided
        if risk_aversion is None:
            # Use default market-implied risk aversion
            # Typically around 2-3 for equity markets
            risk_aversion = 2.5
        
        # Calculate market-implied prior returns
        market_prior = black_litterman.market_implied_prior_returns(
            mcaps, risk_aversion, S
        )
        
        # Create Black-Litterman model
        if views:
            # With views: use Idzorek's method for confidence
            bl = BlackLittermanModel(
                S,
                pi=market_prior,
                absolute_views=views,
                omega="idzorek",  # Idzorek's confidence method!
                view_confidences=[confidence] * len(views)
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
        
        return {
            "success": True,
            "weights": weights,
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
    
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
