from __future__ import annotations

import re
from typing import Any, Optional


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_ssn(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    normalized = _WHITESPACE_RE.sub("", text)
    return normalized or None
