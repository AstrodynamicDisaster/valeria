from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Dict, List, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.agent.utils import format_periodo
from core.models import Employee, Payroll, PayrollLine


def _decimal_or_default(value: Any, default: Decimal = Decimal("0.00")) -> Decimal:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return default


def _bool_or_default(value: Any, default: bool = False) -> bool:
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


def create_payroll_record(
    session: Session,
    employee_id: int,
    periodo: Dict[str, Any],
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Insert a payroll (and optional lines) into the database using the simplified schema.

    Returns a dict matching the previous agent-facing contract:
      {"success": bool, "data": Payroll | None, "message": str, "error": Optional[str]}
    """
    try:
        employee = session.query(Employee).filter_by(id=employee_id).first()
        if not employee:
            return {
                "success": False,
                "error": "Employee not found",
                "message": f"Employee with ID {employee_id} not found",
            }

        if not isinstance(periodo, dict):
            return {
                "success": False,
                "error": "Invalid periodo",
                "message": "Periodo must be an object with 'desde' and 'hasta' fields",
            }

        periodo_payload = {k: v for k, v in periodo.items() if v is not None}

        target_desde = periodo_payload.get("desde")
        target_hasta = periodo_payload.get("hasta")
        if target_desde or target_hasta:
            existing = session.query(Payroll).filter_by(employee_id=employee_id).all()
            for row in existing:
                existing_periodo = row.periodo or {}
                if (
                    existing_periodo.get("desde") == target_desde
                    and existing_periodo.get("hasta") == target_hasta
                ):
                    period_str = format_periodo(periodo_payload)
                    return {
                        "success": False,
                        "error": "Payroll already exists for this period",
                        "message": f"Payroll already exists for {period_str}",
                    }

        warnings_arg = kwargs.get("warnings")
        if isinstance(warnings_arg, List):
            warnings_text = json.dumps(warnings_arg, ensure_ascii=False)
        elif isinstance(warnings_arg, str):
            warnings_text = warnings_arg
        else:
            warnings_text = None

        payroll = Payroll(
            employee_id=employee_id,
            periodo=periodo_payload,
            devengo_total=kwargs.get("devengo_total"),
            deduccion_total=kwargs.get("deduccion_total"),
            aportacion_empresa_total=kwargs.get("aportacion_empresa_total"),
            liquido_a_percibir=kwargs.get("liquido_a_percibir"),
            prorrata_pagas_extra=_decimal_or_default(kwargs.get("prorrata_pagas_extra")),
            base_cc=_decimal_or_default(kwargs.get("base_cc")),
            base_at_ep=_decimal_or_default(kwargs.get("base_at_ep")),
            base_irpf=_decimal_or_default(kwargs.get("base_irpf")),
            tipo_irpf=_decimal_or_default(kwargs.get("tipo_irpf")),
            warnings=warnings_text,
        )

        session.add(payroll)
        session.flush()  # obtain payroll.id

        line_collections: List[Tuple[str, List[Dict[str, Any]]]] = [
            ("devengo", kwargs.get("devengo_items") or []),
            ("deduccion", kwargs.get("deduccion_items") or []),
            ("aportacion_empresa", kwargs.get("aportacion_empresa_items") or []),
        ]

        line_count = 0
        for category, items in line_collections:
            for item in items:
                if not isinstance(item, dict):
                    continue
                concept = item.get("concept") or item.get("concepto")
                amount = item.get("amount") or item.get("importe")
                if concept is None or amount is None:
                    continue

                payroll_line = PayrollLine(
                    payroll_id=payroll.id,
                    category=category,
                    concept=str(concept),
                    amount=Decimal(str(amount)),
                    is_taxable_income=_bool_or_default(
                        item.get("is_taxable_income") or item.get("tributa_irpf")
                    ),
                    is_taxable_ss=_bool_or_default(
                        item.get("is_taxable_ss") or item.get("cotiza_ss")
                    ),
                    is_sickpay=_bool_or_default(item.get("is_sickpay")),
                    is_in_kind=_bool_or_default(
                        item.get("is_in_kind") or item.get("en_especie")
                    ),
                    is_pay_advance=_bool_or_default(item.get("is_pay_advance")),
                    is_seizure=_bool_or_default(item.get("is_seizure")),
                )
                session.add(payroll_line)
                line_count += 1

        session.commit()

        full_name = f"{employee.first_name} {employee.last_name}"
        if employee.last_name2:
            full_name += f" {employee.last_name2}"
        period_label = format_periodo(periodo_payload)

        return {
            "success": True,
            "data": payroll,
            "message": f"Successfully created payroll for '{full_name}' - {period_label} (ID: {payroll.id}, {line_count} line(s))",
        }

    except IntegrityError as exc:
        session.rollback()
        return {
            "success": False,
            "error": f"Database integrity error: {exc}",
            "message": f"Failed to create payroll: {exc}",
        }
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        return {
            "success": False,
            "error": str(exc),
            "message": f"Failed to create payroll: {exc}",
        }
