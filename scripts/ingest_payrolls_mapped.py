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
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy.exc import IntegrityError

# Add repo root to path to import core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import create_database_engine, get_session
from core.normalization import normalize_ssn
from core.models import Client, ClientLocation, Employee, EmployeePeriod, Payroll, PayrollLine


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


def _normalize_id(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _resolve_client(session, empresa: Dict[str, Any]) -> Optional[Client]:
    if not isinstance(empresa, dict):
        return None
    cif = (empresa.get("cif") or "").strip()
    name = (empresa.get("razon_social") or "").strip()
    if cif:
        client = session.query(Client).filter_by(cif=cif).first()
        if client:
            return client
    if name:
        return session.query(Client).filter_by(name=name).first()
    return None


def _has_valid_employee_period(
    session,
    employee_id: int,
    periodo: Dict[str, Any],
    client_id,
) -> bool:
    desde = _parse_date((periodo or {}).get("desde"))
    hasta = _parse_date((periodo or {}).get("hasta"))
    if hasta is None:
        return False
    period_start = desde or hasta
    period_end = hasta

    return (
        session.query(EmployeePeriod.id)
        .join(ClientLocation, ClientLocation.id == EmployeePeriod.location_id)
        .filter(
            EmployeePeriod.employee_id == employee_id,
            ClientLocation.company_id == client_id,
            EmployeePeriod.period_begin_date <= period_end,
            (EmployeePeriod.period_end_date.is_(None))
            | (EmployeePeriod.period_end_date >= period_start),
        )
        .first()
        is not None
    )


def _payroll_context(payroll: Dict[str, Any]) -> str:
    trabajador = payroll.get("trabajador") if isinstance(payroll, dict) else None
    dni = trabajador.get("dni") if isinstance(trabajador, dict) else None
    periodo = payroll.get("periodo") if isinstance(payroll, dict) else None
    desde = periodo.get("desde") if isinstance(periodo, dict) else None
    hasta = periodo.get("hasta") if isinstance(periodo, dict) else None

    parts: List[str] = []
    if dni:
        parts.append(f"dni={dni}")
    if desde or hasta:
        parts.append(f"periodo={desde or '?'}..{hasta or '?'}")
    if parts:
        return " (" + ", ".join(parts) + ")"
    return ""


def _validate_structure(
    payload: Dict[str, Any],
    session=None,
    require_employee_match: bool = False,
) -> List[str]:
    errors: List[str] = []
    payrolls = payload.get("payrolls")
    if not isinstance(payrolls, list):
        return ["Top-level key 'payrolls' must be a list."]

    for idx, payroll in enumerate(payrolls):
        if not isinstance(payroll, dict):
            errors.append(f"[{idx}] payroll is not an object")
            continue

        context = _payroll_context(payroll)
        missing = [k for k in PAYROLL_REQUIRED_FIELDS if k not in payroll]
        if missing:
            errors.append(
                f"[{idx}] missing payroll fields: {', '.join(missing)}{context}"
            )
            continue

        if payroll.get("type") not in ALLOWED_PAYROLL_TYPES:
            errors.append(
                f"[{idx}] invalid payroll type: {payroll.get('type')!r}{context}"
            )

        periodo = payroll.get("periodo")
        if not isinstance(periodo, dict):
            errors.append(f"[{idx}] periodo must be an object{context}")
        else:
            desde = (periodo.get("desde") or "").strip()
            hasta = (periodo.get("hasta") or "").strip()
            if payroll.get("type") == "settlement":
                if not hasta:
                    errors.append(f"[{idx}] periodo.hasta is required for settlements{context}")
            else:
                if not (desde and hasta):
                    errors.append(f"[{idx}] periodo.desde and periodo.hasta are required{context}")

        trabajador = payroll.get("trabajador")
        if not isinstance(trabajador, dict):
            errors.append(f"[{idx}] trabajador must be an object{context}")
        else:
            ss_number = normalize_ssn(trabajador.get("ss_number"))
            dni = _normalize_id(trabajador.get("dni"))
            if not ss_number and not dni:
                errors.append(
                    f"[{idx}] trabajador.ss_number or trabajador.dni is required to match employee{context}"
                )
            elif require_employee_match and session is not None:
                employee = None
                if ss_number:
                    employee = (
                        session.query(Employee).filter_by(ss_number=ss_number).first()
                    )
                if employee is None and dni:
                    employee = (
                        session.query(Employee)
                        .filter_by(identity_card_number=dni)
                        .first()
                    )
                if employee is None:
                    errors.append(
                        f"[{idx}] no employee match for ss_number={ss_number!r} or dni={dni!r}{context}"
                    )
            if not trabajador.get("nombre"):
                errors.append(
                    f"[{idx}] trabajador.nombre is required to create employee{context}"
                )

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
                errors.append(f"[{idx}] {field}: {exc}{context}")

        lines = payroll.get("payroll_lines")
        if not isinstance(lines, list):
            errors.append(f"[{idx}] payroll_lines must be a list{context}")
            continue

        for line_idx, line in enumerate(lines):
            if not isinstance(line, dict):
                errors.append(
                    f"[{idx}][line {line_idx}] line is not an object{context}"
                )
                continue

            line_missing = [k for k in LINE_REQUIRED_FIELDS if k not in line]
            if line_missing:
                errors.append(
                    f"[{idx}][line {line_idx}] missing line fields: {', '.join(line_missing)}{context}"
                )
                continue

            if line.get("category") not in ALLOWED_LINE_CATEGORIES:
                errors.append(
                    f"[{idx}][line {line_idx}] invalid category: {line.get('category')!r}{context}"
                )
            try:
                _as_decimal(line.get("amount"))
            except ValueError as exc:
                errors.append(f"[{idx}][line {line_idx}] amount: {exc}{context}")

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
                        f"[{idx}][line {line_idx}] {bool_field} must be boolean{context}"
                    )

    return errors


def _find_or_create_employee(session, trabajador: Dict[str, Any]) -> Optional[Employee]:
    ss_number = normalize_ssn(trabajador.get("ss_number"))
    dni = _normalize_id(trabajador.get("dni"))

    employee = None
    if ss_number:
        employee = session.query(Employee).filter_by(ss_number=ss_number).first()
    if employee:
        return employee

    if dni:
        employee = session.query(Employee).filter_by(identity_card_number=dni).first()
    if employee:
        return employee

    return None


def _payroll_exists(session, employee_id: int, periodo: Dict[str, Any], liquido: Decimal) -> bool:
    desde = (periodo or {}).get("desde")
    hasta = (periodo or {}).get("hasta")
    if not (desde and hasta):
        return False
    return (
        session.query(Payroll)
        .filter(Payroll.employee_id == employee_id)
        .filter(Payroll.periodo["desde"].as_string() == str(desde))
        .filter(Payroll.periodo["hasta"].as_string() == str(hasta))
        .filter(Payroll.liquido_a_percibir == liquido)
        .first()
        is not None
    )


def _ingest_payrolls(
    session,
    payrolls: List[Dict[str, Any]],
    dry_run: bool = False,
    batch_size: int = 200,
) -> Tuple[int, int, int, List[Dict[str, Any]]]:
    created = 0
    skipped = 0
    lines_created = 0
    skipped_records: List[Dict[str, Any]] = []

    for idx, payroll in enumerate(payrolls, start=1):
        trabajador = payroll["trabajador"]
        employee = _find_or_create_employee(session, trabajador)
        ss_number = normalize_ssn(trabajador.get("ss_number"))
        dni = _normalize_id(trabajador.get("dni"))
        empresa = payroll.get("empresa") or {}

        if employee is None:
            skipped += 1
            skipped_records.append(
                {
                    "index": idx,
                    "reason": "employee_not_found",
                    "ss_number": ss_number,
                    "dni": dni,
                    "empresa_cif": (empresa.get("cif") or "").strip(),
                    "empresa_razon_social": (empresa.get("razon_social") or "").strip(),
                    "periodo_desde": (payroll.get("periodo") or {}).get("desde"),
                    "periodo_hasta": (payroll.get("periodo") or {}).get("hasta"),
                    "type": payroll.get("type"),
                }
            )
            continue

        if employee.id is None:
            raise RuntimeError("Employee id is None after creation/lookup.")
        employee_id = int(employee.id)

        periodo = payroll.get("periodo") or {}
        client = _resolve_client(session, empresa)
        if client is None or not _has_valid_employee_period(session, employee_id, periodo, client.id):
            skipped += 1
            skipped_records.append(
                {
                    "index": idx,
                    "reason": "invalid_employee_period",
                    "ss_number": ss_number,
                    "dni": dni,
                    "empresa_cif": (empresa.get("cif") or "").strip(),
                    "empresa_razon_social": (empresa.get("razon_social") or "").strip(),
                    "periodo_desde": periodo.get("desde"),
                    "periodo_hasta": periodo.get("hasta"),
                    "type": payroll.get("type"),
                }
            )
            continue

        liquido = _as_decimal(payroll.get("liquido_a_percibir"))
        if _payroll_exists(session, employee_id, periodo, liquido):
            skipped += 1
            continue

        warnings_text = _normalize_warnings(payroll.get("warnings"))

        payroll_row = Payroll(
            employee_id=employee_id,
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

    return created, skipped, lines_created, skipped_records


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

    engine = create_database_engine(database_url=args.db_url, echo=False)
    session = get_session(engine)

    try:
        errors = _validate_structure(payload, session=session, require_employee_match=False)
        if errors:
            print("Structure validation failed:")
            for err in errors[:50]:
                print(f" - {err}")
            if len(errors) > 50:
                print(f" ... and {len(errors) - 50} more")
            return 1

        created, skipped, lines_created, skipped_records = _ingest_payrolls(
            session,
            payload["payrolls"],
            dry_run=args.dry_run,
        )
        if skipped_records:
            input_dir = os.path.dirname(args.input) or "."
            base_name = os.path.splitext(os.path.basename(args.input))[0]
            log_path = os.path.join(input_dir, f"{base_name}_skipped.json")
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(skipped_records, f, ensure_ascii=False, indent=2)
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
