"""Market data tools — stock quotes, history, and company info via yfinance."""

from datetime import datetime, timedelta

import yfinance as yf


def get_stock_quote(ticker: str) -> dict:
    """Get current stock quote: price, volume, change, market cap."""
    stock = yf.Ticker(ticker)
    info = stock.info

    price = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")

    change = None
    change_pct = None
    if price and prev_close:
        change = round(price - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2)

    return {
        "ticker": ticker.upper(),
        "price": price,
        "currency": info.get("currency", "USD"),
        "change": change,
        "change_percent": change_pct,
        "volume": info.get("volume"),
        "market_cap": info.get("marketCap"),
        "exchange": info.get("exchange"),
        "timestamp": datetime.now().isoformat(),
    }


def get_stock_history(ticker: str, period: str = "1mo", interval: str = "1d") -> dict:
    """Get historical price data.

    Args:
        ticker: Stock ticker symbol.
        period: Data period — 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max.
        interval: Data interval — 1m, 5m, 15m, 1h, 1d, 1wk, 1mo.
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)

    if df.empty:
        return {"ticker": ticker.upper(), "error": "No data found", "records": []}

    records = []
    for date, row in df.iterrows():
        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(row["Open"], 2),
            "high": round(row["High"], 2),
            "low": round(row["Low"], 2),
            "close": round(row["Close"], 2),
            "volume": int(row["Volume"]),
        })

    return {
        "ticker": ticker.upper(),
        "period": period,
        "interval": interval,
        "count": len(records),
        "records": records,
    }


def get_company_info(ticker: str) -> dict:
    """Get company profile: sector, industry, description, financials summary."""
    stock = yf.Ticker(ticker)
    info = stock.info

    return {
        "ticker": ticker.upper(),
        "name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "website": info.get("website"),
        "employees": info.get("fullTimeEmployees"),
        "description": info.get("longBusinessSummary"),
        "financials": {
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "eps": info.get("trailingEps"),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
        },
    }
