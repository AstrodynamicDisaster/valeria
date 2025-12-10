#!/usr/bin/env python3
"""
Reprocess production DB query results (company_employees join companies)
and create employee periods in the local database.

Usage:
    python scripts/reprocess_prod_query.py "Company Name or CIF"

Notes:
    - Reads from the production database using core.database.create_prod_engine
      and the fixed query provided.
    - Writes into the local/target database using create_database_engine.
    - Creates employees when missing and applies the merge logic in
      core.agent.vida_laboral to avoid overlapping ALTA periods.
"""

import os
import sys
from typing import Mapping, Any

# Allow running as a script from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import MetaData, Table, select, or_
from sqlalchemy.orm import sessionmaker

from core.database import create_database_engine, create_prod_engine
from core.agent import vida_laboral
from core.agent.state import ProcessingState, VidaLaboralContext
from core.models import Client


def build_prod_query(prod_engine, company_identifier: str, employee_identifier: str | None = None):
    """SQLAlchemy Core query with required company filter and optional employee filter."""
    md = MetaData()
    company_employees = Table("company_employees", md, schema="public", autoload_with=prod_engine)
    companies = Table("companies", md, schema="public", autoload_with=prod_engine)

    excluded_statuses = ("Test", "Error", "enrollment_cancelled", "cancelling_casia", "Canceled")

    stmt = (
        select(
            company_employees.c.first_name.label("first_name"),
            company_employees.c.last_name.label("last_name"),
            company_employees.c.last_name2.label("last_name2"),
            company_employees.c.ss_number.label("ss_number"),
            company_employees.c.identity_card_number.label("identity_card_number"),
            company_employees.c.begin_date.label("begin_date"),
            company_employees.c.created_at.label("created_at"),
            company_employees.c.id.label("id"),
            company_employees.c.enrollment_confirmation.label("enrollment_confirmation"),
            company_employees.c.employee_status.label("employee_status"),
            company_employees.c.contract_code.label("contract_code"),
            company_employees.c.end_date.label("end_date"),
            company_employees.c.cancel_enrollment_date.label("cancel_enrollment_date"),
            company_employees.c.irpf.label("irpf"),
            company_employees.c.rlce.label("rlce"),
            companies.c.name.label("Companies__name"),
            companies.c.cif.label("Companies__cif"),
            companies.c.begin_date.label("Companies__begin_date"),
            companies.c.payslips.label("Companies__payslips"),
        )
        .select_from(company_employees.outerjoin(companies, company_employees.c.company_id == companies.c.id))
        .where(
            companies.c.payslips.is_(True),
            companies.c.status == "Active",
            or_(companies.c.cif == company_identifier, companies.c.name == company_identifier),
            or_(
                company_employees.c.employee_status.is_(None),
                ~company_employees.c.employee_status.in_(excluded_statuses),
            ),
        )
    )
    if employee_identifier:
        stmt = stmt.where(
            or_(
                company_employees.c.identity_card_number == employee_identifier,
                company_employees.c.ss_number == employee_identifier,
            )
        )
    return stmt


def map_row(row: Mapping[str, Any]) -> dict:
    """Convert a query row mapping to the vida_laboral schema."""
    status = (row.get("employee_status") or "").strip().lower()
    end_date = row.get("end_date")
    situacion = "BAJA" if status != "active" or end_date else "ALTA"

    begin_date = row.get("begin_date")
    surname1 = (row.get("last_name") or "").strip()
    surname2 = (row.get("last_name2") or "").strip()
    full_surnames = f"{surname1} {surname2}".strip()

    return {
        "naf": (row.get("ss_number") or "").strip(),
        "documento": (row.get("identity_card_number") or "").strip(),
        # Keep original order for now; downstream may adjust parsing
        "nombre": f"{(row.get('first_name') or '').strip()} {full_surnames}".strip(),
        "first_name_raw": (row.get("first_name") or "").strip(),
        "surname1_raw": surname1,
        "surname2_raw": surname2 or None,
        "situacion": situacion,
        "f_real_alta": begin_date.isoformat() if begin_date else None,
        "f_efecto_alta": begin_date.isoformat() if begin_date else None,
        "f_real_sit": end_date.isoformat() if end_date else None,
        "codigo_contrato": (row.get("contract_code") or "").strip(),
    }


def process_prod_query(client_identifier: str, employee_identifier: str | None = None) -> dict:
    """Fetch filtered rows from prod, process into local DB."""
    target_engine = create_database_engine()
    prod_engine = create_prod_engine(echo=False)

    TargetSession = sessionmaker(bind=target_engine)
    target_session = TargetSession()

    try:
        client = target_session.query(Client).filter(
            (Client.name == client_identifier) | (Client.cif == client_identifier)
        ).first()
        if not client:
            return {"success": False, "error": f"Client '{client_identifier}' not found in target DB"}

        ctx = VidaLaboralContext(ProcessingState(client_id=client.id), create_employees=True)
        row_count = 0

        with prod_engine.connect() as conn:
            stmt = build_prod_query(prod_engine, company_identifier=client_identifier, employee_identifier=employee_identifier)
            result = conn.execute(stmt)
            for row in result.mappings():  # returns RowMapping
                # Optional: skip if row company doesn't match selected client
                if row.get("Companies__cif") and row["Companies__cif"] != client.cif:
                    continue
                mapped = map_row(row)
                vida_laboral.process_row(target_session, client.id, mapped, ctx)
                row_count += 1

        target_session.commit()
        return {
            "success": True,
            "rows_processed": row_count,
            "employees_created": ctx.employees_created,
            "employees_updated": ctx.employees_updated,
            "periods_created": ctx.periods_created,
            "vacation_periods_created": ctx.vacation_periods_created,
        }
    except Exception as exc:  # pragma: no cover - operational script
        target_session.rollback()
        return {"success": False, "error": str(exc)}
    finally:
        target_session.close()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/reprocess_prod_query.py \"Company Name or CIF\" [employee DNI/NIE/SSN]")
        sys.exit(1)

    client_identifier = sys.argv[1]
    employee_identifier = sys.argv[2] if len(sys.argv) >= 3 else None

    result = process_prod_query(client_identifier, employee_identifier)

    if result.get("success"):
        print(f"Processed {result['rows_processed']} rows for {client_identifier}")
        print(f"Employees created: {result['employees_created']}, updated: {result['employees_updated']}")
        print(f"Periods created: {result['periods_created']} (vacation: {result['vacation_periods_created']})")
        sys.exit(0)

    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    sys.exit(1)


if __name__ == "__main__":
    main()
