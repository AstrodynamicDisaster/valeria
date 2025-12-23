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


def _bool_or_default(value: Optional[object], default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)):
        return bool(value)
    raw = str(value).strip().lower()
    if raw in {"true", "t", "1", "yes", "y"}:
        return True
    if raw in {"false", "f", "0", "no", "n"}:
        return False
    return default


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
            if isinstance(item, Mapping):
                concept = item.get("concept")
                if concept is None:
                    concept = item.get("concepto")
                amount = item.get("amount")
                if amount is None:
                    amount = item.get("importe")
            else:
                concept = None
                amount = None

            if concept is None or amount is None:
                continue

            is_taxable_income = _bool_or_default(item.get("is_taxable_income") if isinstance(item, Mapping) else None)
            if not is_taxable_income and isinstance(item, Mapping):
                if item.get("ind_tributa_IRPF") is not None:
                    is_taxable_income = _bool_or_default(item.get("ind_tributa_IRPF"))
                elif item.get("tributa_irpf") is not None:
                    is_taxable_income = _bool_or_default(item.get("tributa_irpf"))

            is_taxable_ss = _bool_or_default(item.get("is_taxable_ss") if isinstance(item, Mapping) else None)
            if not is_taxable_ss and isinstance(item, Mapping):
                if item.get("ind_cotiza_ss") is not None:
                    is_taxable_ss = _bool_or_default(item.get("ind_cotiza_ss"))
                elif item.get("cotiza_ss") is not None:
                    is_taxable_ss = _bool_or_default(item.get("cotiza_ss"))

            is_sickpay = _bool_or_default(item.get("is_sickpay") if isinstance(item, Mapping) else None)
            is_in_kind = _bool_or_default(item.get("is_in_kind") if isinstance(item, Mapping) else None)
            if not is_in_kind and isinstance(item, Mapping) and item.get("en_especie") is not None:
                is_in_kind = _bool_or_default(item.get("en_especie"))
            is_pay_advance = _bool_or_default(item.get("is_pay_advance") if isinstance(item, Mapping) else None)
            is_seizure = _bool_or_default(item.get("is_seizure") if isinstance(item, Mapping) else None)

            line = PayrollLine(
                payroll_id=payroll_id,
                category=category,
                concept=str(concept),
                raw_concept=str(item.get("raw_concept") or item.get("concepto_raw") or concept),
                amount=_decimal_or_none(amount) or Decimal("0.00"),
                is_taxable_income=is_taxable_income,
                is_taxable_ss=is_taxable_ss,
                is_sickpay=is_sickpay,
                is_in_kind=is_in_kind,
                is_pay_advance=is_pay_advance,
                is_seizure=is_seizure,
            )
            session.add(line)
            created.append(line)

    return created
