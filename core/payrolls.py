from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterable, Mapping, Optional, Union

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.agent.utils import format_periodo
from core.models import Employee, Payroll, PayrollLine


def _decimal(value: Any, default: Decimal = Decimal("0.00")) -> Decimal:
    """Best-effort decimal conversion with a simple fallback."""
    try:
        return default if value is None else Decimal(str(value))
    except Exception:
        return default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)):
        return bool(value)
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "t", "1", "yes", "y"}


def create_payroll(
    session: Session,
    employee_id: int,
    periodo: Mapping[str, Any],
    totals: Optional[Mapping[str, Any]] = None,
    payroll_lines: Optional[Iterable[Mapping[str, Any]]] = None,
    warnings: Union[str, Iterable[str], None] = None,
    payroll_type: Optional[str] = None,
) -> dict:
    """
    Minimal helper to persist a payroll plus its line items.

    Expected keys in `totals`:
      devengo_total, deduccion_total, aportacion_empresa_total,
      liquido_a_percibir, prorrata_pagas_extra, base_cc, base_at_ep,
      base_irpf, tipo_irpf

    Each line in `payroll_lines` must include: category, concept, amount.
    """
    totals = totals or {}
    payroll_lines = list(payroll_lines or [])

    def _normalize_payroll_type(value: Optional[str]) -> str:
        if value is None:
            return "payslip"
        normalized = str(value).strip().lower()
        if normalized in {"payslip", "settlement", "hybrid"}:
            return normalized
        return "payslip"

    try:
        employee = session.query(Employee).get(employee_id)
        if not employee:
            return {"success": False, "error": f"Employee {employee_id} not found"}

        if not isinstance(periodo, Mapping):
            return {"success": False, "error": "Periodo must be a mapping"}

        periodo_clean = {k: v for k, v in periodo.items() if v is not None}
        target_desde = periodo_clean.get("desde")
        target_hasta = periodo_clean.get("hasta")
        if target_desde or target_hasta:
            clash = (
                session.query(Payroll)
                .filter_by(employee_id=employee_id)
                .filter(Payroll.periodo["desde"].astext == target_desde)
                .filter(Payroll.periodo["hasta"].astext == target_hasta)
                .first()
            )
            if clash:
                period_label = format_periodo(periodo_clean)
                return {"success": False, "error": f"Payroll already exists for {period_label}"}

        warnings_text: Optional[str]
        if warnings is None:
            warnings_text = None
        elif isinstance(warnings, str):
            warnings_text = warnings
        else:
            warnings_text = "\n".join(str(w) for w in warnings)

        payroll = Payroll(
            employee_id=employee_id,
            type=_normalize_payroll_type(payroll_type),
            periodo=periodo_clean,
            type=type,
            devengo_total=_decimal(totals.get("devengo_total")),
            deduccion_total=_decimal(totals.get("deduccion_total")),
            aportacion_empresa_total=_decimal(totals.get("aportacion_empresa_total")),
            liquido_a_percibir=_decimal(totals.get("liquido_a_percibir")),
            prorrata_pagas_extra=_decimal(totals.get("prorrata_pagas_extra")),
            base_cc=_decimal(totals.get("base_cc")),
            base_at_ep=_decimal(totals.get("base_at_ep")),
            base_irpf=_decimal(totals.get("base_irpf")),
            tipo_irpf=_decimal(totals.get("tipo_irpf")),
            warnings=warnings_text,
        )
        session.add(payroll)
        session.flush()  # obtain payroll.id

        line_objects = []
        for item in payroll_lines:
            if not isinstance(item, Mapping):
                continue
            category = item.get("category")
            concept = item.get("concept") or item.get("concepto")
            amount = item.get("amount") or item.get("importe")
            if not category or concept is None or amount is None:
                continue

            line = PayrollLine(
                payroll_id=payroll.id,
                category=str(category),
                concept=str(concept),
                raw_concept=str(item.get("raw_concept") or concept),
                amount=_decimal(amount),
                is_taxable_income=_bool(item.get("is_taxable_income")),
                is_taxable_ss=_bool(item.get("is_taxable_ss")),
                is_sickpay=_bool(item.get("is_sickpay")),
                is_in_kind=_bool(item.get("is_in_kind")),
                is_pay_advance=_bool(item.get("is_pay_advance")),
                is_seizure=_bool(item.get("is_seizure")),
            )
            session.add(line)
            line_objects.append(line)

        session.commit()

        period_label = format_periodo(periodo_clean)
        return {
            "success": True,
            "data": payroll,
            "lines": len(line_objects),
            "message": f"Created payroll {payroll.id} for {period_label}",
        }

    except IntegrityError as exc:
        session.rollback()
        return {"success": False, "error": f"Integrity error: {exc}"}
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        return {"success": False, "error": str(exc)}
