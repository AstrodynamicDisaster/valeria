#!/usr/bin/env python3
"""
ValerIA Core Module
Runtime database models and utilities for the payroll processing workflow.
"""

# Models
from .models import (
    Base,
    Client,
    Employee,
    NominaConcept,
    Document,
    Payroll,
    PayrollLine,
    ChecklistItem
)

# Database utilities
from .database import (
    create_database_engine,
    ensure_documents_directory,
    get_client_document_path,
    get_employee_document_path,
    save_document_file,
    load_document_file,
    parse_vida_laboral_csv_simple,
    BASIC_NOMINA_CONCEPTS
)

# Production models (read-only)
from .production_models import (
    ProductionBase,
    ProductionCompany,
    ProductionEmployee,
    create_production_engine,
    create_production_session,
    get_production_company_by_cif,
    get_production_company_by_id,
    get_production_employee_by_identity_card,
    list_production_employees_for_company
)

# Main application modules
from .valeria_agent import ValeriaAgent
from .process_payroll import extract_payroll_info

__all__ = [
    # Models
    'Base',
    'Client',
    'Employee',
    'NominaConcept',
    'Document',
    'Payroll',
    'PayrollLine',
    'ChecklistItem',

    # Database utilities
    'create_database_engine',
    'ensure_documents_directory',
    'get_client_document_path',
    'get_employee_document_path',
    'save_document_file',
    'load_document_file',
    'parse_vida_laboral_csv_simple',
    'BASIC_NOMINA_CONCEPTS',

    # Production models
    'ProductionBase',
    'ProductionCompany',
    'ProductionEmployee',
    'create_production_engine',
    'create_production_session',
    'get_production_company_by_cif',
    'get_production_company_by_id',
    'get_production_employee_by_identity_card',
    'list_production_employees_for_company',

    # Main application
    'ValeriaAgent',
    'extract_payroll_info'
]
