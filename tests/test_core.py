import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.market_data import get_stock_quote, get_stock_history, get_company_info
from src.report_parser import (
    parse_financial_report,
    extract_balance_sheet,
    compare_reports,
    _detect_standard,
    _extract_metrics,
    _extract_periods,
)
from src.risk_metrics import calculate_var, calculate_sharpe_ratio, _interpret_sharpe


# ── Market Data ───────────────────────────────────────────────────────────────

class TestMarketData:

    @patch("src.market_data.yf.Ticker")
    def test_get_stock_quote_returns_price(self, mock_ticker_cls):
        mock_ticker_cls.return_value.info = {
            "currentPrice": 150.25,
            "previousClose": 148.00,
            "volume": 5_000_000,
            "marketCap": 2_400_000_000_000,
            "currency": "USD",
            "exchange": "NMS",
        }
        result = get_stock_quote("AAPL")
        assert result["ticker"] == "AAPL"
        assert result["price"] == 150.25
        assert result["change"] == 2.25
        assert result["change_percent"] is not None

    @patch("src.market_data.yf.Ticker")
    def test_get_stock_quote_handles_missing_price(self, mock_ticker_cls):
        mock_ticker_cls.return_value.info = {
            "regularMarketPrice": 42.0,
            "regularMarketPreviousClose": 41.0,
        }
        result = get_stock_quote("XYZ")
        assert result["price"] == 42.0

    @patch("src.market_data.yf.Ticker")
    def test_get_stock_history_returns_records(self, mock_ticker_cls):
        import pandas as pd
        dates = pd.date_range("2025-01-01", periods=3)
        df = pd.DataFrame({
            "Open": [100, 101, 102],
            "High": [105, 106, 107],
            "Low": [99, 100, 101],
            "Close": [104, 105, 106],
            "Volume": [1000, 2000, 3000],
        }, index=dates)
        mock_ticker_cls.return_value.history.return_value = df

        result = get_stock_history("AAPL", period="5d")
        assert result["count"] == 3
        assert result["records"][0]["close"] == 104.0

    @patch("src.market_data.yf.Ticker")
    def test_get_stock_history_empty(self, mock_ticker_cls):
        import pandas as pd
        mock_ticker_cls.return_value.history.return_value = pd.DataFrame()
        result = get_stock_history("FAKE")
        assert result["error"] == "No data found"

    @patch("src.market_data.yf.Ticker")
    def test_get_company_info_returns_profile(self, mock_ticker_cls):
        mock_ticker_cls.return_value.info = {
            "longName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "country": "United States",
            "marketCap": 2_400_000_000_000,
            "trailingPE": 28.5,
        }
        result = get_company_info("AAPL")
        assert result["name"] == "Apple Inc."
        assert result["sector"] == "Technology"
        assert result["financials"]["pe_ratio"] == 28.5


# ── Report Parser ─────────────────────────────────────────────────────────────

class TestReportParser:

    def test_detect_standard_ifrs(self):
        assert _detect_standard("Prepared in accordance with IFRS standards") == "IFRS"

    def test_detect_standard_gaap(self):
        assert _detect_standard("Under US GAAP principles") == "GAAP"

    def test_detect_standard_both(self):
        assert _detect_standard("Reconciliation from IFRS to US GAAP") == "IFRS+GAAP"

    def test_detect_standard_none(self):
        assert _detect_standard("This is just regular text") is None

    def test_extract_metrics_revenue(self):
        text = "Total Revenue: $1,234,567.89\nNet Income: $456,789"
        metrics = _extract_metrics(text)
        assert metrics["revenue"] == 1234567.89
        assert metrics["net_income"] == 456789.0

    def test_extract_metrics_eps(self):
        text = "Earnings per share: $3.45"
        metrics = _extract_metrics(text)
        assert metrics["eps"] == 3.45

    def test_extract_periods(self):
        text = "Results for FY2024 compared to Q3 2025 and FY2024"
        periods = _extract_periods(text)
        assert "FY2024" in periods
        assert "Q3 2025" in periods

    def test_parse_report_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_financial_report("/nonexistent/report.pdf")

    def test_extract_balance_sheet_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            extract_balance_sheet("/nonexistent/report.pdf")


# ── Risk Metrics ──────────────────────────────────────────────────────────────

class TestRiskMetrics:

    @patch("src.risk_metrics.yf.Ticker")
    def test_calculate_var_returns_metrics(self, mock_ticker_cls):
        import pandas as pd
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        df = pd.DataFrame({"Close": prices}, index=pd.date_range("2024-01-01", periods=100))
        mock_ticker_cls.return_value.history.return_value = df

        result = calculate_var("AAPL", period="1y", confidence=0.95, investment=10000)
        assert result["ticker"] == "AAPL"
        assert "parametric_var" in result
        assert "historical_var" in result
        assert result["parametric_var"]["usd"] > 0

    @patch("src.risk_metrics.yf.Ticker")
    def test_calculate_var_insufficient_data(self, mock_ticker_cls):
        import pandas as pd
        mock_ticker_cls.return_value.history.return_value = pd.DataFrame({"Close": [100, 101]})
        result = calculate_var("FAKE")
        assert result["error"] == "Insufficient data"

    @patch("src.risk_metrics.yf.Ticker")
    def test_calculate_sharpe_returns_ratio(self, mock_ticker_cls):
        import pandas as pd
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(200) * 0.3)
        df = pd.DataFrame({"Close": prices}, index=pd.date_range("2024-01-01", periods=200))
        mock_ticker_cls.return_value.history.return_value = df

        result = calculate_sharpe_ratio("AAPL", period="1y")
        assert result["ticker"] == "AAPL"
        assert "sharpe_ratio" in result
        assert "interpretation" in result

    def test_interpret_sharpe(self):
        assert "Negative" in _interpret_sharpe(-0.5)
        assert "Sub-optimal" in _interpret_sharpe(0.5)
        assert "Good" in _interpret_sharpe(1.5)
        assert "Very good" in _interpret_sharpe(2.5)
        assert "Excellent" in _interpret_sharpe(3.5)
