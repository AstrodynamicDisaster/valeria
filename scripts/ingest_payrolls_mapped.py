#!/usr/bin/env python3
"""
Ingest payrolls from payrolls_mapped.json into the local database.

Usage:
    python scripts/ingest_payrolls_mapped.py payrolls_mapped.json
    python scripts/ingest_payrolls_mapped.py payrolls_mapped.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy.exc import IntegrityError

# Add repo root to path to import core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import create_database_engine, get_session
from core.models import Employee, Payroll, PayrollLine


PAYROLL_REQUIRED_FIELDS = [
    "type",
    "empresa",
    "trabajador",
    "periodo",
    "devengo_total",
    "deduccion_total",
    "aportacion_empresa_total",
    "liquido_a_percibir",
    "prorrata_pagas_extra",
    "base_cc",
    "base_at_ep",
    "base_irpf",
    "tipo_irpf",
    "payroll_lines",
]

LINE_REQUIRED_FIELDS = [
    "category",
    "concept",
    "amount",
    "is_taxable_income",
    "is_taxable_ss",
    "is_sickpay",
    "is_in_kind",
    "is_pay_advance",
    "is_seizure",
]

ALLOWED_PAYROLL_TYPES = {"payslip", "settlement", "hybrid"}
ALLOWED_LINE_CATEGORIES = {"devengo", "deduccion", "aportacion_empresa"}


def _as_decimal(value: Any) -> Decimal:
    try:
        if value is None:
            return Decimal("0")
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Invalid numeric value: {value!r}")


def _parse_full_name(full_name: str) -> Tuple[str, str, Optional[str]]:
    parts = [p for p in str(full_name).strip().split() if p]
    if not parts:
        return ("Unknown", "Unknown", None)
    if len(parts) == 1:
        return (parts[0], "Unknown", None)
    if len(parts) == 2:
        return (parts[1], parts[0], None)
    # Assume Spanish ordering: last_name last_name2 first_names...
    last_name = parts[0]
    last_name2 = parts[1]
    first_name = " ".join(parts[2:])
    return (first_name, last_name, last_name2)


def _normalize_warnings(warnings: Any) -> Optional[str]:
    if warnings is None:
        return None
    if isinstance(warnings, str):
        return warnings
    try:
        return json.dumps(warnings, ensure_ascii=False)
    except Exception:
        if isinstance(warnings, Iterable):
            return "\n".join(str(w) for w in warnings)
        return str(warnings)


def _validate_structure(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    payrolls = payload.get("payrolls")
    if not isinstance(payrolls, list):
        return ["Top-level key 'payrolls' must be a list."]

    for idx, payroll in enumerate(payrolls):
        if not isinstance(payroll, dict):
            errors.append(f"[{idx}] payroll is not an object")
            continue

        missing = [k for k in PAYROLL_REQUIRED_FIELDS if k not in payroll]
        if missing:
            errors.append(f"[{idx}] missing payroll fields: {', '.join(missing)}")
            continue

        if payroll.get("type") not in ALLOWED_PAYROLL_TYPES:
            errors.append(f"[{idx}] invalid payroll type: {payroll.get('type')!r}")

        if not isinstance(payroll.get("periodo"), dict):
            errors.append(f"[{idx}] periodo must be an object")

        trabajador = payroll.get("trabajador")
        if not isinstance(trabajador, dict):
            errors.append(f"[{idx}] trabajador must be an object")
        else:
            if not trabajador.get("dni"):
                errors.append(f"[{idx}] trabajador.dni is required to match/create employee")
            if not trabajador.get("nombre"):
                errors.append(f"[{idx}] trabajador.nombre is required to create employee")

        for field in (
            "devengo_total",
            "deduccion_total",
            "aportacion_empresa_total",
            "liquido_a_percibir",
            "prorrata_pagas_extra",
            "base_cc",
            "base_at_ep",
            "base_irpf",
            "tipo_irpf",
        ):
            try:
                _as_decimal(payroll.get(field))
            except ValueError as exc:
                errors.append(f"[{idx}] {field}: {exc}")

        lines = payroll.get("payroll_lines")
        if not isinstance(lines, list):
            errors.append(f"[{idx}] payroll_lines must be a list")
            continue

        for line_idx, line in enumerate(lines):
            if not isinstance(line, dict):
                errors.append(f"[{idx}][line {line_idx}] line is not an object")
                continue

            line_missing = [k for k in LINE_REQUIRED_FIELDS if k not in line]
            if line_missing:
                errors.append(
                    f"[{idx}][line {line_idx}] missing line fields: {', '.join(line_missing)}"
                )
                continue

            if line.get("category") not in ALLOWED_LINE_CATEGORIES:
                errors.append(
                    f"[{idx}][line {line_idx}] invalid category: {line.get('category')!r}"
                )
            try:
                _as_decimal(line.get("amount"))
            except ValueError as exc:
                errors.append(f"[{idx}][line {line_idx}] amount: {exc}")

            for bool_field in (
                "is_taxable_income",
                "is_taxable_ss",
                "is_sickpay",
                "is_in_kind",
                "is_pay_advance",
                "is_seizure",
            ):
                if not isinstance(line.get(bool_field), bool):
                    errors.append(
                        f"[{idx}][line {line_idx}] {bool_field} must be boolean"
                    )

    return errors


def _find_or_create_employee(session, trabajador: Dict[str, Any]) -> Employee:
    dni = str(trabajador.get("dni")).strip()
    employee = session.query(Employee).filter_by(identity_card_number=dni).first()
    if employee:
        return employee

    first_name, last_name, last_name2 = _parse_full_name(trabajador.get("nombre", ""))
    employee = Employee(
        first_name=first_name,
        last_name=last_name,
        last_name2=last_name2,
        identity_card_number=dni,
        ss_number=trabajador.get("ss_number"),
    )
    session.add(employee)
    session.flush()
    return employee


def _payroll_exists(session, employee_id: int, periodo: Dict[str, Any], liquido: Decimal) -> bool:
    desde = (periodo or {}).get("desde")
    hasta = (periodo or {}).get("hasta")
    if not (desde and hasta):
        return False
    return (
        session.query(Payroll)
        .filter(Payroll.employee_id == employee_id)
        .filter(Payroll.periodo["desde"].astext == str(desde))
        .filter(Payroll.periodo["hasta"].astext == str(hasta))
        .filter(Payroll.liquido_a_percibir == liquido)
        .first()
        is not None
    )


def _ingest_payrolls(
    session,
    payrolls: List[Dict[str, Any]],
    dry_run: bool = False,
    batch_size: int = 200,
) -> Tuple[int, int, int]:
    created = 0
    skipped = 0
    lines_created = 0

    for idx, payroll in enumerate(payrolls, start=1):
        trabajador = payroll["trabajador"]
        employee = _find_or_create_employee(session, trabajador)

        periodo = payroll.get("periodo") or {}
        liquido = _as_decimal(payroll.get("liquido_a_percibir"))
        if _payroll_exists(session, employee.id, periodo, liquido):
            skipped += 1
            continue

        warnings_text = _normalize_warnings(payroll.get("warnings"))

        payroll_row = Payroll(
            employee_id=employee.id,
            type=payroll.get("type"),
            periodo=periodo,
            devengo_total=_as_decimal(payroll.get("devengo_total")),
            deduccion_total=_as_decimal(payroll.get("deduccion_total")),
            aportacion_empresa_total=_as_decimal(payroll.get("aportacion_empresa_total")),
            liquido_a_percibir=liquido,
            prorrata_pagas_extra=_as_decimal(payroll.get("prorrata_pagas_extra")),
            base_cc=_as_decimal(payroll.get("base_cc")),
            base_at_ep=_as_decimal(payroll.get("base_at_ep")),
            base_irpf=_as_decimal(payroll.get("base_irpf")),
            tipo_irpf=_as_decimal(payroll.get("tipo_irpf")),
            warnings=warnings_text,
        )
        session.add(payroll_row)
        session.flush()

        for line in payroll.get("payroll_lines", []):
            payroll_line = PayrollLine(
                payroll_id=payroll_row.id,
                category=line.get("category"),
                concept=line.get("concept"),
                raw_concept=line.get("raw_concept"),
                amount=_as_decimal(line.get("amount")),
                is_taxable_income=line.get("is_taxable_income"),
                is_taxable_ss=line.get("is_taxable_ss"),
                is_sickpay=line.get("is_sickpay"),
                is_in_kind=line.get("is_in_kind"),
                is_pay_advance=line.get("is_pay_advance"),
                is_seizure=line.get("is_seizure"),
            )
            session.add(payroll_line)
            lines_created += 1

        created += 1

        if not dry_run and idx % batch_size == 0:
            session.commit()

    if not dry_run:
        session.commit()
    else:
        session.rollback()

    return created, skipped, lines_created


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest payrolls_mapped.json into the DB.")
    parser.add_argument("input", help="Path to payrolls_mapped.json")
    parser.add_argument("--dry-run", action="store_true", help="Validate and simulate ingest only")
    parser.add_argument(
        "--db-url",
        default=None,
        help="Database URL (defaults to POSTGRES_* env vars)",
    )
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        payload = json.load(f)

    errors = _validate_structure(payload)
    if errors:
        print("Structure validation failed:")
        for err in errors[:50]:
            print(f" - {err}")
        if len(errors) > 50:
            print(f" ... and {len(errors) - 50} more")
        return 1

    engine = create_database_engine(database_url=args.db_url, echo=False)
    session = get_session(engine)

    try:
        created, skipped, lines_created = _ingest_payrolls(
            session,
            payload["payrolls"],
            dry_run=args.dry_run,
        )
    except IntegrityError as exc:
        session.rollback()
        print(f"Database integrity error: {exc}")
        return 2
    except Exception as exc:
        session.rollback()
        print(f"Error ingesting payrolls: {exc}")
        return 3
    finally:
        session.close()

    mode = "Dry run" if args.dry_run else "Ingest"
    print(f"{mode} complete: payrolls created={created}, skipped={skipped}, lines created={lines_created}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
