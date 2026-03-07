"""Risk metrics — VaR, Sharpe ratio, portfolio risk calculations."""

import numpy as np
import yfinance as yf


def calculate_var(
    ticker: str,
    period: str = "1y",
    confidence: float = 0.95,
    investment: float = 10000.0,
) -> dict:
    """Calculate Value at Risk (VaR) for a single stock.

    Args:
        ticker: Stock ticker symbol.
        period: Historical period for returns (1mo, 3mo, 6mo, 1y, 2y).
        confidence: Confidence level (0.90, 0.95, 0.99).
        investment: Portfolio value in USD.
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)

    if df.empty or len(df) < 10:
        return {"ticker": ticker, "error": "Insufficient data"}

    returns = df["Close"].pct_change().dropna().values
    mean = float(np.mean(returns))
    std = float(np.std(returns))

    # Parametric (normal) VaR
    z_score = float(np.abs(np.percentile(np.random.standard_normal(100000), (1 - confidence) * 100)))
    var_pct = mean - z_score * std
    var_usd = abs(var_pct) * investment

    # Historical VaR
    hist_var_pct = float(np.percentile(returns, (1 - confidence) * 100))
    hist_var_usd = abs(hist_var_pct) * investment

    return {
        "ticker": ticker.upper(),
        "period": period,
        "confidence": confidence,
        "investment": investment,
        "daily_returns": {
            "mean": round(mean * 100, 4),
            "std": round(std * 100, 4),
            "observations": len(returns),
        },
        "parametric_var": {
            "percent": round(abs(var_pct) * 100, 4),
            "usd": round(var_usd, 2),
        },
        "historical_var": {
            "percent": round(abs(hist_var_pct) * 100, 4),
            "usd": round(hist_var_usd, 2),
        },
    }


def calculate_sharpe_ratio(
    ticker: str,
    period: str = "1y",
    risk_free_rate: float = 0.05,
) -> dict:
    """Calculate the Sharpe ratio for a stock.

    Args:
        ticker: Stock ticker symbol.
        period: Historical period (1mo, 3mo, 6mo, 1y, 2y, 5y).
        risk_free_rate: Annual risk-free rate (default 5%).
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)

    if df.empty or len(df) < 10:
        return {"ticker": ticker, "error": "Insufficient data"}

    returns = df["Close"].pct_change().dropna().values
    trading_days = 252

    annual_return = float(np.mean(returns) * trading_days)
    annual_std = float(np.std(returns) * np.sqrt(trading_days))

    sharpe = (annual_return - risk_free_rate) / annual_std if annual_std > 0 else 0.0

    return {
        "ticker": ticker.upper(),
        "period": period,
        "risk_free_rate": risk_free_rate,
        "annual_return": round(annual_return * 100, 2),
        "annual_volatility": round(annual_std * 100, 2),
        "sharpe_ratio": round(sharpe, 4),
        "interpretation": _interpret_sharpe(sharpe),
    }


def calculate_portfolio_risk(
    tickers: list[str],
    weights: list[float] | None = None,
    period: str = "1y",
) -> dict:
    """Calculate portfolio risk metrics for multiple stocks.

    Args:
        tickers: List of stock ticker symbols.
        weights: Portfolio weights (must sum to 1). Equal weights if omitted.
        period: Historical period for returns.
    """
    n = len(tickers)
    if weights is None:
        weights = [1.0 / n] * n

    if len(weights) != n:
        return {"error": "Number of weights must match number of tickers"}

    if abs(sum(weights) - 1.0) > 0.01:
        return {"error": "Weights must sum to 1.0"}

    # Fetch returns
    returns_data = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty or len(df) < 10:
            return {"error": f"Insufficient data for {ticker}"}
        returns_data[ticker] = df["Close"].pct_change().dropna()

    # Align dates
    import pandas as pd
    df_returns = pd.DataFrame(returns_data).dropna()

    if len(df_returns) < 10:
        return {"error": "Insufficient overlapping data"}

    w = np.array(weights)
    cov_matrix = df_returns.cov().values * 252  # annualized
    corr_matrix = df_returns.corr().values

    portfolio_var = float(w @ cov_matrix @ w)
    portfolio_std = float(np.sqrt(portfolio_var))

    annual_returns = {
        t: round(float(df_returns[t].mean() * 252) * 100, 2)
        for t in tickers
    }
    portfolio_return = float(w @ np.array([df_returns[t].mean() * 252 for t in tickers]))

    return {
        "tickers": [t.upper() for t in tickers],
        "weights": [round(w, 4) for w in weights],
        "period": period,
        "individual_returns": annual_returns,
        "portfolio_return": round(portfolio_return * 100, 2),
        "portfolio_volatility": round(portfolio_std * 100, 2),
        "correlation_matrix": {
            tickers[i]: {
                tickers[j]: round(float(corr_matrix[i][j]), 4)
                for j in range(n)
            }
            for i in range(n)
        },
    }


def _interpret_sharpe(ratio: float) -> str:
    if ratio < 0:
        return "Negative — underperforming risk-free rate"
    if ratio < 1:
        return "Sub-optimal — low risk-adjusted return"
    if ratio < 2:
        return "Good — acceptable risk-adjusted return"
    if ratio < 3:
        return "Very good — strong risk-adjusted return"
    return "Excellent — outstanding risk-adjusted return"
