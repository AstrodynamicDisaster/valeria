"""
Vida laboral CSV processing utilities.
"""

from __future__ import annotations

from typing import Dict

from sqlalchemy.orm import Session

from core.agent.state import VidaLaboralContext
from core.agent.utils import parse_date, parse_spanish_name
from core.models import Employee, VacationPeriod


def handle_alta(session: Session, client_id: str, row: Dict[str, str], context: VidaLaboralContext) -> None:
    """Create a new employment period for an ALTA record."""
    # Remove only the first leading zero if present (not all zeros)
    documento = row['documento'][1:] if row['documento'].startswith('0') else row['documento']
    first_name, last_name, last_name2 = parse_spanish_name(row['nombre'])
    identity_doc_type = 'NIE' if documento.startswith(('X', 'Y', 'Z')) else 'DNI'
    begin_date = parse_date(row.get('f_efecto_alta'))

    employee = Employee(
        company_id=client_id,
        first_name=first_name,
        last_name=last_name,
        last_name2=last_name2,
        identity_card_number=documento,
        identity_doc_type=identity_doc_type,
        ss_number=row.get('naf', '').strip() or None,
        begin_date=begin_date,
        end_date=None,
        salary=1500.00,
        role="Empleado",
        employee_status='Active',
        tipo_contrato=row.get('codigo_contrato', ''),
    )
    session.add(employee)
    context.employees_created += 1
    print(f"✅ Created new employment period for {row['nombre']} starting {begin_date}")


def handle_baja(session: Session, client_id: str, row: Dict[str, str], context: VidaLaboralContext) -> None:
    """Update or create employment records for BAJA situations."""
    # Remove only the first leading zero if present (not all zeros)
    documento = row['documento'][1:] if row['documento'].startswith('0') else row['documento']
    first_name, last_name, last_name2 = parse_spanish_name(row['nombre'])
    identity_doc_type = 'NIE' if documento.startswith(('X', 'Y', 'Z')) else 'DNI'

    employee = session.query(Employee).filter_by(
        company_id=client_id,
        identity_card_number=documento,
        end_date=None,
    ).order_by(Employee.begin_date.desc()).first()

    end_date = parse_date(row.get('f_real_sit'))

    if employee:
        employee.end_date = end_date
        employee.employee_status = 'Terminated'
        context.employees_updated += 1
        print(f"✅ Closed employment period for {row['nombre']} ending {end_date}")
        return

    begin_date = parse_date(row.get('f_efecto_alta'))
    employee = Employee(
        company_id=client_id,
        first_name=first_name,
        last_name=last_name,
        last_name2=last_name2,
        identity_card_number=documento,
        identity_doc_type=identity_doc_type,
        ss_number=row.get('naf', '').strip() or None,
        begin_date=begin_date,
        end_date=end_date,
        salary=1500.00,
        role="Empleado",
        employee_status='Terminated',
        tipo_contrato=row.get('codigo_contrato', ''),
    )
    session.add(employee)
    context.employees_created += 1
    print(f"⚠️  BAJA record without matching ALTA for {row['nombre']} ({documento})")
    print(f"✅ Created terminated record for {row['nombre']} (begin: {begin_date}, end: {end_date})")


def handle_vacacion(session: Session, client_id: str, row: Dict[str, str], context: VidaLaboralContext) -> None:
    """Record a VAC.RETRIB.NO vacation period."""
    # Remove only the first leading zero if present (not all zeros)
    documento = row['documento'][1:] if row['documento'].startswith('0') else row['documento']
    employee = session.query(Employee).filter_by(
        company_id=client_id,
        identity_card_number=documento,
    ).order_by(Employee.begin_date.desc()).first()

    if not employee:
        print(f"⚠️  VAC.RETRIB.NO record without employee for {row['nombre']} ({documento})")
        return

    vacation_start = parse_date(row.get('f_efecto_alta'))
    vacation_end = parse_date(row.get('f_real_sit'))

    if not vacation_start or not vacation_end:
        print(f"⚠️  Skipping VAC.RETRIB.NO for {row['nombre']} ({documento}): missing dates")
        return

    vacation = VacationPeriod(
        employee_id=employee.id,
        start_date=vacation_start,
        end_date=vacation_end,
        vacation_type='VAC.RETRIB.NO',
        notes=f"Imported from vida laboral: {row['nombre']}",
    )
    session.add(vacation)
    context.vacation_periods_created += 1
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
