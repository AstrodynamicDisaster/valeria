"""
Helper functions for dealing with payroll line items.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable, List, Mapping, Optional, Sequence

from sqlalchemy.orm import Session

from core.models import PayrollLine

PayrollLinePayload = Mapping[str, object]


def _decimal_or_none(value: Optional[object]) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return None


def build_payroll_lines(
    session: Session,
    payroll_id: int,
    collections: Sequence[tuple[str, Iterable[PayrollLinePayload]]],
) -> List[PayrollLine]:
    """
    Expand the JSON arrays returned by the extractor into `PayrollLine` ORM instances.

    Args:
        session: SQLAlchemy session used to persist the lines.
        payroll_id: Identifier of the parent payroll.
        collections: Sequence of (category, iterable-of-items) tuples.

    Returns:
        The list of `PayrollLine` objects added to the session.
    """
    created: List[PayrollLine] = []

    for category, items in collections:
        for item in items:
            concepto = item.get("concepto") if isinstance(item, Mapping) else None
            importe = item.get("importe") if isinstance(item, Mapping) else None

            if concepto is None or importe is None:
                continue

            line = PayrollLine(
                payroll_id=payroll_id,
                category=category,
                concepto=str(concepto),
                importe=_decimal_or_none(importe) or Decimal("0.00"),
                base=_decimal_or_none(item.get("base")) if isinstance(item, Mapping) else None,
                tipo=_decimal_or_none(item.get("tipo")) if isinstance(item, Mapping) else None,
            )
            session.add(line)
            created.append(line)

    return created
