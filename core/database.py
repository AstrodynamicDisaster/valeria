#!/usr/bin/env python3
"""
ValerIA Core Database Utilities
Database connection management and utility functions.
These functions are used at runtime by the application.
"""

from __future__ import annotations

import os
import re
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional, Sequence

from sqlalchemy import create_engine, func
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session, sessionmaker

from core.models import Client, ClientLocation, Employee, EmployeePeriod, Payroll, PayrollLine
from core.normalization import normalize_ssn

from dotenv import load_dotenv
load_dotenv()


def create_database_engine(database_url: str = None, echo: bool = False):
    """Create database engine from environment or default values"""
    if database_url is None:
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DB', 'valeria')
        db_user = os.getenv('POSTGRES_USER', 'valeria')
        db_password = os.getenv('POSTGRES_PASSWORD', 'YourStrongPassw0rd!')
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    engine = create_engine(database_url, echo=echo)
    return engine

def create_prod_engine(database_url: str = None, echo: bool = True):
    """Create database engine from environment or default values"""
    database_url = os.getenv('PROD_URL', '')
    print(f"Connecting to production database at: {database_url}")
    engine = create_engine(url=database_url, echo=echo)
    return engine


def get_session(engine=None, echo: bool = False) -> Session:
    """Create a SQLAlchemy session bound to the given engine (or default engine)."""
    if engine is None:
        engine = create_database_engine(echo=echo)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


# Document Storage Utilities

def _documents_disabled() -> bool:
    """Flag to disable local documents folder creation."""
    return os.getenv("DISABLE_LOCAL_DOCUMENTS", "false").lower() == "true"


def ensure_documents_directory():
    """Create documents directory structure if it doesn't exist.

    Can be disabled by setting DISABLE_LOCAL_DOCUMENTS=true to avoid creating
    the ./documents folder in environments that never store local files.
    """
    if _documents_disabled():
        raise RuntimeError(
            "Local documents storage disabled (set DISABLE_LOCAL_DOCUMENTS=false to re-enable)"
        )

    base_dir = "./documents"
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def get_client_document_path(client_id: str) -> str:
    """Get document directory path for a client"""
    base_dir = ensure_documents_directory()
    client_dir = os.path.join(base_dir, f"client_{client_id}")
    os.makedirs(client_dir, exist_ok=True)
    return client_dir


def get_employee_document_path(client_id: str, employee_id: int) -> str:
    """Get document directory path for an employee"""
    client_dir = get_client_document_path(client_id)
    employee_dir = os.path.join(client_dir, f"employee_{employee_id}")
    os.makedirs(employee_dir, exist_ok=True)
    return employee_dir


def save_document_file(file_content: bytes, filename: str, client_id: str, employee_id: int = None) -> str:
    """Save document file and return relative path"""
    if employee_id:
        doc_dir = get_employee_document_path(client_id, employee_id)
    else:
        doc_dir = get_client_document_path(client_id)

    file_path = os.path.join(doc_dir, filename)

    with open(file_path, 'wb') as f:
        f.write(file_content)

    # Return relative path for database storage
    relative_path = os.path.relpath(file_path, ".")
    return relative_path


def load_document_file(file_path: str) -> bytes:
    """Load document file from relative path"""
    with open(file_path, 'rb') as f:
        return f.read()


# Vida Laboral CSV Parsing Utility

def parse_vida_laboral_csv_simple(csv_content: str, client_id: str) -> dict:
    """Simple vida laboral CSV parser - core functionality only"""
    import csv
    from io import StringIO

    result = {
        'employees': {},
        'employment_data': [],
        'errors': []
    }

    try:
        csv_reader = csv.DictReader(StringIO(csv_content))

        for row in csv_reader:
            documento = row.get('documento', '').strip()
            nombre = row.get('nombre', '').strip()
            situacion = row.get('situacion', '').strip()

            if not documento or not nombre:
                continue

            # Store unique employees
            if documento not in result['employees']:
                result['employees'][documento] = {
                    'documento': documento,
                    'full_name': nombre,
                    'client_id': client_id
                }

            # Store employment events for checklist generation
            if situacion in ['ALTA', 'BAJA']:
                result['employment_data'].append({
                    'documento': documento,
                    'situacion': situacion,
                    'f_real_sit': row.get('f_real_sit', '').strip()
                })

    except Exception as e:
        result['errors'].append(f"Error parsing CSV: {str(e)}")

    return result


# Seed Data for Nomina Concepts

BASIC_NOMINA_CONCEPTS = [
    # Basic salary concepts
    {'concept_code': '001', 'short_desc': 'Salario base', 'tributa_irpf': True, 'cotiza_ss': True, 'default_group': 'ordinaria'},
    {'concept_code': '002', 'short_desc': 'Antigüedad', 'tributa_irpf': True, 'cotiza_ss': True, 'default_group': 'ordinaria'},
    {'concept_code': '120', 'short_desc': 'Plus convenio', 'tributa_irpf': True, 'cotiza_ss': True, 'default_group': 'ordinaria'},
    {'concept_code': '301', 'short_desc': 'Horas extra', 'tributa_irpf': True, 'cotiza_ss': True, 'default_group': 'variable'},

    # In-kind benefits
    {'concept_code': '601', 'short_desc': 'Seguro médico', 'tributa_irpf': True, 'cotiza_ss': False, 'en_especie': True, 'default_group': 'especie'},
    {'concept_code': '620', 'short_desc': 'Ticket restaurant', 'tributa_irpf': True, 'cotiza_ss': False, 'en_especie': True, 'default_group': 'especie'},

    # Deductions
    {'concept_code': '700', 'short_desc': 'IRPF', 'tributa_irpf': False, 'cotiza_ss': False, 'default_group': 'deduccion'},
    {'concept_code': '730', 'short_desc': 'SS Trabajador', 'tributa_irpf': False, 'cotiza_ss': False, 'default_group': 'deduccion'}
]


# ============================================================================
# Query endpoints
# ============================================================================

_ISO_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def _parse_date_str(value: str) -> date:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    # Fallback: try ISO parser for datetimes like 2025-11-01T00:00:00Z
    try:
        from dateutil.parser import isoparse
        return isoparse(value).date()
    except Exception as e:  # pragma: no cover
        raise ValueError(f"Unsupported date format: {value}") from e


def _parse_period_iso(period_iso: str) -> tuple[date, date]:
    """
    Parse a period input into (start_date, end_date).

    Supported inputs:
    - 'YYYY-MM' (month): expands to first/last day of month.
    - 'YYYY-MM-DD' or 'DD-MM-YYYY' or 'DD/MM/YYYY' (single date): start=end.
    - 'start/end' or 'start to end' or 'start → end': date range.
    """
    if not period_iso:
        raise ValueError("period_iso is required")

    raw = period_iso.strip()
    if _ISO_MONTH_RE.match(raw):
        year, month = map(int, raw.split("-"))
        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])
        return start, end

    for sep in ("/", "→", " to "):
        if sep in raw:
            parts = [p.strip() for p in raw.split(sep) if p.strip()]
            if len(parts) == 2:
                start = _parse_date_str(parts[0])
                end = _parse_date_str(parts[1])
                return (start, end) if start <= end else (end, start)

    single = _parse_date_str(raw)
    return single, single


def list_employee_ssns_for_company_period(
    session: Session,
    period_iso: str,
    company_ssn: str,  # Note: This is actually the CCC (Código Cuenta Cotización)
) -> list[str]:
    """
    Return distinct employee SSNs for employees with any EmployeePeriod overlapping
    the given period and company location.

    Args:
        session: SQLAlchemy session.
        period_iso: Period string in ISO-ish format (see _parse_period_iso).
        company_ssn: Company location's CCC (ClientLocation.ccc_ss).
    """
    period_start, period_end = _parse_period_iso(period_iso)

    location = session.query(ClientLocation).filter(ClientLocation.ccc_ss == company_ssn).first()
    if not location:
        return []

    rows = (
        session.query(Employee.ss_number)
        .join(EmployeePeriod, Employee.id == EmployeePeriod.employee_id)
        .filter(
            EmployeePeriod.location_id == location.id,
            EmployeePeriod.period_begin_date <= period_end,
            func.coalesce(EmployeePeriod.period_end_date, period_end) >= period_start,
            Employee.ss_number.isnot(None),
        )
        .distinct()
        .all()
    )
    return [r[0] for r in rows if r[0]]


def get_payroll_line_aggregates(
    session: Session,
    employee_ssn: str,
    company_ssn: str,  # Note: This is actually the CCC (Código Cuenta Cotización)
    period_iso: str,
    concepto_filter: Optional[str] = None,
    category_type: Optional[str] = None,
) -> dict:
    """
    Aggregate payroll line totals (sum of amount) for an employee/company location/period.

    Args:
        session: SQLAlchemy session.
        employee_ssn: Employee Social Security number (Employee.ss_number).
        company_ssn: Company location's CCC (ClientLocation.ccc_ss).
        period_iso: Period string in ISO-ish format.
        concepto_filter: Optional substring filter on PayrollLine.concept (case-insensitive).
        category_type: Optional category filter: 'deduccion', 'devengo', 'aportacion empresa'
                       (spaces/underscore tolerated).

    Returns:
        Dict with totals by category and overall total.
    """
    period_start, period_end = _parse_period_iso(period_iso)

    normalized_ssn = normalize_ssn(employee_ssn)
    employee = session.query(Employee).filter(Employee.ss_number == normalized_ssn).first()
    location = session.query(ClientLocation).filter(ClientLocation.ccc_ss == company_ssn).first()
    if not employee or not location:
        return {"employee_ssn": normalized_ssn, "company_ssn": company_ssn, "period": period_iso, "totals": {}, "total_importe": Decimal("0.00")}

    # Ensure employee has a period for this location overlapping the requested period.
    has_company_period = (
        session.query(EmployeePeriod.id)
        .filter(
            EmployeePeriod.employee_id == employee.id,
            EmployeePeriod.location_id == location.id,
            EmployeePeriod.period_begin_date <= period_end,
            func.coalesce(EmployeePeriod.period_end_date, period_end) >= period_start,
        )
        .first()
    )
    if not has_company_period:
        return {"employee_ssn": normalized_ssn, "company_ssn": company_ssn, "period": period_iso, "totals": {}, "total_importe": Decimal("0.00")}

    # Pull payrolls for employee; filter by period overlap in Python due to mixed date formats.
    payroll_rows: Sequence[Row[tuple[int, Any]]] = (
        session.query(Payroll.id, Payroll.periodo)
        .filter(Payroll.employee_id == employee.id)
        .all()
    )
    matching_payroll_ids: list[int] = []
    for payroll_id, periodo in payroll_rows:
        if not isinstance(periodo, dict):
            continue
        desde = periodo.get("desde")
        hasta = periodo.get("hasta") or desde
        if not desde:
            continue
        try:
            pay_start = _parse_date_str(str(desde))
            pay_end = _parse_date_str(str(hasta)) if hasta else pay_start
        except Exception:
            continue
        if pay_start <= period_end and pay_end >= period_start:
            matching_payroll_ids.append(payroll_id)

    if not matching_payroll_ids:
        return {"employee_ssn": normalized_ssn, "company_ssn": company_ssn, "period": period_iso, "totals": {}, "total_importe": Decimal("0.00")}

    query = (
        session.query(PayrollLine.category, func.sum(PayrollLine.amount))
        .filter(PayrollLine.payroll_id.in_(matching_payroll_ids))
    )

    if concepto_filter:
        query = query.filter(PayrollLine.concept.ilike(f"%{concepto_filter.strip()}%"))

    normalized_category = None
    if category_type:
        normalized_category = category_type.strip().lower().replace(" ", "_")
        if normalized_category == "aportacion_empresa" or normalized_category == "aportacionempresa":
            normalized_category = "aportacion_empresa"
        query = query.filter(PayrollLine.category == normalized_category)

    query = query.group_by(PayrollLine.category)
    results = query.all()

    totals: dict[str, Decimal] = {}
    total_importe = Decimal("0.00")
    for cat, amount in results:
        amount = amount or Decimal("0.00")
        totals[str(cat)] = amount
        total_importe += amount

    # If a category was requested but no rows matched, include empty category with 0.
    if normalized_category and normalized_category not in totals:
        totals[normalized_category] = Decimal("0.00")

    return {
        "employee_ssn": normalized_ssn,
        "company_ssn": company_ssn,
        "period": period_iso,
        "concepto_filter": concepto_filter,
        "category_type": normalized_category,
        "totals": totals,
        "total_importe": total_importe,
        "payroll_count": len(matching_payroll_ids),
    }


def get_employee_devengo_total(
    session: Session,
    employee_ssn: str,
    company_ssn: str,  # Note: This is actually the CCC (Código Cuenta Cotización)
    period_iso: str,
) -> dict:
    """
    Aggregate sum of Payroll.devengo_total for an employee/company location/period.

    Args:
        session: SQLAlchemy session.
        employee_ssn: Employee Social Security number (Employee.ss_number).
        company_ssn: Company location's CCC (ClientLocation.ccc_ss).
        period_iso: Period string in ISO-ish format.

    Returns:
        Dict with total devengo and payroll count.
    """
    period_start, period_end = _parse_period_iso(period_iso)

    normalized_ssn = normalize_ssn(employee_ssn)
    employee = session.query(Employee).filter(Employee.ss_number == normalized_ssn).first()
    location = session.query(ClientLocation).filter(ClientLocation.ccc_ss == company_ssn).first()
    if not employee or not location:
        return {"employee_ssn": normalized_ssn, "company_ssn": company_ssn, "period": period_iso, "devengo_total": Decimal("0.00"), "payroll_count": 0}

    has_company_period = (
        session.query(EmployeePeriod.id)
        .filter(
            EmployeePeriod.employee_id == employee.id,
            EmployeePeriod.location_id == location.id,
            EmployeePeriod.period_begin_date <= period_end,
            func.coalesce(EmployeePeriod.period_end_date, period_end) >= period_start,
        )
        .first()
    )
    if not has_company_period:
        return {"employee_ssn": normalized_ssn, "company_ssn": company_ssn, "period": period_iso, "devengo_total": Decimal("0.00"), "payroll_count": 0}

    payroll_rows: Sequence[Row[tuple[int, Any, Decimal]]] = (
        session.query(Payroll.id, Payroll.periodo, Payroll.devengo_total)
        .filter(Payroll.employee_id == employee.id)
        .all()
    )
    matching_payroll_ids: list[int] = []
    for payroll_id, periodo, _dev in payroll_rows:
        if not isinstance(periodo, dict):
            continue
        desde = periodo.get("desde")
        hasta = periodo.get("hasta") or desde
        if not desde:
            continue
        try:
            pay_start = _parse_date_str(str(desde))
            pay_end = _parse_date_str(str(hasta)) if hasta else pay_start
        except Exception:
            continue
        if pay_start <= period_end and pay_end >= period_start:
            matching_payroll_ids.append(payroll_id)

    if not matching_payroll_ids:
        return {"employee_ssn": normalized_ssn, "company_ssn": company_ssn, "period": period_iso, "devengo_total": Decimal("0.00"), "payroll_count": 0}

    devengo_sum = (
        session.query(func.sum(Payroll.devengo_total))
        .filter(Payroll.id.in_(matching_payroll_ids))
        .scalar()
    ) or Decimal("0.00")

    return {
        "employee_ssn": normalized_ssn,
        "company_ssn": company_ssn,
        "period": period_iso,
        "devengo_total": devengo_sum,
        "payroll_count": len(matching_payroll_ids),
    }
