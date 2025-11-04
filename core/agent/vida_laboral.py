"""
Vida laboral CSV processing utilities.
"""

from __future__ import annotations

from typing import Dict

from sqlalchemy.orm import Session

from core.agent.state import VidaLaboralContext
from core.agent.utils import parse_date, parse_spanish_name
from core.models import Employee, EmployeePeriod


def handle_alta(session: Session, client_id: str, row: Dict[str, str], context: VidaLaboralContext) -> None:
    """Create or find employee and create ALTA period."""
    # Remove only the first leading zero if present (not all zeros)
    documento = row['documento'][1:] if row['documento'].startswith('0') else row['documento']
    first_name, last_name, last_name2 = parse_spanish_name(row['nombre'])
    identity_doc_type = 'NIE' if documento.startswith(('X', 'Y', 'Z')) else 'DNI'
    begin_date = parse_date(row.get('f_efecto_alta'))
    ss_number = row.get('naf', '').strip() or None

    # Try to find existing employee using priority-based matching
    employee = None
    # Priority 1: Try SSN match (if available) - more reliable across NIE→DNI transitions
    if ss_number:
        employee = session.query(Employee).filter_by(ss_number=ss_number).first()

    # Priority 2: Fall back to DNI/NIE match
    if not employee:
        employee = session.query(Employee).filter_by(identity_card_number=documento).first()

    # If not found and we're allowed to create employees
    if not employee and context.create_employees:
        employee = Employee(
            first_name=first_name,
            last_name=last_name,
            last_name2=last_name2,
            identity_card_number=documento,
            identity_doc_type=identity_doc_type,
            ss_number=ss_number,
        )
        session.add(employee)
        session.flush()  # Get the employee ID
        context.employees_created += 1
        print(f"✅ Created new employee: {row['nombre']} ({documento})")

    # If still not found (and we're not creating), skip
    if not employee:
        context.employees_not_found += 1
        print(f"⚠️  Skipping ALTA for {row['nombre']} ({documento}) - employee not found")
        return

    # Create the ALTA period
    period = EmployeePeriod(
        employee_id=employee.id,
        company_id=client_id,
        period_begin_date=begin_date,
        period_end_date=None,
        period_type='alta',
        tipo_contrato=row.get('codigo_contrato', ''),
        salary=1500.00,  # Default salary, can be updated later
        role="Empleado",  # Default role
        notes=f"ALTA from vida laboral: {row['nombre']}"
    )
    session.add(period)
    context.periods_created += 1
    print(f"✅ Created ALTA period for {row['nombre']} starting {begin_date}")


def handle_baja(session: Session, client_id: str, row: Dict[str, str], context: VidaLaboralContext) -> None:
    """Find active ALTA period and close it (change to BAJA)."""
    # Remove only the first leading zero if present (not all zeros)
    documento = row['documento'][1:] if row['documento'].startswith('0') else row['documento']
    first_name, last_name, last_name2 = parse_spanish_name(row['nombre'])
    identity_doc_type = 'NIE' if documento.startswith(('X', 'Y', 'Z')) else 'DNI'
    ss_number = row.get('naf', '').strip() or None
    end_date = parse_date(row.get('f_real_sit'))

    # Find employee using priority-based matching
    employee = None
    # Priority 1: Try SSN match (if available) - more reliable across NIE→DNI transitions
    if ss_number:
        employee = session.query(Employee).filter_by(ss_number=ss_number).first()

    # Priority 2: Fall back to DNI/NIE match
    if not employee:
        employee = session.query(Employee).filter_by(identity_card_number=documento).first()

    if not employee:
        context.employees_not_found += 1
        print(f"⚠️  Skipping BAJA for {row['nombre']} ({documento}) - employee not found")
        return

    # Find active ALTA period for this employee and company
    active_period = session.query(EmployeePeriod).filter_by(
        employee_id=employee.id,
        company_id=client_id,
        period_type='alta',
        period_end_date=None
    ).order_by(EmployeePeriod.period_begin_date.desc()).first()

    if active_period:
        # Modify the existing ALTA period: add end_date and change type to 'baja'
        active_period.period_end_date = end_date
        active_period.period_type = 'baja'
        context.employees_updated += 1
        print(f"✅ Closed ALTA period for {row['nombre']} → BAJA ending {end_date}")
        return

    # If no active ALTA found, create a terminated period (BAJA without prior ALTA in our system)
    begin_date = parse_date(row.get('f_efecto_alta'))
    period = EmployeePeriod(
        employee_id=employee.id,
        company_id=client_id,
        period_begin_date=begin_date,
        period_end_date=end_date,
        period_type='baja',
        tipo_contrato=row.get('codigo_contrato', ''),
        salary=1500.00,
        role="Empleado",
        notes=f"BAJA without prior ALTA: {row['nombre']}"
    )
    session.add(period)
    context.periods_created += 1
    print(f"⚠️  BAJA without matching ALTA for {row['nombre']} ({documento})")
    print(f"✅ Created terminated period for {row['nombre']} (begin: {begin_date}, end: {end_date})")


def handle_vacacion(session: Session, client_id: str, row: Dict[str, str], context: VidaLaboralContext) -> None:
    """Record a VAC.RETRIB.NO vacation period."""
    # Remove only the first leading zero if present (not all zeros)
    documento = row['documento'][1:] if row['documento'].startswith('0') else row['documento']
    ss_number = row.get('naf', '').strip() or None

    # Find employee using priority-based matching
    employee = None
    # Priority 1: Try SSN match (if available) - more reliable across NIE→DNI transitions
    if ss_number:
        employee = session.query(Employee).filter_by(ss_number=ss_number).first()

    # Priority 2: Fall back to DNI/NIE match
    if not employee:
        employee = session.query(Employee).filter_by(identity_card_number=documento).first()

    if not employee:
        context.employees_not_found += 1
        print(f"⚠️  Skipping VAC.RETRIB.NO for {row['nombre']} ({documento}) - employee not found")
        return

    vacation_start = parse_date(row.get('f_efecto_alta'))
    vacation_end = parse_date(row.get('f_real_sit'))

    if not vacation_start or not vacation_end:
        print(f"⚠️  Skipping VAC.RETRIB.NO for {row['nombre']} ({documento}): missing dates")
        return

    # Create vacation period using EmployeePeriod model
    vacation_period = EmployeePeriod(
        employee_id=employee.id,
        company_id=client_id,
        period_begin_date=vacation_start,
        period_end_date=vacation_end,
        period_type='vacaciones',
        notes=f"VAC.RETRIB.NO from vida laboral: {row['nombre']}",
    )
    session.add(vacation_period)
    context.vacation_periods_created += 1
    context.periods_created += 1
    print(f"✅ Added vacation period for {row['nombre']} ({vacation_start} to {vacation_end})")


HANDLERS = {
    'ALTA': handle_alta,
    'BAJA': handle_baja,
    'VAC.RETRIB.NO': handle_vacacion,
}


def process_row(session: Session, client_id: str, row: Dict[str, str], context: VidaLaboralContext) -> None:
    """Dispatch vida laboral rows to the appropriate handler."""
    situacion = row.get('situacion')
    if not situacion:
        return

    handler = HANDLERS.get(situacion)
    if handler is None:
        return

    handler(session, client_id, row, context)
