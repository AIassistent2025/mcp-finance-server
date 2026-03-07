"""MCP Finance Server — registers all financial tools via FastMCP."""

from mcp.server.fastmcp import FastMCP

from src.market_data import get_stock_quote, get_stock_history, get_company_info
from src.report_parser import parse_financial_report, extract_balance_sheet, compare_reports
from src.risk_metrics import calculate_var, calculate_sharpe_ratio, calculate_portfolio_risk

mcp = FastMCP(
    "finance-server",
    instructions="MCP server for financial data — market quotes, report parsing, risk metrics.",
)


# ── Market Data ───────────────────────────────────────────────────────────────

@mcp.tool()
def stock_quote(ticker: str) -> dict:
    """Get current stock quote with price, volume, change, and market cap.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, TSLA).
    """
    return get_stock_quote(ticker)


@mcp.tool()
def stock_history(ticker: str, period: str = "1mo", interval: str = "1d") -> dict:
    """Get historical stock price data (OHLCV).

    Args:
        ticker: Stock ticker symbol.
        period: Data period — 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max.
        interval: Data interval — 1m, 5m, 15m, 1h, 1d, 1wk, 1mo.
    """
    return get_stock_history(ticker, period, interval)


@mcp.tool()
def company_info(ticker: str) -> dict:
    """Get company profile — sector, industry, description, and key financial ratios.

    Args:
        ticker: Stock ticker symbol.
    """
    return get_company_info(ticker)


# ── Report Parser ─────────────────────────────────────────────────────────────

@mcp.tool()
def parse_report(pdf_path: str) -> dict:
    """Parse a financial report PDF and extract key metrics (revenue, net income, EPS, etc.).

    Detects IFRS or GAAP standard automatically.

    Args:
        pdf_path: Absolute path to the PDF file.
    """
    return parse_financial_report(pdf_path)


@mcp.tool()
def balance_sheet(pdf_path: str) -> dict:
    """Extract balance sheet data (assets, liabilities, equity) from a financial report PDF.

    Args:
        pdf_path: Absolute path to the PDF file.
    """
    return extract_balance_sheet(pdf_path)


@mcp.tool()
def compare_financial_reports(pdf_path_a: str, pdf_path_b: str) -> dict:
    """Compare key financial metrics between two report PDFs and show changes.

    Args:
        pdf_path_a: Path to the first (earlier) report PDF.
        pdf_path_b: Path to the second (later) report PDF.
    """
    return compare_reports(pdf_path_a, pdf_path_b)


# ── Risk Metrics ──────────────────────────────────────────────────────────────

@mcp.tool()
def value_at_risk(
    ticker: str,
    period: str = "1y",
    confidence: float = 0.95,
    investment: float = 10000.0,
) -> dict:
    """Calculate Value at Risk (VaR) — both parametric and historical.

    Shows the maximum expected loss at a given confidence level.

    Args:
        ticker: Stock ticker symbol.
        period: Historical period for returns (1mo, 3mo, 6mo, 1y, 2y).
        confidence: Confidence level (0.90, 0.95, 0.99).
        investment: Portfolio value in USD.
    """
    return calculate_var(ticker, period, confidence, investment)


@mcp.tool()
def sharpe_ratio(
    ticker: str,
    period: str = "1y",
    risk_free_rate: float = 0.05,
) -> dict:
    """Calculate the Sharpe ratio — measures risk-adjusted return.

    Args:
        ticker: Stock ticker symbol.
        period: Historical period (1mo, 3mo, 6mo, 1y, 2y, 5y).
        risk_free_rate: Annual risk-free rate (default 5%).
    """
    return calculate_sharpe_ratio(ticker, period, risk_free_rate)


@mcp.tool()
def portfolio_risk(
    tickers: list[str],
    weights: list[float] | None = None,
    period: str = "1y",
) -> dict:
    """Calculate portfolio risk — volatility, returns, and correlation matrix.

    Args:
        tickers: List of stock ticker symbols (e.g. ["AAPL", "MSFT", "GOOGL"]).
        weights: Portfolio weights (must sum to 1). Equal weights if omitted.
        period: Historical period for returns (1mo, 3mo, 6mo, 1y, 2y).
    """
    return calculate_portfolio_risk(tickers, weights, period)
