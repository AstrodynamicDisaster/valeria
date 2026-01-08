#!/usr/bin/env python3
"""
Modelo 190 query helpers.

Focused SQLAlchemy queries for tax reporting.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import exists, func
from sqlalchemy.orm import Session

from core.database import get_session
from core.models import Client, ClientLocation, Employee, EmployeePeriod, Payroll, PayrollLine


def get_employee_devengo_no_sickpay_total(
    session: Session,
    employee_ssn: str,
    company_cif: str,
    period_start: str,
    period_end: str,
) -> dict:
    """
    Sum devengo amounts (excluding sick pay) for an employee/company/period.

    Args:
        session: SQLAlchemy session.
        employee_ssn: Employee Social Security number (Employee.ss_number).
        company_cif: Client CIF (Client.cif).
        period_start: Period start date string matching payroll.periodo->>'desde'.
        period_end: Period end date string matching payroll.periodo->>'hasta'.

    Returns:
        Dict with total devengo (excluding sick pay).
    """
    company_match = (
        session.query(EmployeePeriod.id)
        .join(ClientLocation, EmployeePeriod.location_id == ClientLocation.id)
        .join(Client, ClientLocation.company_id == Client.id)
        .filter(
            EmployeePeriod.employee_id == Employee.id,
            Client.cif == company_cif,
        )
        .exists()
    )

    total = (
        session.query(func.coalesce(func.sum(PayrollLine.amount), 0))
        .join(Payroll, PayrollLine.payroll_id == Payroll.id)
        .join(Employee, Payroll.employee_id == Employee.id)
        .filter(
            Employee.ss_number == employee_ssn,
            company_match,
            PayrollLine.category == "devengo",
            PayrollLine.is_sickpay.is_(False),
            Payroll.periodo["desde"].astext == period_start,
            Payroll.periodo["hasta"].astext == period_end,
        )
        .scalar()
    )

    return {
        "employee_ssn": employee_ssn,
        "company_cif": company_cif,
        "period_start": period_start,
        "period_end": period_end,
        "devengo_no_sickpay_total": total or Decimal("0.00"),
    }


def get_employee_devengo_no_sickpay_total_with_session(
    employee_ssn: str,
    company_cif: str,
    period_start: str,
    period_end: str,
    *,
    echo: bool = False,
) -> dict:
    """Convenience wrapper that manages its own session."""
    session = get_session(echo=echo)
    try:
        return get_employee_devengo_no_sickpay_total(
            session, employee_ssn, company_cif, period_start, period_end
        )
    finally:
        session.close()


__all__ = [
    "get_employee_devengo_no_sickpay_total",
    "get_employee_devengo_no_sickpay_total_with_session",
]
