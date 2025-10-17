#!/usr/bin/env python3
"""
ValerIA Core Database Models
SQLAlchemy ORM models for the payroll processing workflow.
These models are used at runtime by the application.
"""

from datetime import datetime
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric,
    String, Text
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Client(Base):
    """Client companies using payroll services - matches production 'companies' table schema"""
    __tablename__ = 'clients'

    id = Column(String, primary_key=True)  # UUID string to match production
    name = Column(Text, nullable=False)  # Was fiscal_name
    cif = Column(Text, unique=True, nullable=False)  # Was nif
    fiscal_address = Column(Text)
    email = Column(Text)
    phone = Column(Text)
    ccc_ss = Column(Text)  # Código Cuenta Cotización Seguridad Social (local only)
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
    employees = relationship("Employee", back_populates="client", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="client", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="client", cascade="all, delete-orphan")


class Employee(Base):
    """Employees of client companies - matches production 'company_employees' table schema"""
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    company_id = Column(String, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)  # Was client_id

    # Identity fields (matching production)
    first_name = Column(Text, nullable=False)  # Split from full_name
    last_name = Column(Text, nullable=False)   # Split from full_name
    last_name2 = Column(Text)                  # Spanish second surname
    identity_card_number = Column(Text, nullable=False)  # Was documento (DNI/NIE)
    identity_doc_type = Column(Text)  # 'DNI' or 'NIE'
    ss_number = Column(Text)  # Was nss (Número Seguridad Social)
    birth_date = Column(Date)  # Was date_of_birth

    # Contact information
    address = Column(Text)
    phone = Column(Text)
    mail = Column(Text)

    # Employment details
    begin_date = Column(Date)  # Was employment_start_date
    end_date = Column(Date)    # Was employment_end_date
    salary = Column(Numeric(10, 2))
    role = Column(Text)
    employee_status = Column(Text)  # 'Active', 'Terminated', etc.
    tipo_contrato = Column(Text)  # Contract type code (e.g., '100', '200') from vida laboral TC field

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="employees")
    payrolls = relationship("Payroll", back_populates="employee", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="employee", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="employee", cascade="all, delete-orphan")
    vacation_periods = relationship("VacationPeriod", back_populates="employee", cascade="all, delete-orphan")


class VacationPeriod(Base):
    """
    Vacation and unpaid leave periods for employees (VAC.RETRIB.NO from vida laboral).
    Stores periods where employee was on vacation or unpaid leave within an employment period.
    """
    __tablename__ = 'vacation_periods'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)

    # Date range for vacation
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)  # Nullable for ongoing vacations

    # Type and metadata
    vacation_type = Column(Text, default='VAC.RETRIB.NO')  # VAC.RETRIB.NO, PERMISO, etc.
    notes = Column(Text)  # Additional information from CSV

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="vacation_periods")


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
    client_id = Column(String, ForeignKey('clients.id', ondelete='CASCADE'))  # Updated to String
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

    # Period information stored as delivered by the extractor
    periodo = Column(JSON, nullable=False)

    # Totals captured explicitly to avoid nested JSON
    devengo_total = Column(Numeric(10, 2), nullable=True)
    deduccion_total = Column(Numeric(10, 2), nullable=True)
    aportacion_empresa_total = Column(Numeric(10, 2), nullable=True)
    liquido_a_percibir = Column(Numeric(10, 2), nullable=True)

    # Free-form warnings list serialized as text (JSON string or newline separated)
    warnings = Column(Text)

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
    concepto = Column(Text, nullable=False)
    importe = Column(Numeric(10, 2), nullable=False)
    base = Column(Numeric(10, 2))
    tipo = Column(Numeric(6, 2))

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    payroll = relationship("Payroll", back_populates="payroll_lines")


class ChecklistItem(Base):
    """Track missing documents and reminders"""
    __tablename__ = 'checklist_items'

    id = Column(Integer, primary_key=True)
    client_id = Column(String, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)  # Updated to String
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
