"""Financial report parser — extract key metrics from PDF reports (IFRS/GAAP)."""

import re
from pathlib import Path

from pypdf import PdfReader


def parse_financial_report(pdf_path: str) -> dict:
    """Parse a financial report PDF and extract key metrics.

    Extracts: revenue, net income, total assets, total liabilities, equity,
    EPS, and any detected accounting standard (IFRS/GAAP).
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Report not found: {pdf_path}")

    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    return {
        "file": path.name,
        "pages": len(reader.pages),
        "standard": _detect_standard(text),
        "metrics": _extract_metrics(text),
        "periods": _extract_periods(text),
    }


def extract_balance_sheet(pdf_path: str) -> dict:
    """Extract balance sheet items from a financial report PDF."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Report not found: {pdf_path}")

    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    return {
        "file": path.name,
        "assets": _extract_section(text, "assets"),
        "liabilities": _extract_section(text, "liabilities"),
        "equity": _extract_section(text, "equity"),
    }


def compare_reports(pdf_path_a: str, pdf_path_b: str) -> dict:
    """Compare key metrics between two financial report PDFs."""
    report_a = parse_financial_report(pdf_path_a)
    report_b = parse_financial_report(pdf_path_b)

    metrics_a = report_a["metrics"]
    metrics_b = report_b["metrics"]

    changes = {}
    all_keys = set(list(metrics_a.keys()) + list(metrics_b.keys()))
    for key in sorted(all_keys):
        val_a = metrics_a.get(key)
        val_b = metrics_b.get(key)
        change = None
        if val_a is not None and val_b is not None and val_a != 0:
            change = round(((val_b - val_a) / abs(val_a)) * 100, 2)
        changes[key] = {
            "report_a": val_a,
            "report_b": val_b,
            "change_percent": change,
        }

    return {
        "report_a": report_a["file"],
        "report_b": report_b["file"],
        "standard_a": report_a["standard"],
        "standard_b": report_b["standard"],
        "comparison": changes,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

_MONEY_RE = re.compile(
    r"[\$€£]?\s*([\d,]+(?:\.\d+)?)\s*(?:million|mln|m|billion|bln|b|thousand|k)?",
    re.IGNORECASE,
)

_METRIC_PATTERNS = {
    "revenue": re.compile(
        r"(?:total\s+)?(?:revenue|net\s+sales|turnover)\s*[:\s]*[\$€£]?\s*([\d,]+(?:\.\d+)?)",
        re.IGNORECASE,
    ),
    "net_income": re.compile(
        r"(?:net\s+(?:income|profit|earnings))\s*[:\s]*[\$€£]?\s*([\d,]+(?:\.\d+)?)",
        re.IGNORECASE,
    ),
    "total_assets": re.compile(
        r"total\s+assets\s*[:\s]*[\$€£]?\s*([\d,]+(?:\.\d+)?)",
        re.IGNORECASE,
    ),
    "total_liabilities": re.compile(
        r"total\s+liabilities\s*[:\s]*[\$€£]?\s*([\d,]+(?:\.\d+)?)",
        re.IGNORECASE,
    ),
    "equity": re.compile(
        r"(?:total\s+)?(?:shareholders?\'?\s+)?equity\s*[:\s]*[\$€£]?\s*([\d,]+(?:\.\d+)?)",
        re.IGNORECASE,
    ),
    "eps": re.compile(
        r"(?:earnings\s+per\s+share|eps)\s*[:\s]*[\$€£]?\s*([\d,]+(?:\.\d+)?)",
        re.IGNORECASE,
    ),
}


def _detect_standard(text: str) -> str | None:
    """Detect whether the report follows IFRS or GAAP."""
    upper = text.upper()
    has_ifrs = "IFRS" in upper or "INTERNATIONAL FINANCIAL REPORTING" in upper
    has_gaap = "GAAP" in upper or "GENERALLY ACCEPTED ACCOUNTING" in upper
    if has_ifrs and has_gaap:
        return "IFRS+GAAP"
    if has_ifrs:
        return "IFRS"
    if has_gaap:
        return "GAAP"
    return None


def _extract_metrics(text: str) -> dict:
    """Extract numeric financial metrics from text."""
    metrics = {}
    for name, pattern in _METRIC_PATTERNS.items():
        match = pattern.search(text)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                metrics[name] = float(raw)
            except ValueError:
                pass
    return metrics


def _extract_periods(text: str) -> list[str]:
    """Extract fiscal period references (e.g. 'FY2024', 'Q3 2025')."""
    pattern = re.compile(r"(?:FY|Q[1-4])\s*20\d{2}", re.IGNORECASE)
    return sorted(set(pattern.findall(text)))


def _extract_section(text: str, section: str) -> dict:
    """Extract line items from a balance sheet section."""
    items = {}
    pattern = re.compile(
        rf"({section}[\s\S]{{0,2000}}?)(?:total\s+{section})",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        return items

    block = match.group(1)
    line_pattern = re.compile(r"([A-Za-z][\w\s&,]+?)\s+([\d,]+(?:\.\d+)?)\s*$", re.MULTILINE)
    for line_match in line_pattern.finditer(block):
        label = line_match.group(1).strip()
        raw = line_match.group(2).replace(",", "")
        try:
            items[label] = float(raw)
        except ValueError:
            pass
    return items
