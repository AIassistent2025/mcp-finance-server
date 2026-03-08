# MCP Finance Server

A [Model Context Protocol](https://modelcontextprotocol.io/) server that gives AI assistants (Claude, ChatGPT, etc.) access to **real-time financial data, report analysis, and risk metrics**.

Built with the official MCP Python SDK, yfinance, and NumPy.

---

## Tools

### Market Data
| Tool | Description |
|---|---|
| `stock_quote` | Current price, volume, change, market cap |
| `stock_history` | Historical OHLCV data (any period/interval) |
| `company_info` | Company profile, sector, PE ratio, beta, 52-week range |

### Report Parsing
| Tool | Description |
|---|---|
| `parse_report` | Extract key metrics from a financial PDF (auto-detects IFRS/GAAP) |
| `balance_sheet` | Extract assets, liabilities, and equity from a PDF |
| `compare_financial_reports` | Compare two report PDFs and show metric changes |

### Risk Metrics
| Tool | Description |
|---|---|
| `value_at_risk` | Parametric and historical VaR at any confidence level |
| `sharpe_ratio` | Risk-adjusted return with interpretation |
| `portfolio_risk` | Multi-asset portfolio volatility and correlation matrix |

---

## Setup

**1. Clone the repository**
```bash
git clone https://github.com/AIassistent2025/mcp-finance-server.git
cd mcp-finance-server
```

**2. Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

---

## Usage

### Run the server

```bash
python main.py
```

The server communicates over **stdio** by default (standard MCP transport).

### Connect to Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "finance": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-finance-server/main.py"]
    }
  }
}
```

Then ask Claude:
- *"What's the current price of AAPL?"*
- *"Calculate the Sharpe ratio for TSLA over the last 2 years"*
- *"What's the Value at Risk for a $50,000 investment in NVDA at 99% confidence?"*
- *"Analyze the risk of a portfolio: 40% AAPL, 30% MSFT, 30% GOOGL"*
- *"Parse this financial report and extract the key metrics"*

### Connect to any MCP client

The server works with any MCP-compatible client. Use the stdio transport:

```bash
python main.py
```

Or integrate programmatically:

```python
from src.server import mcp
mcp.run()
```

---

## Project Structure

```
mcp-finance-server/
├── src/
│   ├── __init__.py
│   ├── server.py          # MCP server — tool registration via FastMCP
│   ├── market_data.py     # Stock quotes, history, company info (yfinance)
│   ├── report_parser.py   # PDF parsing for IFRS/GAAP financial reports
│   └── risk_metrics.py    # VaR, Sharpe ratio, portfolio risk (NumPy)
├── tests/
│   ├── __init__.py
│   └── test_core.py       # 20 unit tests with mocked external calls
├── main.py                # Entry point
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Running Tests

```bash
pytest tests/ -v
```

All external API calls (yfinance) are mocked — tests run offline and fast.

---

## Why MCP for Finance?

Traditional AI interactions often suffer from "context drift" and "hallucinations" when dealing with precise financial data. The **Model Context Protocol (MCP)** solves this by:
*   **Decoupling Logic from Reasoning:** The AI reasons about the strategy, while the MCP server provides the ground-truth data.
*   **Standardized Interfaces:** Any LLM (Claude, ChatGPT, etc.) can use these tools without custom prompt engineering for every API.
*   **Security & Privacy:** Financial data stays within your local or trusted environment, only the necessary context is shared with the model.

---

## Features Deep Dive

### 📊 Real-Time Market Intelligence
Powered by `yfinance`, our tools provide more than just price. We pull volume dynamics, sector classification, and key valuation ratios (P/E, Beta) to give the AI a 360-degree view of the ticker.

### 📄 IFRS/GAAP Document Ingestion
The `parse_report` tool doesn't just read text; it uses heuristic-driven logic to identify standard financial tables. It can distinguish between "Total Assets" and "Net Assets" across different reporting standards, ensuring the AI performs accurate longitudinal analysis.

### 📉 Quantitative Risk Modeling
We’ve implemented institutional-grade risk metrics:
*   **Value at Risk (VaR):** Uses historical simulation to estimate potential portfolio drawdown.
*   **Sharpe Ratio:** Automatically fetches risk-free rates to provide a realistic view of risk-adjusted performance.

---

## Troubleshooting

*   **API Rate Limits:** `yfinance` is free but can be throttled. If you encounter errors, wait 60 seconds or use a VPN/Proxy.
*   **PDF Parsing Issues:** Ensure the PDF is a text-based report (not a scanned image). For scanned PDFs, use an OCR pre-processor.
*   **Path Errors:** Always use **absolute paths** when providing `pdf_path` to the tools.

---

## Contributing

Contributions are welcome! Whether it's adding new risk metrics, supporting more broker APIs, or improving PDF parsing logic, feel free to open a PR.

---

## License

MIT
