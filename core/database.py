#!/usr/bin/env python3
"""
ValerIA Core Database Utilities
Database connection management and utility functions.
These functions are used at runtime by the application.
"""

import os
from typing import Optional
from sqlalchemy import create_engine


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


# Document Storage Utilities

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
