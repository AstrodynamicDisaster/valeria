"""
Utility functions for vida laboral CSV processing.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Tuple


def parse_spanish_name(raw_name: str) -> Tuple[str, str, Optional[str]]:
    """
    Split vida laboral name field into first name and surnames following the rules:

    - If the name contains ` --- ` the employee has only one surname. Text to the left
      becomes `last_name` and text to the right (any length) becomes `first_name`.
      `last_name2` is None.
    - Otherwise the employee has two surnames. The first word is `last_name`, the second
      word is `last_name2`, and everything after the second space belongs to `first_name`.
    """
    if not raw_name:
        return "Unknown", "Unknown", None

    nombre = raw_name.strip()
    if not nombre:
        return "Unknown", "Unknown", None

    if " --- " in nombre:
        last_name_part, first_name_part = nombre.split(" --- ", 1)
        last_name = last_name_part.strip() or "Unknown"
        first_name = first_name_part.strip() or "Unknown"
        last_name2 = None
    else:
        parts = nombre.split()
        if len(parts) >= 3:
            last_name = parts[0].strip() or "Unknown"
            last_name2 = parts[1].strip() or None
            first_name = " ".join(parts[2:]).strip() or "Unknown"
        elif len(parts) == 2:
            last_name = parts[0].strip() or "Unknown"
            last_name2 = None
            first_name = parts[1].strip() or "Unknown"
        else:
            last_name = parts[0].strip() or "Unknown"
            last_name2 = None
            first_name = "Unknown"

    return first_name, last_name, last_name2


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
