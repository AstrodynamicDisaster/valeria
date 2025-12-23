#!/usr/bin/env python3
"""
ValerIA Core Database Models
SQLAlchemy ORM models for the payroll processing workflow.
These models are used at runtime by the application.
"""

from datetime import datetime
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, JSON, Numeric,
    String, Text
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Client(Base):
    """Client companies using payroll services"""
    __tablename__ = 'clients'

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(Text, nullable=False)  # Was fiscal_name
    cif = Column(Text, unique=True, nullable=False)  # Was nif
    fiscal_address = Column(Text)
    email = Column(Text)
    phone = Column(Text)
    begin_date = Column(DateTime(timezone=True))
    managed_by = Column(Text)
    payslips = Column(Boolean, default=True)

    # Legal representative fields (matching production)
    legal_repr_first_name = Column(Text)
    legal_repr_last_name1 = Column(Text)
    legal_repr_last_name2 = Column(Text)
    legal_repr_nif = Column(Text)
    legal_repr_role = Column(Text)
    legal_repr_phone = Column(Text)
    legal_repr_email = Column(Text)

    # Status and metadata
    status = Column(Text, default='Active')
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    locations = relationship("ClientLocation", back_populates="client", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="client", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="client", cascade="all, delete-orphan")


class ClientLocation(Base):
    """Client company locations with unique CCC (Código Cuenta Cotización)"""
    __tablename__ = 'client_locations'

    id = Column(Integer, primary_key=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    ccc_ss = Column(Text, unique=True, nullable=False)  # Código Cuenta Cotización / NAF

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="locations")
    employee_periods = relationship("EmployeePeriod", back_populates="location", cascade="all, delete-orphan")


class Employee(Base):
    """Employees - simplified model with only identity and contact information"""
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)

    # Identity fields
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    last_name2 = Column(Text)  # Spanish second surname
    identity_card_number = Column(Text, nullable=False)  # DNI/NIE
    identity_doc_type = Column(Text)  # 'DNI' or 'NIE'
    ss_number = Column(Text)  # Número Seguridad Social
    birth_date = Column(Date)

    # Contact information
    address = Column(Text)
    phone = Column(Text)
    mail = Column(Text)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    periods = relationship("EmployeePeriod", back_populates="employee", cascade="all, delete-orphan")
    payrolls = relationship("Payroll", back_populates="employee", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="employee", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="employee", cascade="all, delete-orphan")


class EmployeePeriod(Base):
    """
    Employment periods tracking ALTA, BAJA, and VACACIONES.
    Replaces the old vacation_periods table and employee begin_date/end_date fields.
    Each period represents an employment event or vacation period.
    """
    __tablename__ = 'employee_periods'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    location_id = Column(Integer, ForeignKey('client_locations.id', ondelete='CASCADE'), nullable=False)

    # Period dates
    period_begin_date = Column(Date, nullable=False)
    period_end_date = Column(Date, nullable=True)  # NULL for active/ongoing periods

    # Period type and details
    period_type = Column(Text, nullable=False)  # 'alta', 'baja', 'vacaciones'
    tipo_contrato = Column(Text)  # Contract type code for ALTA/BAJA periods

    # Employment details (can change per period)
    salary = Column(Numeric(12, 2))  # Salary for this period
    role = Column(Text)  # Job role for this period

    notes = Column(Text)  # Additional information

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="periods")
    location = relationship("ClientLocation", back_populates="employee_periods")


class NominaConcept(Base):
    """Spanish payroll concept codes dictionary"""
    __tablename__ = 'nomina_concepts'

    concept_code = Column(Text, primary_key=True)
    short_desc = Column(Text, nullable=False)
    long_desc = Column(Text)
    tributa_irpf = Column(Boolean, default=False)
    cotiza_ss = Column(Boolean, default=False)  # Simplified - cotiza Social Security
    en_especie = Column(Boolean, default=False)
    default_group = Column(Text)  # ordinaria, variable, especie, deduccion
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class Document(Base):
    """Documents with simple local file storage"""
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='CASCADE'))
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'))
    payroll_id = Column(Integer, ForeignKey('payrolls.id', ondelete='CASCADE'))

    # Document info
    document_type = Column(Text, nullable=False)  # payslip, contract, etc.
    original_filename = Column(Text)
    file_path = Column(Text, nullable=False)  # Relative path: documents/client_123/employee_456/file.pdf
    file_hash = Column(Text)
    file_size_bytes = Column(Integer)

    # Processing status
    received_at = Column(DateTime(timezone=True), default=func.now())
    processed_at = Column(DateTime(timezone=True))
    status = Column(Text, default='received')  # received, processing, processed, error

    # AI extraction results
    ocr_text = Column(Text)
    extraction_result = Column(JSON)  # Structured data extracted by AI
    extraction_confidence = Column(Numeric(3, 2))  # 0.00 to 1.00

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="documents")
    employee = relationship("Employee", back_populates="documents")
    payroll = relationship("Payroll", back_populates="documents")


class Payroll(Base):
    """Minimal payroll snapshot extracted from payslips"""
    __tablename__ = 'payrolls'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)

    type = Column(
        Enum("payslip", "settlement", "hybrid", name="payroll_type"),
        nullable=False,
        default="payslip",
    )

    # Period information stored as delivered by the extractor
    periodo = Column(JSON, nullable=False)


    # Totals captured explicitly to avoid nested JSON
    devengo_total = Column(Numeric(12, 2), nullable=False)
    deduccion_total = Column(Numeric(12, 2), nullable=False)
    aportacion_empresa_total =  Column(Numeric(12, 2), nullable=False)
    liquido_a_percibir =  Column(Numeric(12, 2), nullable=False)
    prorrata_pagas_extra =  Column(Numeric(12, 2), nullable=False)
    base_cc =  Column(Numeric(12, 2), nullable=False)
    base_at_ep =  Column(Numeric(12, 2), nullable=False)
    base_irpf =  Column(Numeric(12, 2), nullable=False)
    tipo_irpf =  Column(Numeric(5, 2), nullable=False)

    # Free-form warnings list serialized as text (JSON string or newline separated)
    warnings = Column(Text)

    # Metadata for merged payrolls (from multiple pages)
    is_merged = Column(Boolean, default=False)  # True if this payroll was merged from multiple parts
    merged_from_files = Column(Text)  # JSON array of source JSON filenames, if merged

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="payrolls")
    payroll_lines = relationship("PayrollLine", back_populates="payroll", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="payroll", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="payroll")


class PayrollLine(Base):
    """Simple payroll line item mirroring the extracted JSON arrays"""
    __tablename__ = 'payroll_lines'

    id = Column(Integer, primary_key=True)
    payroll_id = Column(Integer, ForeignKey('payrolls.id', ondelete='CASCADE'), nullable=False)
    category = Column(String, nullable=False)  # devengo, deduccion, aportacion_empresa
    concept = Column(Text, nullable=False)
    raw_concept = Column(Text)
    amount = Column(Numeric(12, 2), nullable=False)
    is_taxable_income = Column(Boolean, nullable=False)
    is_taxable_ss = Column(Boolean, nullable=False)
    is_sickpay = Column(Boolean, nullable=False)
    is_in_kind = Column(Boolean, nullable=False)
    is_pay_advance = Column(Boolean, nullable=False)
    is_seizure = Column(Boolean, nullable=False)
    

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    payroll = relationship("Payroll", back_populates="payroll_lines")


class ChecklistItem(Base):
    """Track missing documents and reminders"""
    __tablename__ = 'checklist_items'

    id = Column(Integer, primary_key=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'))
    payroll_id = Column(Integer, ForeignKey('payrolls.id', ondelete='SET NULL'))

    # What's needed
    item_type = Column(Text, nullable=False)  # payslip, contract, etc.
    description = Column(Text, nullable=False)
    period_year = Column(Integer)
    period_month = Column(Integer)
    due_date = Column(Date)

    # Status
    status = Column(Text, default='pending')  # pending, received, processed, validated
    priority = Column(Text, default='normal')  # high, normal, low

    # Communication tracking
    reminder_count = Column(Integer, default=0)
    last_reminder_sent_at = Column(DateTime(timezone=True))
    next_reminder_due_at = Column(DateTime(timezone=True))

    # Links
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='SET NULL'))

    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="checklist_items")
    employee = relationship("Employee", back_populates="checklist_items")
    payroll = relationship("Payroll", back_populates="checklist_items")


# ============================================================================
# Utility Functions for EmployeePeriod
# ============================================================================

def calculate_employee_status(employee_id: int, session) -> str:
    """
    Calculate employee status dynamically from periods.

    Returns:
        'Active' - if latest ALTA period has no end_date
        'Terminated' - if latest period is BAJA or has an end_date
        'Unknown' - if no periods exist
    """
    from sqlalchemy import desc

    latest_period = session.query(EmployeePeriod).filter(
        EmployeePeriod.employee_id == employee_id
    ).order_by(desc(EmployeePeriod.period_begin_date)).first()

    if not latest_period:
        return 'Unknown'

    # Active if it's an ALTA with no end date
    if latest_period.period_type == 'alta' and latest_period.period_end_date is None:
        return 'Active'

    # Terminated if it's a BAJA or has an end date
    if latest_period.period_type == 'baja' or latest_period.period_end_date is not None:
        return 'Terminated'

    return 'Unknown'


def get_employee_company(employee_id: int, session) -> str:
    """
    Get employee's current/most recent company ID.

    Returns:
        Company ID string or None if no periods exist
    """
    from sqlalchemy import desc

    period = session.query(EmployeePeriod).filter(
        EmployeePeriod.employee_id == employee_id
    ).order_by(desc(EmployeePeriod.period_begin_date)).first()

    return period.location.company_id if period else None


def get_active_employee_period(employee_id: int, session) -> EmployeePeriod:
    """
    Get the active employment period for an employee.

    Returns the most recent ALTA period with no end_date.
    """
    from sqlalchemy import desc

    return session.query(EmployeePeriod).filter(
        EmployeePeriod.employee_id == employee_id,
        EmployeePeriod.period_type == 'alta',
        EmployeePeriod.period_end_date is None
    ).order_by(desc(EmployeePeriod.period_begin_date)).first()
