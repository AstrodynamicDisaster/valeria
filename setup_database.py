#!/usr/bin/env python3
"""
ValerIA Simplified Database Setup Script
SQLAlchemy ORM-based database schema - Core essentials only
Focuses on AI processing workflow, payroll data, and Models 111/190 reporting
"""

import os
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric,
    String, Text, Index, UniqueConstraint, create_engine, text
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

# Core Database Models

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

    # Status
    active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="employees")
    payrolls = relationship("Payroll", back_populates="employee", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="employee", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="employee", cascade="all, delete-orphan")


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

    # Relationships
    payroll_lines = relationship("PayrollLine", back_populates="concept")


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
    """Payroll data extracted from payslips"""
    __tablename__ = 'payrolls'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)

    # Period info
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    pay_date = Column(Date)
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)
    period_quarter = Column(Integer, nullable=False)

    # Core amounts for Models 111/190
    bruto_total = Column(Numeric(10, 2))
    neto_total = Column(Numeric(10, 2))

    # IRPF data (critical for Models 111/190)
    irpf_base_monetaria = Column(Numeric(10, 2))
    irpf_base_especie = Column(Numeric(10, 2))
    irpf_retencion_monetaria = Column(Numeric(10, 2))
    irpf_retencion_especie = Column(Numeric(10, 2))

    # Social Security (simplified)
    ss_trabajador_total = Column(Numeric(10, 2))

    # Validation
    extraction_confidence = Column(Numeric(3, 2))
    validated_at = Column(DateTime(timezone=True))
    validated_by = Column(Text)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="payrolls")
    payroll_lines = relationship("PayrollLine", back_populates="payroll", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="payroll", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="payroll")


class PayrollLine(Base):
    """Individual line items from payslips"""
    __tablename__ = 'payroll_lines'

    id = Column(Integer, primary_key=True)
    payroll_id = Column(Integer, ForeignKey('payrolls.id', ondelete='CASCADE'), nullable=False)
    concept_code = Column(Text, ForeignKey('nomina_concepts.concept_code'))
    concept_desc = Column(Text, nullable=False)

    # Simplified flags
    is_devengo = Column(Boolean, default=True)
    is_deduccion = Column(Boolean, default=False)
    tributa_irpf = Column(Boolean, default=False)
    en_especie = Column(Boolean, default=False)

    # Amounts
    units = Column(Numeric(10, 4))
    importe_devengo = Column(Numeric(10, 2))
    importe_deduccion = Column(Numeric(10, 2))

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    payroll = relationship("Payroll", back_populates="payroll_lines")
    concept = relationship("NominaConcept", back_populates="payroll_lines")


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


# Simple Document Storage Utilities

def ensure_documents_directory():
    """Create documents directory structure if it doesn't exist"""
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


# Basic Vida Laboral CSV Import

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


# Seed Data

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


# Database Setup Functions

def create_database_engine(database_url: str = None, echo: bool = True):
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


def create_tables(engine):
    """Create all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("✓ Database tables created successfully!")


def create_indexes(engine):
    """Create performance indexes"""
    print("Creating database indexes...")

    indexes = [
        Index('idx_employees_company_id', Employee.company_id),  # Updated from client_id
        Index('idx_employees_identity_card', Employee.identity_card_number),  # Updated from documento
        Index('idx_employees_active', Employee.active),
        Index('idx_documents_client_id', Document.client_id),
        Index('idx_documents_employee_id', Document.employee_id),
        Index('idx_documents_status', Document.status),
        Index('idx_payrolls_employee_id', Payroll.employee_id),
        Index('idx_payrolls_period', Payroll.period_year, Payroll.period_month),
        Index('idx_payrolls_validated', Payroll.validated_at),
        Index('idx_payroll_lines_payroll_id', PayrollLine.payroll_id),
        Index('idx_checklist_items_client_id', ChecklistItem.client_id),
        Index('idx_checklist_items_status', ChecklistItem.status),
        Index('idx_checklist_items_due_date', ChecklistItem.due_date),
    ]

    with engine.connect() as conn:
        for index in indexes:
            try:
                index.create(engine)
            except Exception as e:
                if 'already exists' not in str(e).lower():
                    print(f"Warning: Could not create index {index.name}: {e}")

    print("✓ Database indexes created successfully!")


def seed_nomina_concepts(engine):
    """Insert basic nomina concepts"""
    print("Seeding nomina_concepts table...")

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        existing_count = session.query(NominaConcept).count()
        if existing_count > 0:
            print(f"✓ Nomina concepts already exist ({existing_count} concepts), skipping seed.")
            return

        for concept_data in BASIC_NOMINA_CONCEPTS:
            concept = NominaConcept(**concept_data)
            session.add(concept)

        session.commit()
        print(f"✓ Seeded {len(BASIC_NOMINA_CONCEPTS)} nomina concepts successfully!")

    except Exception as e:
        session.rollback()
        print(f"✗ Error seeding nomina concepts: {e}")
        raise
    finally:
        session.close()


def create_basic_views(engine):
    """Create essential views for reporting"""
    print("Creating database views...")

    views = [
        # Payroll completeness for missing document detection
        """
        CREATE OR REPLACE VIEW payroll_completeness AS
        SELECT
            e.company_id,
            e.id as employee_id,
            CONCAT(e.first_name, ' ', e.last_name, COALESCE(' ' || e.last_name2, '')) as full_name,
            years.period_year,
            COUNT(p.id) as payrolls_received,
            12 - COUNT(p.id) as payrolls_missing,
            CASE WHEN COUNT(p.id) = 12 THEN true ELSE false END as complete_year
        FROM employees e
        CROSS JOIN generate_series(2023, EXTRACT(YEAR FROM NOW())::int) as years(period_year)
        LEFT JOIN payrolls p ON e.id = p.employee_id AND p.period_year = years.period_year
        WHERE e.active = true
        GROUP BY e.company_id, e.id, e.first_name, e.last_name, e.last_name2, years.period_year
        ORDER BY e.company_id, full_name, years.period_year;
        """,

        # Model 111 quarterly data
        """
        CREATE OR REPLACE VIEW model111_quarterly_data AS
        SELECT
            c.id as client_id,
            c.name as fiscal_name,
            c.cif,
            p.period_year,
            p.period_quarter,
            COUNT(DISTINCT e.id) as employee_count,
            COUNT(p.id) as payroll_count,
            SUM(COALESCE(p.irpf_base_monetaria, 0) + COALESCE(p.irpf_base_especie, 0)) as base_irpf_total,
            SUM(COALESCE(p.irpf_retencion_monetaria, 0) + COALESCE(p.irpf_retencion_especie, 0)) as retencion_irpf_total
        FROM clients c
        JOIN employees e ON c.id = e.company_id
        JOIN payrolls p ON e.id = p.employee_id
        WHERE c.active = true AND e.active = true AND p.validated_at IS NOT NULL
        GROUP BY c.id, c.name, c.cif, p.period_year, p.period_quarter
        ORDER BY c.name, p.period_year, p.period_quarter;
        """
    ]

    with engine.connect() as conn:
        for view_sql in views:
            try:
                conn.execute(text(view_sql))
            except Exception as e:
                print(f"Warning: Could not create view: {e}")

    print("✓ Database views created successfully!")


def setup_timezone(engine):
    """Set database timezone"""
    print("Setting database timezone to Europe/Madrid...")
    with engine.connect() as conn:
        conn.execute(text("SET timezone = 'Europe/Madrid';"))
    print("✓ Database timezone set successfully!")


def main():
    """Main setup function"""
    print("🚀 Starting ValerIA Simplified Database Setup...")
    print("=" * 50)

    try:
        # Create database engine
        engine = create_database_engine()
        print("✓ Database connection established!")

        # Setup
        setup_timezone(engine)
        create_tables(engine)
        create_indexes(engine)
        seed_nomina_concepts(engine)
        create_basic_views(engine)

        # Create documents directory
        ensure_documents_directory()
        print("✓ Documents directory created!")

        print("=" * 50)
        print("🎉 ValerIA Simplified Database Setup Completed!")
        print("\nCore features ready:")
        print("- AI document processing workflow")
        print("- Payroll data extraction")
        print("- Missing document detection")
        print("- Models 111/190 reporting")
        print("- Local file storage")

        return 0

    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())