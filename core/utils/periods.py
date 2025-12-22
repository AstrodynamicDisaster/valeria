"""
Period-related utility functions for handling payroll periods.

These functions are shared across the codebase for parsing and manipulating
period dictionaries from payroll data.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Optional, Tuple


def parse_date(value: Optional[str]) -> Optional[date]:
    """Parse common Spanish date formats."""
    if not value:
        return None

    value = value.strip()
    if not value:
        return None

    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def extract_period_dates(periodo: Optional[Dict[str, str]]) -> Tuple[Optional[date], Optional[date]]:
    """Return start and end dates parsed from a periodo dict."""
    if not periodo or not isinstance(periodo, dict):
        return None, None

    start = parse_date(periodo.get("desde"))
    end = parse_date(periodo.get("hasta"))
    return start, end


def period_reference_date(periodo: Optional[Dict[str, str]]) -> Optional[date]:
    """Pick the most relevant date from periodo for comparisons (prefer end, fallback to start)."""
    start, end = extract_period_dates(periodo)
    return end or start


def format_periodo(periodo: Optional[Dict[str, str]]) -> str:
    """Return a human-readable representation of periodo."""
    if not periodo or not isinstance(periodo, dict):
        return "periodo-desconocido"

    start = periodo.get("desde")
    end = periodo.get("hasta")

    if start and end:
        return f"{start} → {end}"
    return start or end or "periodo-desconocido"
