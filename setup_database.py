#!/usr/bin/env python3
"""
ValerIA Database Setup Script
SQLAlchemy ORM-based database schema creation for payroll onboarding automation
Based on ValerIA_Onboarding_Automation_Spec.md
"""

import os
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric,
    String, Text, Index, UniqueConstraint, create_engine, text
)
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMPTZ
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

# Database Models

class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    fiscal_name = Column(Text, nullable=False)
    nif = Column(Text, unique=True, nullable=False)
    ccc_ss = Column(Text)  # Código Cuenta Cotización Seguridad Social
    contact_emails = Column(ARRAY(Text))
    active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMPTZ, default=func.now())
    updated_at = Column(TIMESTAMPTZ, default=func.now(), onupdate=func.now())

    # Relationships
    contacts = relationship("ClientContact", back_populates="client", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="client", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="client", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="client", cascade="all, delete-orphan")
    model111_quarterly = relationship("Model111Quarterly", back_populates="client", cascade="all, delete-orphan")
    model190_annual_detail = relationship("Model190AnnualDetail", back_populates="client", cascade="all, delete-orphan")
    model190_annual_summary = relationship("Model190AnnualSummary", back_populates="client", cascade="all, delete-orphan")


class ClientContact(Base):
    __tablename__ = 'client_contacts'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    full_name = Column(Text, nullable=False)
    email = Column(Text)
    phone = Column(Text)
    role = Column(Text)  # Account Manager, HR, etc.
    is_primary = Column(Boolean, default=False)
    created_at = Column(TIMESTAMPTZ, default=func.now())
    updated_at = Column(TIMESTAMPTZ, default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="contacts")


class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    full_name = Column(Text, nullable=False)
    nif = Column(Text)
    nss = Column(Text)  # Número Seguridad Social
    date_of_birth = Column(Date)
    active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMPTZ, default=func.now())
    updated_at = Column(TIMESTAMPTZ, default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="employees")
    employment_periods = relationship("EmploymentPeriod", back_populates="employee", cascade="all, delete-orphan")
    payrolls = relationship("Payroll", back_populates="employee", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="employee", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="employee", cascade="all, delete-orphan")
    model190_annual_detail = relationship("Model190AnnualDetail", back_populates="employee", cascade="all, delete-orphan")


class EmploymentPeriod(Base):
    __tablename__ = 'employment_periods'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    alta_date = Column(Date, nullable=False)
    baja_date = Column(Date)
    contract_type = Column(Text)  # Indefinido, Temporal, etc.
    jornada_type = Column(Text)   # Completa, Parcial
    jornada_pct = Column(Numeric(5, 2))  # Percentage of full-time
    notes = Column(Text)
    created_at = Column(TIMESTAMPTZ, default=func.now())
    updated_at = Column(TIMESTAMPTZ, default=func.now(), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="employment_periods")
    payrolls = relationship("Payroll", back_populates="employment_period")


class NominaConcept(Base):
    __tablename__ = 'nomina_concepts'

    concept_code = Column(Text, primary_key=True)
    short_desc = Column(Text, nullable=False)
    long_desc = Column(Text)
    tributa_irpf = Column(Boolean, default=False)
    cotiza_cc = Column(Boolean, default=False)  # Cotiza Contingencias Comunes
    cotiza_cp = Column(Boolean, default=False)  # Cotiza Contingencias Profesionales
    en_especie = Column(Boolean, default=False)
    default_group = Column(Text)  # ordinaria, variable, especie, deduccion, indemnizacion
    model190_box = Column(Text)   # For Model 190 mapping
    is_devengo = Column(Boolean, default=True)
    is_deduccion = Column(Boolean, default=False)
    created_at = Column(TIMESTAMPTZ, default=func.now())
    updated_at = Column(TIMESTAMPTZ, default=func.now(), onupdate=func.now())

    # Relationships
    payroll_lines = relationship("PayrollLine", back_populates="concept")


class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'))
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'))
    payroll_id = Column(Integer, ForeignKey('payrolls.id', ondelete='CASCADE'))
    document_type = Column(Text, nullable=False)  # payslip, contract, ID, etc.
    original_filename = Column(Text)
    storage_uri = Column(Text, nullable=False)
    file_hash = Column(Text)
    file_size_bytes = Column(Integer)
    mime_type = Column(Text)
    received_at = Column(TIMESTAMPTZ, default=func.now())
    processed_at = Column(TIMESTAMPTZ)
    status = Column(Text, default='received')  # received, processing, processed, error
    ocr_text = Column(Text)
    extraction_metadata = Column(JSON)
    error_details = Column(Text)
    created_at = Column(TIMESTAMPTZ, default=func.now())
    updated_at = Column(TIMESTAMPTZ, default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="documents")
    employee = relationship("Employee", back_populates="documents")
    payroll = relationship("Payroll", back_populates="documents")


class Payroll(Base):
    __tablename__ = 'payrolls'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    employment_period_id = Column(Integer, ForeignKey('employment_periods.id', ondelete='SET NULL'))
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    pay_date = Column(Date)
    # Generated columns - SQLAlchemy doesn't support GENERATED ALWAYS AS, so we'll use properties
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)
    period_quarter = Column(Integer, nullable=False)

    # Totals
    bruto_total = Column(Numeric(10, 2))
    neto_total = Column(Numeric(10, 2))

    # IRPF bases and withholdings
    irpf_base_monetaria = Column(Numeric(10, 2))
    irpf_base_especie = Column(Numeric(10, 2))
    irpf_retencion_monetaria = Column(Numeric(10, 2))
    irpf_retencion_especie = Column(Numeric(10, 2))

    # Social Security
    ss_trabajador_total = Column(Numeric(10, 2))
    base_cc = Column(Numeric(10, 2))  # Base Contingencias Comunes (excludes overtime)
    base_cp = Column(Numeric(10, 2))  # Base Contingencias Profesionales (includes overtime)

    # Special items
    indemnizacion = Column(Numeric(10, 2))

    # Additional data
    extra_json = Column(JSON)

    # Audit
    extraction_confidence = Column(Numeric(3, 2))  # 0.00 to 1.00
    validated_at = Column(TIMESTAMPTZ)
    validated_by = Column(Text)

    created_at = Column(TIMESTAMPTZ, default=func.now())
    updated_at = Column(TIMESTAMPTZ, default=func.now(), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="payrolls")
    employment_period = relationship("EmploymentPeriod", back_populates="payrolls")
    payroll_lines = relationship("PayrollLine", back_populates="payroll", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="payroll", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="payroll")


class PayrollLine(Base):
    __tablename__ = 'payroll_lines'

    id = Column(Integer, primary_key=True)
    payroll_id = Column(Integer, ForeignKey('payrolls.id', ondelete='CASCADE'), nullable=False)
    concept_code = Column(Text, ForeignKey('nomina_concepts.concept_code'))
    concept_desc = Column(Text, nullable=False)

    # Flags (can override concept defaults)
    is_devengo = Column(Boolean, default=True)
    is_deduccion = Column(Boolean, default=False)
    tributa_irpf = Column(Boolean, default=False)
    cotiza_cc = Column(Boolean, default=False)
    cotiza_cp = Column(Boolean, default=False)
    en_especie = Column(Boolean, default=False)

    # Amounts
    units = Column(Numeric(10, 4))
    importe_devengo = Column(Numeric(10, 2))
    importe_deduccion = Column(Numeric(10, 2))

    created_at = Column(TIMESTAMPTZ, default=func.now())
    updated_at = Column(TIMESTAMPTZ, default=func.now(), onupdate=func.now())

    # Relationships
    payroll = relationship("Payroll", back_populates="payroll_lines")
    concept = relationship("NominaConcept", back_populates="payroll_lines")


class ChecklistItem(Base):
    __tablename__ = 'checklist_items'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'))
    payroll_id = Column(Integer, ForeignKey('payrolls.id', ondelete='SET NULL'))

    # What's required
    item_type = Column(Text, nullable=False)  # payslip, contract, etc.
    description = Column(Text, nullable=False)
    period_year = Column(Integer)
    period_month = Column(Integer)
    due_date = Column(Date)

    # Status tracking
    status = Column(Text, default='pending')  # pending, received, processed, validated, missing
    priority = Column(Text, default='normal')  # high, normal, low

    # Communication
    reminder_count = Column(Integer, default=0)
    last_reminder_sent_at = Column(TIMESTAMPTZ)
    next_reminder_due_at = Column(TIMESTAMPTZ)

    # Links
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='SET NULL'))

    # Notes
    notes = Column(Text)
    assigned_to = Column(Text)

    created_at = Column(TIMESTAMPTZ, default=func.now())
    updated_at = Column(TIMESTAMPTZ, default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="checklist_items")
    employee = relationship("Employee", back_populates="checklist_items")
    payroll = relationship("Payroll", back_populates="checklist_items")


class Model111Quarterly(Base):
    __tablename__ = 'model111_quarterly'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)

    # Aggregated totals
    base_irpf_total = Column(Numeric(12, 2))
    retencion_irpf_total = Column(Numeric(12, 2))

    # Metadata
    employee_count = Column(Integer)
    payroll_count = Column(Integer)
    generated_at = Column(TIMESTAMPTZ, default=func.now())
    reviewed_at = Column(TIMESTAMPTZ)
    reviewed_by = Column(Text)

    created_at = Column(TIMESTAMPTZ, default=func.now())
    updated_at = Column(TIMESTAMPTZ, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('client_id', 'year', 'quarter', name='uq_model111_client_year_quarter'),
    )

    # Relationships
    client = relationship("Client", back_populates="model111_quarterly")


class Model190AnnualDetail(Base):
    __tablename__ = 'model190_annual_detail'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    year = Column(Integer, nullable=False)

    # Employee info
    employee_nif = Column(Text)
    employee_full_name = Column(Text)

    # Annual totals per employee
    percepciones_monetarias = Column(Numeric(12, 2))  # Monetary perceptions
    percepciones_especie = Column(Numeric(12, 2))     # In-kind perceptions
    percepciones_it = Column(Numeric(12, 2))          # IT perceptions (no company complements)
    retenciones_irpf = Column(Numeric(12, 2))         # IRPF withholdings
    indemnizaciones = Column(Numeric(12, 2))          # Severance payments
    ss_trabajador_informative = Column(Numeric(12, 2)) # SS worker contribution (informative)

    # Metadata
    payroll_count = Column(Integer)
    generated_at = Column(TIMESTAMPTZ, default=func.now())
    reviewed_at = Column(TIMESTAMPTZ)
    reviewed_by = Column(Text)

    created_at = Column(TIMESTAMPTZ, default=func.now())
    updated_at = Column(TIMESTAMPTZ, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('client_id', 'employee_id', 'year', name='uq_model190_detail_client_employee_year'),
    )

    # Relationships
    client = relationship("Client", back_populates="model190_annual_detail")
    employee = relationship("Employee", back_populates="model190_annual_detail")


class Model190AnnualSummary(Base):
    __tablename__ = 'model190_annual_summary'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    year = Column(Integer, nullable=False)

    # Summary totals
    total_employees = Column(Integer)
    total_percepciones_monetarias = Column(Numeric(12, 2))
    total_percepciones_especie = Column(Numeric(12, 2))
    total_percepciones_it = Column(Numeric(12, 2))
    total_retenciones_irpf = Column(Numeric(12, 2))
    total_indemnizaciones = Column(Numeric(12, 2))

    # Metadata
    generated_at = Column(TIMESTAMPTZ, default=func.now())
    reviewed_at = Column(TIMESTAMPTZ)
    reviewed_by = Column(Text)

    created_at = Column(TIMESTAMPTZ, default=func.now())
    updated_at = Column(TIMESTAMPTZ, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('client_id', 'year', name='uq_model190_summary_client_year'),
    )

    # Relationships
    client = relationship("Client", back_populates="model190_annual_summary")


# Seed data for nomina_concepts
NOMINA_CONCEPTS_SEED = [
    # Ordinary monetary concepts (001-399)
    {
        'concept_code': '001',
        'short_desc': 'Salario base',
        'long_desc': 'Salario base mensual',
        'tributa_irpf': True,
        'cotiza_cc': True,
        'cotiza_cp': True,
        'en_especie': False,
        'default_group': 'ordinaria',
        'model190_box': 'monetary'
    },
    {
        'concept_code': '002',
        'short_desc': 'Antigüedad',
        'long_desc': 'Plus por antigüedad',
        'tributa_irpf': True,
        'cotiza_cc': True,
        'cotiza_cp': True,
        'en_especie': False,
        'default_group': 'ordinaria',
        'model190_box': 'monetary'
    },
    {
        'concept_code': '003',
        'short_desc': 'Pagas extras',
        'long_desc': 'Pagas extraordinarias prorrateadas',
        'tributa_irpf': True,
        'cotiza_cc': True,
        'cotiza_cp': True,
        'en_especie': False,
        'default_group': 'ordinaria',
        'model190_box': 'monetary'
    },
    {
        'concept_code': '120',
        'short_desc': 'Plus convenio',
        'long_desc': 'Plus de convenio colectivo',
        'tributa_irpf': True,
        'cotiza_cc': True,
        'cotiza_cp': True,
        'en_especie': False,
        'default_group': 'ordinaria',
        'model190_box': 'monetary'
    },
    {
        'concept_code': '130',
        'short_desc': 'Plus nocturnidad',
        'long_desc': 'Plus por trabajo nocturno',
        'tributa_irpf': True,
        'cotiza_cc': True,
        'cotiza_cp': True,
        'en_especie': False,
        'default_group': 'ordinaria',
        'model190_box': 'monetary'
    },
    {
        'concept_code': '140',
        'short_desc': 'Plus festivos',
        'long_desc': 'Plus por trabajo en festivos',
        'tributa_irpf': True,
        'cotiza_cc': True,
        'cotiza_cp': True,
        'en_especie': False,
        'default_group': 'ordinaria',
        'model190_box': 'monetary'
    },
    # Variable concepts (300-399)
    {
        'concept_code': '301',
        'short_desc': 'Horas extra',
        'long_desc': 'Horas extraordinarias',
        'tributa_irpf': True,
        'cotiza_cc': False,
        'cotiza_cp': True,
        'en_especie': False,
        'default_group': 'variable',
        'model190_box': 'monetary'
    },
    {
        'concept_code': '302',
        'short_desc': 'Comisiones',
        'long_desc': 'Comisiones sobre ventas',
        'tributa_irpf': True,
        'cotiza_cc': True,
        'cotiza_cp': True,
        'en_especie': False,
        'default_group': 'variable',
        'model190_box': 'monetary'
    },
    {
        'concept_code': '310',
        'short_desc': 'Productividad',
        'long_desc': 'Incentivos por productividad',
        'tributa_irpf': True,
        'cotiza_cc': True,
        'cotiza_cp': True,
        'en_especie': False,
        'default_group': 'variable',
        'model190_box': 'monetary'
    },
    {
        'concept_code': '320',
        'short_desc': 'Kilometraje',
        'long_desc': 'Indemnización kilometraje coche propio',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'variable',
        'model190_box': 'exempt'
    },
    # Vacation and special payments (400-499)
    {
        'concept_code': '401',
        'short_desc': 'Vacaciones',
        'long_desc': 'Vacaciones no disfrutadas',
        'tributa_irpf': True,
        'cotiza_cc': True,
        'cotiza_cp': True,
        'en_especie': False,
        'default_group': 'ordinaria',
        'model190_box': 'monetary'
    },
    {
        'concept_code': '450',
        'short_desc': 'IT común',
        'long_desc': 'Incapacidad Temporal contingencias comunes',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'it',
        'model190_box': 'it'
    },
    {
        'concept_code': '451',
        'short_desc': 'IT profesional',
        'long_desc': 'Incapacidad Temporal contingencias profesionales',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'it',
        'model190_box': 'it'
    },
    # In-kind benefits (600-699)
    {
        'concept_code': '601',
        'short_desc': 'Seguro médico',
        'long_desc': 'Seguro médico privado',
        'tributa_irpf': True,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': True,
        'default_group': 'especie',
        'model190_box': 'in_kind'
    },
    {
        'concept_code': '610',
        'short_desc': 'Dietas exentas',
        'long_desc': 'Dietas de viaje exentas de tributación',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'especie',
        'model190_box': 'exempt'
    },
    {
        'concept_code': '620',
        'short_desc': 'Ticket restaurant',
        'long_desc': 'Ticket restaurant',
        'tributa_irpf': True,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': True,
        'default_group': 'especie',
        'model190_box': 'in_kind'
    },
    {
        'concept_code': '630',
        'short_desc': 'Coche empresa',
        'long_desc': 'Uso privado vehículo empresa',
        'tributa_irpf': True,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': True,
        'default_group': 'especie',
        'model190_box': 'in_kind'
    },
    {
        'concept_code': '640',
        'short_desc': 'Formación',
        'long_desc': 'Gastos de formación',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'especie',
        'model190_box': 'exempt'
    },
    # Deductions (700-799)
    {
        'concept_code': '700',
        'short_desc': 'IRPF',
        'long_desc': 'Retención IRPF',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'deduccion',
        'model190_box': None,
        'is_devengo': False,
        'is_deduccion': True
    },
    {
        'concept_code': '730',
        'short_desc': 'SS Trabajador CC',
        'long_desc': 'Seguridad Social Contingencias Comunes',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'deduccion',
        'model190_box': None,
        'is_devengo': False,
        'is_deduccion': True
    },
    {
        'concept_code': '731',
        'short_desc': 'SS Trabajador CP',
        'long_desc': 'Seguridad Social Contingencias Profesionales',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'deduccion',
        'model190_box': None,
        'is_devengo': False,
        'is_deduccion': True
    },
    {
        'concept_code': '732',
        'short_desc': 'SS Trabajador Desempleo',
        'long_desc': 'Seguridad Social Desempleo',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'deduccion',
        'model190_box': None,
        'is_devengo': False,
        'is_deduccion': True
    },
    {
        'concept_code': '733',
        'short_desc': 'SS Trabajador FP',
        'long_desc': 'Seguridad Social Formación Profesional',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'deduccion',
        'model190_box': None,
        'is_devengo': False,
        'is_deduccion': True
    },
    {
        'concept_code': '740',
        'short_desc': 'Anticipos',
        'long_desc': 'Anticipos de nómina',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'deduccion',
        'model190_box': None,
        'is_devengo': False,
        'is_deduccion': True
    },
    {
        'concept_code': '750',
        'short_desc': 'Embargo',
        'long_desc': 'Retención judicial',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'deduccion',
        'model190_box': None,
        'is_devengo': False,
        'is_deduccion': True
    },
    # Severance payments (900-999)
    {
        'concept_code': '900',
        'short_desc': 'Indemnización despido',
        'long_desc': 'Indemnización por despido',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'indemnizacion',
        'model190_box': 'severance'
    },
    {
        'concept_code': '901',
        'short_desc': 'Indemnización traslado',
        'long_desc': 'Indemnización por traslado',
        'tributa_irpf': False,
        'cotiza_cc': False,
        'cotiza_cp': False,
        'en_especie': False,
        'default_group': 'indemnizacion',
        'model190_box': 'severance'
    },
    {
        'concept_code': '910',
        'short_desc': 'Finiquito',
        'long_desc': 'Liquidación al cese',
        'tributa_irpf': True,
        'cotiza_cc': True,
        'cotiza_cp': True,
        'en_especie': False,
        'default_group': 'indemnizacion',
        'model190_box': 'severance'
    }
]


def create_database_engine(database_url: str = None):
    """Create database engine from environment variables or provided URL"""
    if database_url is None:
        # Get connection parameters from environment or use defaults matching docker-compose.yml
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DB', 'valeria')
        db_user = os.getenv('POSTGRES_USER', 'valeria')
        db_password = os.getenv('POSTGRES_PASSWORD', 'changeme')

        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    engine = create_engine(database_url, echo=True)
    return engine


def create_tables(engine):
    """Create all tables in the database"""
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("✓ Database tables created successfully!")


def create_indexes(engine):
    """Create additional indexes for performance"""
    print("Creating database indexes...")

    indexes = [
        # Employee indexes
        Index('idx_employees_client_id', Employee.client_id),
        Index('idx_employees_active', Employee.active),
        Index('idx_employees_nif', Employee.nif),

        # Employment periods
        Index('idx_employment_periods_employee_id', EmploymentPeriod.employee_id),
        Index('idx_employment_periods_dates', EmploymentPeriod.alta_date, EmploymentPeriod.baja_date),

        # Documents
        Index('idx_documents_client_id', Document.client_id),
        Index('idx_documents_employee_id', Document.employee_id),
        Index('idx_documents_status', Document.status),
        Index('idx_documents_type', Document.document_type),

        # Payrolls
        Index('idx_payrolls_employee_id', Payroll.employee_id),
        Index('idx_payrolls_period', Payroll.period_year, Payroll.period_month),
        Index('idx_payrolls_client_period', Payroll.employee_id, Payroll.period_year, Payroll.period_month),
        Index('idx_payrolls_validated', Payroll.validated_at),

        # Payroll lines
        Index('idx_payroll_lines_payroll_id', PayrollLine.payroll_id),
        Index('idx_payroll_lines_concept', PayrollLine.concept_code),

        # Checklist items
        Index('idx_checklist_items_client_id', ChecklistItem.client_id),
        Index('idx_checklist_items_employee_id', ChecklistItem.employee_id),
        Index('idx_checklist_items_status', ChecklistItem.status),
        Index('idx_checklist_items_due_date', ChecklistItem.due_date),
        Index('idx_checklist_items_reminder_due', ChecklistItem.next_reminder_due_at),

        # Model 111
        Index('idx_model111_client_period', Model111Quarterly.client_id, Model111Quarterly.year, Model111Quarterly.quarter),

        # Model 190
        Index('idx_model190_detail_client_year', Model190AnnualDetail.client_id, Model190AnnualDetail.year),
        Index('idx_model190_summary_client_year', Model190AnnualSummary.client_id, Model190AnnualSummary.year),
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
    """Insert seed data for nomina_concepts table"""
    print("Seeding nomina_concepts table...")

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check if concepts already exist
        existing_count = session.query(NominaConcept).count()
        if existing_count > 0:
            print(f"✓ Nomina concepts already exist ({existing_count} concepts), skipping seed.")
            return

        # Insert seed data
        for concept_data in NOMINA_CONCEPTS_SEED:
            concept = NominaConcept(**concept_data)
            session.add(concept)

        session.commit()
        print(f"✓ Seeded {len(NOMINA_CONCEPTS_SEED)} nomina concepts successfully!")

    except Exception as e:
        session.rollback()
        print(f"✗ Error seeding nomina concepts: {e}")
        raise
    finally:
        session.close()


def create_views(engine):
    """Create useful database views"""
    print("Creating database views...")

    views = [
        # Active employees with current employment period
        """
        CREATE OR REPLACE VIEW active_employees_current AS
        SELECT
            e.*,
            ep.alta_date,
            ep.baja_date,
            ep.contract_type,
            ep.jornada_type,
            ep.jornada_pct,
            c.fiscal_name as client_name,
            c.nif as client_nif
        FROM employees e
        JOIN clients c ON e.client_id = c.id
        LEFT JOIN employment_periods ep ON e.id = ep.employee_id
            AND ep.baja_date IS NULL  -- Current employment period
        WHERE e.active = true
            AND c.active = true;
        """,

        # Payroll completeness by employee and year
        """
        CREATE OR REPLACE VIEW payroll_completeness AS
        SELECT
            e.client_id,
            e.id as employee_id,
            e.full_name,
            years.period_year,
            COUNT(p.id) as payrolls_received,
            12 - COUNT(p.id) as payrolls_missing,
            CASE WHEN COUNT(p.id) = 12 THEN true ELSE false END as complete_year,
            ARRAY_AGG(p.period_month ORDER BY p.period_month) as months_received
        FROM employees e
        CROSS JOIN generate_series(2023, EXTRACT(YEAR FROM NOW())::int) as years(period_year)
        LEFT JOIN payrolls p ON e.id = p.employee_id
            AND p.period_year = years.period_year
        WHERE e.active = true
        GROUP BY e.client_id, e.id, e.full_name, years.period_year
        ORDER BY e.client_id, e.full_name, years.period_year;
        """,

        # Model 111 quarterly aggregations (ready to generate)
        """
        CREATE OR REPLACE VIEW model111_quarterly_ready AS
        SELECT
            c.id as client_id,
            c.fiscal_name,
            c.nif,
            p.period_year,
            p.period_quarter,
            COUNT(DISTINCT e.id) as employee_count,
            COUNT(p.id) as payroll_count,
            SUM(p.irpf_base_monetaria + COALESCE(p.irpf_base_especie, 0)) as base_irpf_total,
            SUM(p.irpf_retencion_monetaria + COALESCE(p.irpf_retencion_especie, 0)) as retencion_irpf_total
        FROM clients c
        JOIN employees e ON c.id = e.client_id
        JOIN payrolls p ON e.id = p.employee_id
        WHERE c.active = true
            AND e.active = true
            AND p.validated_at IS NOT NULL  -- Only validated payrolls
        GROUP BY c.id, c.fiscal_name, c.nif, p.period_year, p.period_quarter
        ORDER BY c.fiscal_name, p.period_year, p.period_quarter;
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
    """Set database timezone to Europe/Madrid as specified"""
    print("Setting database timezone to Europe/Madrid...")

    with engine.connect() as conn:
        conn.execute(text("SET timezone = 'Europe/Madrid';"))

    print("✓ Database timezone set successfully!")


def main():
    """Main setup function"""
    print("🚀 Starting ValerIA Database Setup...")
    print("=" * 50)

    # Create database engine
    try:
        engine = create_database_engine()
        print("✓ Database connection established!")
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        print("Make sure PostgreSQL is running and environment variables are set correctly.")
        return 1

    try:
        # Setup timezone
        setup_timezone(engine)

        # Create tables
        create_tables(engine)

        # Create indexes
        create_indexes(engine)

        # Seed data
        seed_nomina_concepts(engine)

        # Create views
        create_views(engine)

        print("=" * 50)
        print("🎉 ValerIA Database Setup Completed Successfully!")
        print("\nNext steps:")
        print("1. Start your n8n workflows")
        print("2. Configure your environment variables")
        print("3. Begin onboarding clients")

        return 0

    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())