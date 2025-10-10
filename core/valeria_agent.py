#!/usr/bin/env python3
"""
ValerIA AI Agent
Processes vida laboral CSV files and nominas PDFs using OpenAI function calling.
Maximizes reuse of existing modules: setup_database.py and process_payroll.py
"""

import json
import csv
import os
import uuid
import zipfile
import re
import glob
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import difflib
import time
from collections import deque
from decimal import Decimal

from openai import OpenAI
from tqdm import tqdm
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect as sa_inspect

# Reuse existing modules
from core.models import (Client, Employee, Payroll, PayrollLine,
    NominaConcept
)
from core.database import create_database_engine
from core.production_models import (
    create_production_engine, ProductionCompany, ProductionEmployee
)
from core.process_payroll import extract_payroll_info


class ValeriaAgent:
    """AI Agent for processing Spanish payroll documents"""

    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)

        # Local database (for payrolls and optionally for companies/employees in dev mode)
        self.engine = create_database_engine(echo=False)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Production database (read-only, for companies/employees when enabled)
        self.use_production_data = os.getenv('USE_PRODUCTION_DATA', 'false').lower() == 'true'
        self.prod_session = None
        if self.use_production_data:
            try:
                prod_engine = create_production_engine(echo=False)
                ProdSession = sessionmaker(bind=prod_engine)
                self.prod_session = ProdSession()
                print("✓ Connected to production database (read-only mode)")
            except Exception as e:
                print(f"⚠️  Warning: Could not connect to production database: {e}")
                print("   Falling back to local data")
                self.use_production_data = False

        self.processing_state = {
            'vida_laboral_processed': False,
            'client_id': None,
            'employees_created': 0,
            'nominas_processed': 0
        }

        # Output control
        self.verbose_mode = False  # Global toggle for technical details
        self.last_tool_result = None  # Stores last operation result for on-demand access

        # Conversational memory (summary + recent turns)
        self.memory_summary: str = ""
        self.conversation_history: deque = deque()
        self._max_history_turns: int = 50  # keep the last 50 turns (user + assistant messages tracked separately)
        self._max_history_messages: int = self._max_history_turns * 2
        self._summary_char_limit: int = 4000

        # Cache for concept mappings
        self._concept_mappings = None

        # Define tools for OpenAI function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "process_vida_laboral_csv",
                    "description": "Process a vida laboral CSV file and insert employee records into database. IMPORTANT: You must ask the user which company to assign employees to before calling this function. Use list_clients to show available companies.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the vida laboral CSV file"
                            },
                            "client_name": {
                                "type": "string",
                                "description": "Name or CIF of the client company (REQUIRED - must ask user first)"
                            }
                        },
                        "required": ["file_path", "client_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_files_from_zip",
                    "description": "Extract PDF files from a ZIP archive for processing",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "zip_path": {
                                "type": "string",
                                "description": "Path to the ZIP file containing nominas PDFs"
                            },
                            "extract_to": {
                                "type": "string",
                                "description": "Directory to extract files to (optional, defaults to temp folder)"
                            }
                        },
                        "required": ["zip_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "process_payslip_batch",
                    "description": "Process multiple nomina PDF files and extract payroll data. Can accept PDF files, directories (will scan for PDFs), or ZIP archives (will extract PDFs).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdf_files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of paths to process - can include PDF files, directories, or ZIP files"
                            }
                        },
                        "required": ["pdf_files"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_processing_report",
                    "description": "Generate a summary report of all processed data in JSON format",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "output_format": {
                                "type": "string",
                                "enum": ["json"],
                                "description": "Output format for the report (default: json)"
                            },
                            "save_to_file": {
                                "type": "boolean",
                                "description": "Whether to save the report to a file (default: false)"
                            },
                            "filename": {
                                "type": "string",
                                "description": "Custom filename (auto-generated if not provided)"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_missing_payslips_report",
                    "description": "Analyze and report missing payslips by comparing vida laboral employment periods with processed nominas. Identifies gaps in payroll documentation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client_id": {
                                "type": "integer",
                                "description": "Client ID to analyze (optional, uses current client if not specified)"
                            },
                            "output_format": {
                                "type": "string",
                                "enum": ["console", "csv", "json"],
                                "description": "Output format for the report (default: json)"
                            },
                            "save_to_file": {
                                "type": "boolean",
                                "description": "Whether to save the report to a file (default: false)"
                            },
                            "filename": {
                                "type": "string",
                                "description": "Custom filename (auto-generated if not provided)"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_client",
                    "description": "Create a new client/company record in the database",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Company name"
                            },
                            "cif": {
                                "type": "string",
                                "description": "Tax identification number (CIF/NIF)"
                            },
                            "fiscal_address": {
                                "type": "string",
                                "description": "Company fiscal address (optional)"
                            },
                            "email": {
                                "type": "string",
                                "description": "Company email (optional)"
                            },
                            "phone": {
                                "type": "string",
                                "description": "Company phone (optional)"
                            }
                        },
                        "required": ["name", "cif"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_employee",
                    "description": "Create a new employee record for a company",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "company_id": {
                                "type": "string",
                                "description": "Company UUID"
                            },
                            "first_name": {
                                "type": "string",
                                "description": "Employee first name"
                            },
                            "last_name": {
                                "type": "string",
                                "description": "Employee last name (paternal surname)"
                            },
                            "last_name2": {
                                "type": "string",
                                "description": "Employee second last name (maternal surname, optional)"
                            },
                            "identity_card_number": {
                                "type": "string",
                                "description": "DNI or NIE number"
                            },
                            "salary": {
                                "type": "number",
                                "description": "Monthly salary (optional)"
                            },
                            "role": {
                                "type": "string",
                                "description": "Job role (optional)"
                            }
                        },
                        "required": ["company_id", "first_name", "last_name", "identity_card_number"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_payroll",
                    "description": "Create a new payroll record for an employee",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {
                                "type": "integer",
                                "description": "Employee ID"
                            },
                            "period_year": {
                                "type": "integer",
                                "description": "Payroll year"
                            },
                            "period_month": {
                                "type": "integer",
                                "description": "Payroll month (1-12)"
                            },
                            "bruto_total": {
                                "type": "number",
                                "description": "Gross total amount"
                            },
                            "neto_total": {
                                "type": "number",
                                "description": "Net total amount"
                            }
                        },
                        "required": ["employee_id", "period_year", "period_month"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_employee",
                    "description": "Update existing employee details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {
                                "type": "integer",
                                "description": "Employee ID to update"
                            },
                            "salary": {
                                "type": "number",
                                "description": "New salary amount (optional)"
                            },
                            "role": {
                                "type": "string",
                                "description": "New job role (optional)"
                            },
                            "employee_status": {
                                "type": "string",
                                "description": "Employment status: 'Active', 'Terminated', etc. (optional)"
                            }
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_employee",
                    "description": "Permanently delete an employee and all associated payrolls. This is a hard delete with cascade.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {
                                "type": "integer",
                                "description": "Employee ID to delete"
                            }
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_client",
                    "description": "Permanently delete a client/company and all associated employees and payrolls. This is a hard delete with cascade.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client_id": {
                                "type": "string",
                                "description": "Client UUID to delete"
                            }
                        },
                        "required": ["client_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_clients",
                    "description": "List all companies/clients in the database",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "active_only": {
                                "type": "boolean",
                                "description": "If true, only show active clients (default: true)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 100)"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_employees",
                    "description": "List employees with optional filters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "company_id": {
                                "type": "string",
                                "description": "Filter by company UUID (optional)"
                            },
                            "employee_status": {
                                "type": "string",
                                "description": "Filter by employment status: 'Active', 'Terminated', etc. (optional, shows all if not specified)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 100)"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_payrolls",
                    "description": "List payrolls with optional filters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {
                                "type": "integer",
                                "description": "Filter by employee ID (optional)"
                            },
                            "year": {
                                "type": "integer",
                                "description": "Filter by year (optional)"
                            },
                            "month": {
                                "type": "integer",
                                "description": "Filter by month 1-12 (optional)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 100)"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_payroll",
                    "description": "Permanently delete a payroll record and all associated line items. This is a hard delete with cascade.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "payroll_id": {
                                "type": "integer",
                                "description": "Payroll ID to delete"
                            }
                        },
                        "required": ["payroll_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_employees",
                    "description": "Search for employees by name or ID number (fuzzy search)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search term (name or ID number)"
                            },
                            "company_id": {
                                "type": "string",
                                "description": "Filter by company UUID (optional)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 20)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_database_stats",
                    "description": "Get overall database statistics (clients, employees, payrolls counts)",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    # ========================================
    # Helper Methods for Dual Data Sources
    # ========================================

    def _get_company(self, cif: str = None, company_id: str = None, name: str = None):
        """
        Get company from either production or local database based on configuration.
        Returns: Local Client object (converted from production if needed)
        """
        if self.use_production_data and self.prod_session:
            # Query production database
            if cif:
                prod_company = self.prod_session.query(ProductionCompany).filter_by(cif=cif).first()
            elif company_id:
                prod_company = self.prod_session.query(ProductionCompany).filter_by(id=company_id).first()
            elif name:
                prod_company = self.prod_session.query(ProductionCompany).filter_by(name=name).first()
            else:
                return None

            if prod_company:
                # Convert production company to local Client structure (but don't save to DB)
                # This allows the rest of the code to work with a consistent interface
                local_company = Client(
                    id=prod_company.id,
                    name=prod_company.name,
                    cif=prod_company.cif,
                    fiscal_address=prod_company.fiscal_address,
                    email=prod_company.email,
                    phone=prod_company.phone,
                    begin_date=prod_company.begin_date,
                    managed_by=prod_company.managed_by,
                    status=prod_company.status,
                    legal_repr_first_name=prod_company.legal_repr_first_name,
                    legal_repr_last_name1=prod_company.legal_repr_last_name1,
                    legal_repr_last_name2=prod_company.legal_repr_last_name2,
                    legal_repr_nif=prod_company.legal_repr_nif,
                    legal_repr_role=prod_company.legal_repr_role,
                    legal_repr_phone=prod_company.legal_repr_phone,
                    legal_repr_email=prod_company.legal_repr_email
                )
                return local_company
            return None
        else:
            # Query local database
            if cif:
                return self.session.query(Client).filter_by(cif=cif).first()
            elif company_id:
                return self.session.query(Client).filter_by(id=company_id).first()
            elif name:
                return self.session.query(Client).filter_by(name=name).first()
            return None

    def _get_employee(self, identity_card_number: str = None, employee_id: int = None, company_id: str = None):
        """
        Get employee from either production or local database based on configuration.
        Returns: Local Employee object (converted from production if needed)
        """
        if self.use_production_data and self.prod_session:
            # Query production database
            if identity_card_number and company_id:
                prod_employee = self.prod_session.query(ProductionEmployee).filter_by(
                    identity_card_number=identity_card_number,
                    company_id=company_id
                ).first()
            elif identity_card_number:
                prod_employee = self.prod_session.query(ProductionEmployee).filter_by(
                    identity_card_number=identity_card_number
                ).first()
            elif employee_id:
                prod_employee = self.prod_session.query(ProductionEmployee).filter_by(id=employee_id).first()
            else:
                return None

            if prod_employee:
                # Convert production employee to local Employee structure
                local_employee = Employee(
                    id=int(prod_employee.id),  # Convert from Numeric to int
                    company_id=prod_employee.company_id,
                    first_name=prod_employee.first_name,
                    last_name=prod_employee.last_name,
                    last_name2=prod_employee.last_name2,
                    identity_card_number=prod_employee.identity_card_number,
                    identity_doc_type=prod_employee.identity_doc_type,
                    ss_number=prod_employee.ss_number,
                    birth_date=prod_employee.birth_date,
                    address=prod_employee.address,
                    phone=prod_employee.phone,
                    mail=prod_employee.mail,
                    begin_date=prod_employee.begin_date,
                    end_date=prod_employee.end_date,
                    salary=float(prod_employee.salary) if prod_employee.salary else None,
                    role=prod_employee.role,
                    employee_status=prod_employee.employee_status,
                    active=(prod_employee.employee_status == 'Active')
                )
                return local_employee
            return None
        else:
            # Query local database
            if identity_card_number and company_id:
                return self.session.query(Employee).filter_by(
                    identity_card_number=identity_card_number,
                    company_id=company_id
                ).first()
            elif identity_card_number:
                return self.session.query(Employee).filter_by(identity_card_number=identity_card_number).first()
            elif employee_id:
                return self.session.query(Employee).filter_by(id=employee_id).first()
            return None

    def _list_employees_for_company(self, company_id: str):
        """
        List all employees for a company from either production or local database.
        Returns: List of local Employee objects
        """
        if self.use_production_data and self.prod_session:
            # Query production database
            prod_employees = self.prod_session.query(ProductionEmployee).filter_by(company_id=company_id).all()

            # Convert to local Employee objects
            local_employees = []
            for prod_emp in prod_employees:
                local_emp = Employee(
                    id=int(prod_emp.id),
                    company_id=prod_emp.company_id,
                    first_name=prod_emp.first_name,
                    last_name=prod_emp.last_name,
                    last_name2=prod_emp.last_name2,
                    identity_card_number=prod_emp.identity_card_number,
                    identity_doc_type=prod_emp.identity_doc_type,
                    ss_number=prod_emp.ss_number,
                    birth_date=prod_emp.birth_date,
                    address=prod_emp.address,
                    phone=prod_emp.phone,
                    mail=prod_emp.mail,
                    begin_date=prod_emp.begin_date,
                    end_date=prod_emp.end_date,
                    salary=float(prod_emp.salary) if prod_emp.salary else None,
                    role=prod_emp.role,
                    employee_status=prod_emp.employee_status,
                    active=(prod_emp.employee_status == 'Active')
                )
                local_employees.append(local_emp)
            return local_employees
        else:
            # Query local database
            return self.session.query(Employee).filter_by(company_id=company_id).all()

    # ========================================
    # Main Processing Methods
    # ========================================

    def process_vida_laboral_csv(self, file_path: str, client_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Process vida laboral CSV file - imports employee data into database.

        Args:
            file_path: Path to the vida laboral CSV file
            client_name: Name or CIF of the company to assign employees to (REQUIRED)

        Returns:
            Dict with success status, employee counts, and message
        """
        try:
            # Client name is required - agent should ask user before calling this
            if not client_name:
                return {
                    "success": False,
                    "error": "client_name is required",
                    "message": "Please specify which company to assign these employees to. Use list_clients to see available companies, or create_client to create a new one."
                }

            # Find client by name or CIF
            client = self.session.query(Client).filter(
                (Client.name == client_name) | (Client.cif == client_name)
            ).first()

            if not client:
                return {
                    "success": False,
                    "error": f"Client '{client_name}' not found",
                    "message": f"Company '{client_name}' does not exist. Use create_client to create it first, or use list_clients to see available companies."
                }

            self.processing_state['client_id'] = client.id

            # Process CSV - reuse CSV parsing patterns from existing code
            employees_created = 0
            employees_updated = 0

            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    documento = row['documento']
                    nombre = row['nombre']
                    situacion = row['situacion']
                    f_real_alta = row.get('f_real_alta', '')
                    f_real_sit = row.get('f_real_sit', '')

                    # Parse Spanish name format: "SURNAME1 SURNAME2 --- FIRSTNAME" (updated for new schema)
                    if ' --- ' in nombre:
                        apellidos, nombre_propio = nombre.split(' --- ', 1)
                        first_name = nombre_propio.strip()

                        # Split surnames
                        surname_parts = apellidos.strip().split()
                        last_name = surname_parts[0] if len(surname_parts) > 0 else "Unknown"
                        last_name2 = surname_parts[1] if len(surname_parts) > 1 else None
                    else:
                        # Fallback: assume first word is first name, rest is surname
                        name_parts = nombre.strip().split()
                        first_name = name_parts[0] if len(name_parts) > 0 else "Unknown"
                        last_name = name_parts[1] if len(name_parts) > 1 else "Unknown"
                        last_name2 = name_parts[2] if len(name_parts) > 2 else None

                    # Parse employment dates
                    begin_date = self._parse_date(f_real_alta) if f_real_alta else None  # Renamed
                    end_date = None  # Renamed
                    if situacion == 'BAJA' and f_real_sit:
                        end_date = self._parse_date(f_real_sit)

                    # Determine document type
                    identity_doc_type = 'NIE' if documento.startswith(('X', 'Y', 'Z')) else 'DNI'

                    # Check if employee exists (updated field names)
                    employee = self.session.query(Employee).filter_by(
                        company_id=client.id,  # Updated from client_id
                        identity_card_number=documento  # Updated from documento
                    ).first()

                    if not employee:
                        employee = Employee(
                            company_id=client.id,
                            first_name=first_name,
                            last_name=last_name,
                            last_name2=last_name2,
                            identity_card_number=documento,
                            identity_doc_type=identity_doc_type,
                            ss_number=f"SS{uuid.uuid4().hex[:10].upper()}",
                            begin_date=begin_date,
                            end_date=end_date,
                            salary=1500.00,  # Default salary
                            role="Empleado",  # Default role
                            employee_status='Terminated' if end_date else 'Active'
                        )
                        self.session.add(employee)
                        employees_created += 1
                    else:
                        # Update existing employee
                        employee.first_name = first_name
                        employee.last_name = last_name
                        employee.last_name2 = last_name2
                        employee.begin_date = begin_date
                        employee.end_date = end_date
                        employee.employee_status = 'Terminated' if end_date else 'Active'
                        employees_updated += 1

            self.session.commit()
            self.processing_state['vida_laboral_processed'] = True
            self.processing_state['employees_created'] = employees_created

            return {
                "success": True,
                "client_id": client.id,
                "client_name": client_name,
                "employees_created": employees_created,
                "employees_updated": employees_updated,
                "message": f"Successfully processed vida laboral for {client_name}"
            }

        except Exception as e:
            self.session.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to process vida laboral CSV: {e}"
            }

    def detect_missing_payslips(self, client_id: Optional[str] = None) -> Dict[str, Any]:  # Updated type hint
        """
        Detect missing payslips by comparing vida laboral employment periods
        with processed nomina records in the database.
        """
        try:

            # Use current client if not specified
            if not client_id:
                client_id = self.processing_state.get('client_id')
                if not client_id:
                    return {
                        "success": False,
                        "error": "No client specified and no vida laboral processed",
                        "message": "Please process vida laboral CSV first or specify client_id"
                    }

            # Get all employees for this client with employment periods
            # Use helper method to get from appropriate data source
            employees = self._list_employees_for_company(client_id)

            # Filter to only those with begin dates
            employees = [emp for emp in employees if emp.begin_date is not None]

            if not employees:
                return {
                    "success": False,
                    "error": "No employees found with employment periods",
                    "message": "Process vida laboral CSV first to establish employment periods"
                }

            missing_payslips = []
            total_missing = 0
            current_date = date.today()

            print(f"🔍 Analyzing missing payslips for {len(employees)} employees...")

            for employee in employees:
                # Build full name from components
                full_name = f"{employee.first_name} {employee.last_name}"
                if employee.last_name2:
                    full_name += f" {employee.last_name2}"

                print(f"   📋 Checking {full_name} ({employee.identity_card_number})...")  # Updated

                # Determine employment period (updated field names)
                start_date = employee.begin_date  # Updated from employment_start_date
                end_date = employee.end_date or current_date  # Updated from employment_end_date

                # Generate expected months
                expected_months = self._generate_expected_months(start_date, end_date)

                # Get processed nomina months for this employee
                processed_nominas = self.session.query(Payroll).filter_by(
                    employee_id=employee.id
                ).all()

                processed_months = {(p.period_year, p.period_month) for p in processed_nominas}

                # Find missing months
                missing_months = []
                for year, month in expected_months:
                    if (year, month) not in processed_months:
                        missing_months.append(f"{year}-{month:02d}")

                if missing_months:
                    employee_missing = {
                        "employee_id": employee.id,
                        "employee_name": full_name,  # Use constructed full_name
                        "identity_card_number": employee.identity_card_number,  # Updated from documento
                        "employment_start": start_date.strftime('%Y-%m-%d') if start_date else None,
                        "employment_end": end_date.strftime('%Y-%m-%d') if employee.end_date else "Active",  # Updated
                        "expected_months": len(expected_months),
                        "processed_months": len(processed_months),
                        "missing_months": missing_months,
                        "missing_count": len(missing_months)
                    }
                    missing_payslips.append(employee_missing)
                    total_missing += len(missing_months)

            # Generate summary
            total_employees = len(employees)
            employees_with_gaps = len(missing_payslips)

            summary = {
                "total_employees_analyzed": total_employees,
                "employees_with_missing_payslips": employees_with_gaps,
                "total_missing_payslips": total_missing,
                "analysis_date": current_date.strftime('%Y-%m-%d')
            }

            return {
                "success": True,
                "summary": summary,
                "missing_payslips": missing_payslips,
                "message": f"Found {total_missing} missing payslips across {employees_with_gaps} employees"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to detect missing payslips: {e}"
            }

    def _generate_expected_months(self, start_date: date, end_date: date) -> List[Tuple[int, int]]:
        """Generate list of (year, month) tuples for expected payslip months"""
        if not start_date:
            return []

        expected_months = []
        current = start_date.replace(day=1)  # Start from first day of month
        end = end_date.replace(day=1) if end_date else date.today().replace(day=1)

        while current <= end:
            expected_months.append((current.year, current.month))
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        return expected_months

    def generate_missing_payslips_report(self, client_id: Optional[int] = None,
                                       output_format: str = "json",
                                       save_to_file: bool = False,
                                       filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive report of missing payslips with multiple output formats.

        Args:
            client_id: Client ID to analyze (uses current if not specified)
            output_format: "console", "csv", or "json"
            save_to_file: Whether to save the report to a file
            filename: Custom filename (auto-generated if not provided)
        """
        try:
            # Get missing payslip data
            result = self.detect_missing_payslips(client_id)

            if not result["success"]:
                return result

            summary = result["summary"]
            missing_data = result["missing_payslips"]

            report_content = ""

            if output_format == "console":
                report_content = self._format_console_report(summary, missing_data)
            elif output_format == "csv":
                report_content = self._format_csv_report(missing_data)
            elif output_format == "json":
                report_content = json.dumps({
                    "summary": summary,
                    "missing_payslips": missing_data
                }, indent=2, default=str)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported output format: {output_format}",
                    "message": "Supported formats: console, csv, json"
                }

            # Save to file if requested
            file_path = None
            if save_to_file:
                # Create reports directory
                import os
                from datetime import datetime
                reports_dir = "./reports"
                os.makedirs(reports_dir, exist_ok=True)

                # Generate filename if not provided
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    extension = "json" if output_format == "json" else "csv" if output_format == "csv" else "txt"
                    filename = f"missing_payslips_report_{timestamp}.{extension}"

                file_path = os.path.join(reports_dir, filename)

                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to write file: {e}",
                        "message": f"Report generated but file writing failed: {e}"
                    }

            return {
                "success": True,
                "format": output_format,
                "report_content": report_content,
                "summary": summary,
                "file_path": file_path,
                "message": f"Generated {output_format} report with {summary['total_missing_payslips']} missing payslips" + (f" - Saved to {file_path}" if file_path else "")
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to generate report: {e}"
            }

    def _format_console_report(self, summary: Dict, missing_data: List[Dict]) -> str:
        """Format missing payslips report for console output"""
        lines = []
        lines.append("📊 MISSING PAYSLIPS ANALYSIS REPORT")
        lines.append("=" * 50)
        lines.append("")

        # Summary section
        lines.append(f"📈 SUMMARY ({summary['analysis_date']})")
        lines.append("-" * 30)
        lines.append(f"  Total employees analyzed: {summary['total_employees_analyzed']}")
        lines.append(f"  Employees with missing payslips: {summary['employees_with_missing_payslips']}")
        lines.append(f"  Total missing payslips: {summary['total_missing_payslips']}")

        if summary['total_employees_analyzed'] > 0:
            completion_rate = ((summary['total_employees_analyzed'] - summary['employees_with_missing_payslips'])
                             / summary['total_employees_analyzed'] * 100)
            lines.append(f"  Payslip completion rate: {completion_rate:.1f}%")
        lines.append("")

        # Detailed section
        if missing_data:
            lines.append("🔍 DETAILED MISSING PAYSLIPS")
            lines.append("-" * 40)

            for emp in missing_data:
                lines.append(f"\n👤 {emp['employee_name']} ({emp['documento']})")
                lines.append(f"   Employment: {emp['employment_start']} to {emp['employment_end']}")
                lines.append(f"   Expected: {emp['expected_months']} | Processed: {emp['processed_months']} | Missing: {emp['missing_count']}")

                # Group missing months by year for readability
                missing_by_year = {}
                for month_str in emp['missing_months']:
                    year = month_str.split('-')[0]
                    month = month_str.split('-')[1]
                    if year not in missing_by_year:
                        missing_by_year[year] = []
                    missing_by_year[year].append(month)

                for year, months in sorted(missing_by_year.items()):
                    months_str = ", ".join(sorted(months))
                    lines.append(f"   📅 {year}: {months_str}")
        else:
            lines.append("✅ No missing payslips found! All employees have complete records.")

        return "\n".join(lines)

    def _format_csv_report(self, missing_data: List[Dict]) -> str:
        """Format missing payslips data as CSV"""
        lines = []
        lines.append("employee_name,documento,employment_start,employment_end,expected_months,processed_months,missing_count,missing_months")

        for emp in missing_data:
            missing_months_str = "|".join(emp['missing_months'])
            line = f"\"{emp['employee_name']}\",{emp['documento']},{emp['employment_start']},{emp['employment_end']},{emp['expected_months']},{emp['processed_months']},{emp['missing_count']},\"{missing_months_str}\""
            lines.append(line)

        return "\n".join(lines)

    def extract_files_from_zip(self, zip_path: str, extract_to: Optional[str] = None) -> Dict[str, Any]:
        """Extract PDF files from ZIP - simple file handling"""
        try:
            if not extract_to:
                extract_to = f"./temp_nominas_{uuid.uuid4().hex[:8]}"

            os.makedirs(extract_to, exist_ok=True)

            pdf_files = []
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.filename.lower().endswith('.pdf'):
                        zip_ref.extract(file_info, extract_to)
                        pdf_files.append(os.path.join(extract_to, file_info.filename))

            return {
                "success": True,
                "pdf_files": pdf_files,
                "extract_location": extract_to,
                "message": f"Extracted {len(pdf_files)} PDF files from {zip_path}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to extract ZIP file: {e}"
            }

    def process_payslip_batch(self, pdf_files: List[str]) -> Dict[str, Any]:
        """
        Process multiple nomina PDFs - reuses existing process_payroll.py

        Args:
            pdf_files: List of paths that can include:
                - Individual PDF files
                - Directories (will scan for PDFs recursively)
                - ZIP archives (will extract PDFs)

        Returns:
            Dict with success status, results, and statistics
        """
        # Check if employees exist in database instead of using workflow flag
        employee_count = self.session.query(Employee).count()
        if employee_count == 0:
            return {
                "success": False,
                "message": "No employees found in database. Please import vida laboral CSV or create employees first."
            }

        # Expand paths to get actual PDF files (handles directories and ZIPs)
        expanded_pdf_files = self._collect_pdfs_from_paths(pdf_files)

        if not expanded_pdf_files:
            return {
                "success": False,
                "message": "No PDF files found in the provided paths."
            }

        processed_count = 0
        failed_count = 0
        results = []

        # Initialize progress tracking
        total_files = len(expanded_pdf_files)
        start_time = time.time()

        print(f"🔄 Processing {total_files} nomina PDF files...")

        # Create progress bar
        with tqdm(total=total_files, desc="Processing nominas", unit="file") as pbar:
            for i, pdf_file in enumerate(expanded_pdf_files):
                try:
                    # Update progress bar with current file
                    pbar.set_description(f"Processing {os.path.basename(pdf_file)}")

                    # Session state is managed globally - don't rollback individual files

                    # Reuse existing PDF processing function
                    employee_data = extract_payroll_info(pdf_file, self.client.api_key)

                    if employee_data:
                        for emp_info in employee_data:
                            try:
                                # Try to match with existing employees
                                employee = self._find_matching_employee(emp_info)

                                if employee:
                                    # Parse date information
                                    period_start = self._parse_date(emp_info.get('period_start'))
                                    period_end = self._parse_date(emp_info.get('period_end'))
                                    pay_date = self._parse_date(emp_info.get('pay_date'))

                                    # Calculate period info
                                    period_year = emp_info.get('period_year', period_start.year if period_start else 2025)
                                    period_month = emp_info.get('period_month', period_start.month if period_start else 1)
                                    period_quarter = ((period_month - 1) // 3) + 1

                                    # Create payroll record with real extracted data
                                    payroll = Payroll(
                                        employee_id=employee.id,
                                        period_start=period_start or date(period_year, period_month, 1),
                                        period_end=period_end or date(period_year, period_month, 28),
                                        pay_date=pay_date or period_end or date(period_year, period_month, 28),
                                        period_year=period_year,
                                        period_month=period_month,
                                        period_quarter=period_quarter,
                                        bruto_total=emp_info.get('bruto_total'),
                                        neto_total=emp_info.get('neto_total'),
                                        irpf_base_monetaria=emp_info.get('irpf_base'),
                                        irpf_retencion_monetaria=emp_info.get('irpf_retencion'),
                                        ss_trabajador_total=emp_info.get('ss_trabajador'),
                                        extraction_confidence=0.8  # Could be improved with confidence scoring
                                    )
                                    self.session.add(payroll)
                                    self.session.flush()  # Get the payroll ID

                                    # Create PayrollLine records for concept lines
                                    concept_lines = emp_info.get('concept_lines', [])
                                    for concept in concept_lines:
                                        # Prepare context for AI mapping
                                        context = {
                                            'amount': concept.get('amount', 0),
                                            'other_concepts': [c.get('concept_desc', '') for c in concept_lines]
                                        }

                                        # Map concept description to database concept code
                                        concept_code = self._map_concept_to_code(concept.get('concept_desc', ''), context)

                                        # Only create payroll line if we have a valid concept code
                                        if concept_code:
                                            try:
                                                payroll_line = PayrollLine(
                                                    payroll_id=payroll.id,
                                                    concept_desc=concept.get('concept_desc', ''),
                                                    concept_code=concept_code,
                                                    is_devengo=concept.get('is_devengo', True),
                                                    is_deduccion=concept.get('is_deduccion', False),
                                                    importe_devengo=concept.get('amount') if concept.get('amount', 0) > 0 else None,
                                                    importe_deduccion=abs(concept.get('amount')) if concept.get('amount', 0) < 0 else None,
                                                    tributa_irpf=concept.get('concept_desc', '').upper().find('IRPF') == -1  # Simplified logic
                                                )
                                                self.session.add(payroll_line)
                                            except Exception as e:
                                                print(f"Warning: Could not add payroll line for '{concept.get('concept_desc', '')}': {e}")
                                                # Continue processing other concepts
                                                continue
                                        else:
                                            print(f"Warning: No concept code found for '{concept.get('concept_desc', '')}' - skipping")

                                    processed_count += 1

                                    # Build full name
                                    emp_full_name = f"{employee.first_name} {employee.last_name}"
                                    if employee.last_name2:
                                        emp_full_name += f" {employee.last_name2}"

                                    results.append({
                                        "employee": emp_full_name,  # Updated to use constructed name
                                        "file": pdf_file,
                                        "period": f"{period_year}-{period_month:02d}",
                                        "gross": emp_info.get('bruto_total'),
                                        "net": emp_info.get('neto_total'),
                                        "concepts": len(concept_lines),
                                        "status": "processed"
                                    })
                                else:
                                    results.append({
                                        "employee": emp_info.get('name', 'Unknown'),
                                        "file": pdf_file,
                                        "status": "employee_not_found"
                                    })
                                    failed_count += 1

                            except Exception as e:
                                print(f"Error processing employee data from {pdf_file}: {e}")
                                # Don't rollback the entire session - just skip this payroll
                                # The session will be committed with all successful payrolls
                                failed_count += 1
                                results.append({
                                    "employee": emp_info.get('name', 'Unknown'),
                                    "file": pdf_file,
                                    "status": "processing_error",
                                    "error": str(e)
                                })
                    else:
                        results.append({
                            "file": pdf_file,
                            "status": "no_data_extracted"
                        })
                        failed_count += 1

                except Exception as e:
                    results.append({
                        "file": pdf_file,
                        "status": "error",
                        "error": str(e)
                    })
                    failed_count += 1

                finally:
                    # Update progress bar and show time estimation
                    elapsed_time = time.time() - start_time
                    files_done = i + 1

                    if files_done > 0:
                        avg_time_per_file = elapsed_time / files_done
                        remaining_files = total_files - files_done
                        estimated_remaining = avg_time_per_file * remaining_files

                        # Update progress bar with ETA
                        pbar.set_postfix({
                            'processed': processed_count,
                            'failed': failed_count,
                            'ETA': f"{estimated_remaining:.1f}s"
                        })

                    pbar.update(1)

        # Commit all changes and show final summary
        self.session.commit()
        self.processing_state['nominas_processed'] = processed_count

        # Calculate total processing time
        total_time = time.time() - start_time
        avg_time_per_file = total_time / total_files if total_files > 0 else 0

        print("\n✅ Processing completed!")
        print(f"   📊 Processed: {processed_count}/{total_files} payslips")
        print(f"   ⏱️  Total time: {total_time:.1f}s (avg: {avg_time_per_file:.1f}s per file)")
        if failed_count > 0:
            print(f"   ⚠️  Failed: {failed_count} files")

        return {
            "success": True,
            "processed_count": processed_count,
            "failed_count": failed_count,
            "results": results,
            "total_time": total_time,
            "avg_time_per_file": avg_time_per_file,
            "message": f"Processed {processed_count} payslips with complete data extraction, {failed_count} failed (took {total_time:.1f}s)"
        }

    def _load_concept_mappings(self) -> Dict[str, Dict]:
        """Load all concept mappings from database for intelligent matching"""
        if self._concept_mappings is not None:
            return self._concept_mappings

        try:
            concepts = self.session.query(NominaConcept).all()
            self._concept_mappings = {
                concept.concept_code: {
                    'short_desc': concept.short_desc,
                    'long_desc': concept.long_desc or concept.short_desc,
                    'tributa_irpf': concept.tributa_irpf,
                    'cotiza_ss': concept.cotiza_ss,
                    'en_especie': concept.en_especie,
                    'default_group': concept.default_group
                }
                for concept in concepts
            }
            return self._concept_mappings
        except Exception as e:
            print(f"Warning: Could not load concept mappings: {e}")
            return {}

    def _find_fuzzy_concept_match(self, description: str, threshold: float = 0.85) -> Optional[str]:
        """Find best concept match using fuzzy string matching"""
        if not description:
            return None

        concept_mappings = self._load_concept_mappings()
        if not concept_mappings:
            return None

        desc_lower = description.lower().strip()
        best_match = None
        best_score = 0

        # Try matching against both short and long descriptions
        for code, concept_info in concept_mappings.items():
            for desc_field in ['short_desc', 'long_desc']:
                target_desc = concept_info[desc_field].lower().strip()

                # Calculate similarity
                similarity = difflib.SequenceMatcher(None, desc_lower, target_desc).ratio()

                if similarity > best_score and similarity >= threshold:
                    best_score = similarity
                    best_match = code

                # Also try partial matching for compound descriptions
                if desc_lower in target_desc or target_desc in desc_lower:
                    partial_score = min(len(desc_lower), len(target_desc)) / max(len(desc_lower), len(target_desc))
                    if partial_score > best_score and partial_score >= threshold:
                        best_score = partial_score
                        best_match = code

        return best_match

    def _get_ai_concept_mapping(self, description: str, context: Dict = None) -> Optional[str]:
        """Use AI to intelligently map concept description to existing database codes"""
        concept_mappings = self._load_concept_mappings()
        if not concept_mappings:
            return None

        # Prepare context information
        context_info = ""
        if context:
            amount = context.get('amount', 'Unknown')
            other_concepts = context.get('other_concepts', [])
            context_info = f"\nAmount: {amount}\nOther concepts in payslip: {other_concepts}"

        # Build list of available concepts for AI
        available_concepts = []
        for code, info in concept_mappings.items():
            available_concepts.append(f"Code {code}: {info['short_desc']} (Group: {info['default_group']})")

        prompt = f"""
        You are analyzing a Spanish payslip concept that needs to be mapped to an existing database concept code.

        EXTRACTED CONCEPT: "{description}"
        {context_info}

        AVAILABLE DATABASE CONCEPTS:
        {chr(10).join(available_concepts)}

        INSTRUCTIONS:
        1. Choose the BEST MATCHING concept code from the available options above
        2. Consider the concept description, amount, and context
        3. You MUST select from existing codes only - do not create new ones
        4. If no good match exists, select the closest generic concept
        5. Return ONLY the 3-digit concept code (e.g., "001", "700", "120")

        SELECTED CONCEPT CODE:
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                #max_completion_tokens=10,
                temperature=0.1
            )

            ai_choice = response.choices[0].message.content.strip()

            # Validate AI response - should be 3-digit code
            if ai_choice in concept_mappings:
                return ai_choice

            # Try to extract 3-digit code from response
            code_match = re.search(r'\b(\d{3})\b', ai_choice)
            if code_match and code_match.group(1) in concept_mappings:
                return code_match.group(1)

            return None

        except Exception as e:
            print(f"Warning: AI concept mapping failed: {e}")
            return None

    def _map_concept_to_code(self, concept_desc: str, context: Dict = None) -> Optional[str]:
        """Map extracted concept description to database concept code using multi-layer approach"""
        if not concept_desc:
            return None

        # Layer 1: Fuzzy matching against database
        fuzzy_match = self._find_fuzzy_concept_match(concept_desc, threshold=0.85)
        if fuzzy_match:
            return fuzzy_match

        # Layer 2: AI-powered intelligent mapping
        ai_match = self._get_ai_concept_mapping(concept_desc, context)
        if ai_match:
            return ai_match

        # Fallback: Return None to avoid foreign key violations
        # The calling code should handle None by either skipping the line or assigning a default
        return None

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string from extracted data"""
        if not date_str:
            return None

        try:
            # Try parsing common date formats
            from datetime import datetime

            # Try YYYY-MM-DD format first
            if '-' in date_str and len(date_str) == 10:
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                except Exception:
                    # If YYYY-MM-DD fails, try DD-MM-YYYY
                    try:
                        return datetime.strptime(date_str, '%d-%m-%Y').date()
                    except Exception:
                        pass

            # Try DD/MM/YYYY format
            if '/' in date_str and len(date_str) == 10:
                return datetime.strptime(date_str, '%d/%m/%Y').date()

            return None
        except Exception:
            return None

    def _normalize_spanish_id(self, id_string: str) -> str:
        """
        Normalize Spanish DNI/NIE by fixing common OCR errors.

        Spanish ID formats:
        - DNI: 8 digits + 1 letter (e.g., 12345678A)
        - NIE: 1 letter (X/Y/Z) + 7 digits + 1 letter (e.g., X1234567A)

        Common OCR errors in NIE numbers:
        - "2" at start → should be "Z"
        - "K" at start → should be "X"
        - "V" at start → should be "Y"

        Args:
            id_string: The ID string to normalize

        Returns:
            Normalized ID string
        """
        if not id_string:
            return id_string

        id_string = id_string.strip().upper()

        # Pattern: digit + 7 digits + letter = likely NIE with misread first letter
        # NIE format: [X/Y/Z][7 digits][letter]
        if len(id_string) == 9 and id_string[0].isdigit() and id_string[-1].isalpha():
            # Check if middle characters are all digits (typical NIE pattern)
            if id_string[1:-1].isdigit():
                first_char = id_string[0]

                # Common OCR confusions for NIE prefix letters
                if first_char == '2':
                    # Most common: 2 → Z
                    return 'Z' + id_string[1:]
                elif first_char in ('K', 'k'):
                    # Less common: K → X
                    return 'X' + id_string[1:]
                elif first_char in ('V', 'v'):
                    # Less common: V → Y
                    return 'Y' + id_string[1:]

        return id_string

    def _find_matching_employee(self, emp_info: Dict) -> Optional[Employee]:
        """
        Match extracted employee info with database records.

        Priority:
        1. Match by DNI/NIE (identity_card_number) - most reliable
        2. Match by name (only if company_id is known) - fallback

        If company_id is not set in processing_state, searches across ALL companies.
        """
        client_id = self.processing_state.get('client_id')
        name = emp_info.get('name', '').strip()
        emp_id = emp_info.get('id', '').strip()

        # Try to match company from extracted payslip data
        if not client_id:
            company_cif = emp_info.get('company_cif', '').strip()
            company_name = emp_info.get('company_name', '').strip()

            # Try matching by CIF first (most reliable)
            if company_cif:
                print(f"🏢 Attempting to match company by CIF: {company_cif}")
                company = self.session.query(Client).filter_by(cif=company_cif).first()
                if company:
                    client_id = company.id
                    self.processing_state['client_id'] = client_id
                    print(f"✅ Matched company from payslip CIF: {company.name} (ID: {company.id})")
                else:
                    print(f"⚠️  Company CIF '{company_cif}' not found in database")

            # Fallback: Try matching by company name (less reliable)
            if not client_id and company_name:
                print(f"🏢 Attempting to match company by name: {company_name}")
                # Try exact match first
                company = self.session.query(Client).filter_by(name=company_name).first()
                if not company:
                    # Try case-insensitive partial match
                    from sqlalchemy import func
                    company = self.session.query(Client).filter(
                        func.upper(Client.name).like(f"%{company_name.upper()}%")
                    ).first()

                if company:
                    client_id = company.id
                    self.processing_state['client_id'] = client_id
                    print(f"✅ Matched company from payslip name: {company.name} (ID: {company.id})")
                else:
                    print(f"⚠️  Company name '{company_name}' not found in database")

            # Update client_id variable for use in employee search below
            if client_id:
                print(f"🎯 Company context established: {client_id}")

        # Try to match by DNI/NIE first (most reliable method)
        if emp_id:
            original_id = emp_id
            print(f"🔍 Searching for employee with ID: {emp_id}")

            # Normalize ID to fix common OCR errors
            normalized_id = self._normalize_spanish_id(emp_id)
            if normalized_id != emp_id:
                print(f"   Normalized ID: {emp_id} → {normalized_id}")
                emp_id = normalized_id

            # Build list of ID variations to try (in priority order)
            id_variations = [emp_id]  # Start with normalized version

            # If ID starts with digit and matches NIE pattern, try X/Y/Z prefixes
            if original_id != emp_id:
                # Already tried normalization, add original as fallback
                id_variations.append(original_id)

            # If original starts with digit, try all NIE prefix variations
            if original_id and original_id[0].isdigit() and len(original_id) == 9:
                for prefix in ['Z', 'X', 'Y']:
                    variant = prefix + original_id[1:]
                    if variant not in id_variations:
                        id_variations.append(variant)

            # Try each variation
            employee = None
            for id_variant in id_variations:
                # Build query - search across all companies if client_id not set
                query = self.session.query(Employee).filter_by(identity_card_number=id_variant)

                # Only filter by company if we have one (stricter matching)
                if client_id:
                    query = query.filter_by(company_id=client_id)
                else:
                    pass  # Search all companies

                employee = query.first()
                if employee:
                    if id_variant != original_id:
                        print(f"   ✅ Matched using variation: {original_id} → {id_variant}")
                    break

            # Print search context after trying all variations
            if client_id and not employee:
                print(f"   Limiting search to company: {client_id}")
            elif not client_id:
                print(f"   Searching across all companies (no company context)")

            if employee:
                print(f"✅ Found employee: {employee.first_name} {employee.last_name} (ID: {employee.id}, Company: {employee.company_id})")

                # Auto-set client_id in processing state if not already set
                if not client_id:
                    self.processing_state['client_id'] = employee.company_id
                    print(f"   Auto-detected company: {employee.company_id}")

                return employee
            else:
                print(f"❌ No employee found with ID: {emp_id}")

        # Try to match by name ONLY if we have company context
        # (Name matching without company is too risky - could match wrong person)
        if name and client_id:
            print(f"🔍 Attempting name-based search: '{name}' in company {client_id}")

            # Search across first_name and last_name fields
            from sqlalchemy import or_, func
            employee = self.session.query(Employee).filter(
                Employee.company_id == client_id,
                or_(
                    Employee.first_name.ilike(f"%{name}%"),
                    Employee.last_name.ilike(f"%{name}%"),
                    func.concat(Employee.first_name, ' ', Employee.last_name).ilike(f"%{name}%")
                )
            ).first()

            if employee:
                print(f"✅ Found employee by name: {employee.first_name} {employee.last_name} (ID: {employee.id})")
                return employee
            else:
                print(f"❌ No employee found by name matching")
        elif name and not client_id:
            print(f"⚠️  Skipping name-based search (no company context - too risky)")

        print(f"❌ Could not match employee from payslip (name: '{name}', id: '{emp_id}')")
        return None

    def generate_processing_report(self, output_format: str = "json",
                                 save_to_file: bool = False,
                                 filename: Optional[str] = None) -> Dict[str, Any]:
        """Generate processing summary - reuses existing database models"""
        try:
            client_id = self.processing_state.get('client_id')

            # Query database using existing models
            total_clients = self.session.query(Client).count()
            total_employees = self.session.query(Employee).count()
            total_payrolls = self.session.query(Payroll).count()

            if client_id:
                client_employees = self.session.query(Employee).filter_by(company_id=client_id).count()
                client_payrolls = self.session.query(Payroll).join(Employee).filter(
                    Employee.company_id == client_id
                ).count()
            else:
                client_employees = 0
                client_payrolls = 0

            # Create report data
            report_data = {
                "processing_state": self.processing_state,
                "database_summary": {
                    "total_clients": total_clients,
                    "total_employees": total_employees,
                    "total_payrolls": total_payrolls,
                    "current_client_employees": client_employees,
                    "current_client_payrolls": client_payrolls
                },
                "report_timestamp": datetime.now().isoformat()
            }

            # Format report content based on output format
            if output_format == "json":
                report_content = json.dumps(report_data, indent=2, default=str)
            else:
                # Default to JSON format even if other format requested
                report_content = json.dumps(report_data, indent=2, default=str)
                output_format = "json"

            # Save to file if requested
            file_path = None
            if save_to_file:
                # Create reports directory
                import os
                reports_dir = "./reports"
                os.makedirs(reports_dir, exist_ok=True)

                # Generate filename if not provided
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"processing_report_{timestamp}.json"

                file_path = os.path.join(reports_dir, filename)

                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to write file: {e}",
                        "message": f"Report generated but file writing failed: {e}"
                    }

            return {
                "success": True,
                "format": output_format,
                "report_content": report_content,
                "processing_state": self.processing_state,
                "database_summary": report_data["database_summary"],
                "file_path": file_path,
                "message": "Processing report generated successfully" + (f" - Saved to {file_path}" if file_path else "")
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to generate report: {e}"
            }

    # ========================================
    # CRUD Operations - Clients
    # ========================================

    def create_client(self, name: str, cif: str, **kwargs) -> Dict[str, Any]:
        """
        Create a new client/company record

        Args:
            name: Company name
            cif: Tax identification number (CIF/NIF)
            **kwargs: Additional fields (fiscal_address, email, phone, etc.)

        Returns:
            {"success": bool, "data": Client, "message": str}
        """
        try:
            # Check if client with same CIF already exists
            existing = self.session.query(Client).filter_by(cif=cif).first()
            if existing:
                return {
                    "success": False,
                    "error": "Client with this CIF already exists",
                    "message": f"Client with CIF {cif} already exists (ID: {existing.id})"
                }

            # Create client
            client = Client(
                id=str(uuid.uuid4()),
                name=name,
                cif=cif,
                fiscal_address=kwargs.get('fiscal_address', ''),
                email=kwargs.get('email', ''),
                phone=kwargs.get('phone', ''),
                ccc_ss=kwargs.get('ccc_ss', ''),
                begin_date=kwargs.get('begin_date'),
                managed_by=kwargs.get('managed_by', ''),
                status=kwargs.get('status', 'Active'),
                active=kwargs.get('active', True),
                legal_repr_first_name=kwargs.get('legal_repr_first_name', ''),
                legal_repr_last_name1=kwargs.get('legal_repr_last_name1', ''),
                legal_repr_last_name2=kwargs.get('legal_repr_last_name2', ''),
                legal_repr_nif=kwargs.get('legal_repr_nif', ''),
                legal_repr_role=kwargs.get('legal_repr_role', ''),
                legal_repr_phone=kwargs.get('legal_repr_phone', ''),
                legal_repr_email=kwargs.get('legal_repr_email', '')
            )

            self.session.add(client)
            self.session.commit()

            return {
                "success": True,
                "data": client,
                "message": f"Successfully created client '{name}' (CIF: {cif}, ID: {client.id})"
            }

        except IntegrityError as e:
            self.session.rollback()
            return {
                "success": False,
                "error": f"Database integrity error: {e}",
                "message": f"Failed to create client: {e}"
            }
        except Exception as e:
            self.session.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create client: {e}"
            }

    def update_client(self, client_id: str, **fields) -> Dict[str, Any]:
        """
        Update existing client details

        Args:
            client_id: Client UUID
            **fields: Fields to update

        Returns:
            {"success": bool, "data": Client, "message": str, "changes": dict}
        """
        try:
            client = self.session.query(Client).filter_by(id=client_id).first()
            if not client:
                return {
                    "success": False,
                    "error": "Client not found",
                    "message": f"Client with ID {client_id} not found"
                }

            # Track changes
            changes = {}
            updatable_fields = [
                'name', 'cif', 'fiscal_address', 'email', 'phone', 'ccc_ss',
                'begin_date', 'managed_by', 'status', 'active',
                'legal_repr_first_name', 'legal_repr_last_name1', 'legal_repr_last_name2',
                'legal_repr_nif', 'legal_repr_role', 'legal_repr_phone', 'legal_repr_email'
            ]

            for field, new_value in fields.items():
                if field in updatable_fields and hasattr(client, field):
                    old_value = getattr(client, field)
                    if old_value != new_value:
                        changes[field] = {"old": old_value, "new": new_value}
                        setattr(client, field, new_value)

            if not changes:
                return {
                    "success": True,
                    "data": client,
                    "message": "No changes made (all values same as current)",
                    "changes": {}
                }

            self.session.commit()

            return {
                "success": True,
                "data": client,
                "message": f"Successfully updated client '{client.name}' ({len(changes)} field(s) changed)",
                "changes": changes
            }

        except Exception as e:
            self.session.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update client: {e}"
            }

    def delete_client(self, client_id: str) -> Dict[str, Any]:
        """
        Delete a client and all associated employees and payrolls

        This is a hard delete that permanently removes the client and cascades
        to all related records (employees, payrolls, documents, etc.)

        Args:
            client_id: Client UUID

        Returns:
            {"success": bool, "message": str, "deleted_counts": dict}
        """
        try:
            client = self.session.query(Client).filter_by(id=client_id).first()
            if not client:
                return {
                    "success": False,
                    "error": "Client not found",
                    "message": f"Client with ID {client_id} not found"
                }

            client_name = client.name
            deleted_counts = {"clients": 0, "employees": 0, "payrolls": 0}

            # Delete all employees and their payrolls (cascade)
            employees = self.session.query(Employee).filter_by(company_id=client_id).all()
            for emp in employees:
                # Delete payrolls for this employee
                payrolls = self.session.query(Payroll).filter_by(employee_id=emp.id).all()
                for payroll in payrolls:
                    self.session.delete(payroll)
                    deleted_counts["payrolls"] += 1

                self.session.delete(emp)
                deleted_counts["employees"] += 1

            # Delete the client (will cascade to documents, checklist items, etc.)
            self.session.delete(client)
            deleted_counts["clients"] = 1
            self.session.commit()

            return {
                "success": True,
                "message": f"Successfully deleted client '{client_name}', {deleted_counts['employees']} employee(s), and {deleted_counts['payrolls']} payroll(s)",
                "deleted_counts": deleted_counts
            }

        except Exception as e:
            self.session.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete client: {e}"
            }

    def list_clients(self, active_only: bool = True, limit: int = 100) -> Dict[str, Any]:
        """
        List all clients with optional filters

        Args:
            active_only: If True, only return active clients
            limit: Maximum number of results

        Returns:
            {"success": bool, "data": List[Client], "count": int, "message": str}
        """
        try:
            query = self.session.query(Client)

            if active_only:
                query = query.filter_by(active=True)

            clients = query.limit(limit).all()

            return {
                "success": True,
                "data": clients,
                "count": len(clients),
                "message": f"Found {len(clients)} client(s)"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0,
                "message": f"Failed to list clients: {e}"
            }

    # ========================================
    # CRUD Operations - Employees
    # ========================================

    def create_employee(self, company_id: str, first_name: str, last_name: str,
                       identity_card_number: str, **kwargs) -> Dict[str, Any]:
        """
        Create a new employee record

        Args:
            company_id: Client UUID
            first_name: Employee first name
            last_name: Employee last name (paternal surname)
            identity_card_number: DNI/NIE number
            **kwargs: Additional fields (last_name2, ss_number, salary, etc.)

        Returns:
            {"success": bool, "data": Employee, "message": str}
        """
        try:
            # Check if company exists
            client = self.session.query(Client).filter_by(id=company_id).first()
            if not client:
                return {
                    "success": False,
                    "error": "Company not found",
                    "message": f"Company with ID {company_id} not found"
                }

            # Check if employee already exists for this company
            existing = self.session.query(Employee).filter_by(
                company_id=company_id,
                identity_card_number=identity_card_number
            ).first()

            if existing:
                return {
                    "success": False,
                    "error": "Employee already exists",
                    "message": f"Employee with ID {identity_card_number} already exists for this company"
                }

            # Create employee
            employee = Employee(
                company_id=company_id,
                first_name=first_name,
                last_name=last_name,
                last_name2=kwargs.get('last_name2'),
                identity_card_number=identity_card_number,
                identity_doc_type=kwargs.get('identity_doc_type', 'DNI'),
                ss_number=kwargs.get('ss_number', ''),
                birth_date=kwargs.get('birth_date'),
                address=kwargs.get('address', ''),
                phone=kwargs.get('phone', ''),
                mail=kwargs.get('mail', ''),
                begin_date=kwargs.get('begin_date'),
                end_date=kwargs.get('end_date'),
                salary=kwargs.get('salary', 0.0),
                role=kwargs.get('role', 'Empleado'),
                employee_status=kwargs.get('employee_status', 'Active'),
                active=kwargs.get('active', True)
            )

            self.session.add(employee)
            self.session.commit()

            full_name = f"{first_name} {last_name}"
            if kwargs.get('last_name2'):
                full_name += f" {kwargs.get('last_name2')}"

            return {
                "success": True,
                "data": employee,
                "message": f"Successfully created employee '{full_name}' (ID: {identity_card_number}, Employee ID: {employee.id})"
            }

        except IntegrityError as e:
            self.session.rollback()
            return {
                "success": False,
                "error": f"Database integrity error: {e}",
                "message": f"Failed to create employee: {e}"
            }
        except Exception as e:
            self.session.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create employee: {e}"
            }

    def update_employee(self, employee_id: int, **fields) -> Dict[str, Any]:
        """
        Update existing employee details

        Args:
            employee_id: Employee ID
            **fields: Fields to update

        Returns:
            {"success": bool, "data": Employee, "message": str, "changes": dict}
        """
        try:
            employee = self.session.query(Employee).filter_by(id=employee_id).first()
            if not employee:
                return {
                    "success": False,
                    "error": "Employee not found",
                    "message": f"Employee with ID {employee_id} not found"
                }

            # Track changes
            changes = {}
            updatable_fields = [
                'first_name', 'last_name', 'last_name2', 'identity_card_number',
                'identity_doc_type', 'ss_number', 'birth_date', 'address', 'phone',
                'mail', 'begin_date', 'end_date', 'salary', 'role', 'employee_status', 'active'
            ]

            for field, new_value in fields.items():
                if field in updatable_fields and hasattr(employee, field):
                    old_value = getattr(employee, field)
                    if old_value != new_value:
                        changes[field] = {"old": old_value, "new": new_value}
                        setattr(employee, field, new_value)

            if not changes:
                return {
                    "success": True,
                    "data": employee,
                    "message": "No changes made (all values same as current)",
                    "changes": {}
                }

            self.session.commit()

            full_name = f"{employee.first_name} {employee.last_name}"
            if employee.last_name2:
                full_name += f" {employee.last_name2}"

            return {
                "success": True,
                "data": employee,
                "message": f"Successfully updated employee '{full_name}' ({len(changes)} field(s) changed)",
                "changes": changes
            }

        except Exception as e:
            self.session.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update employee: {e}"
            }

    def delete_employee(self, employee_id: int) -> Dict[str, Any]:
        """
        Delete an employee and all associated payrolls

        This is a hard delete that permanently removes the employee and cascades
        to all related records (payrolls, documents, etc.)

        Args:
            employee_id: Employee ID

        Returns:
            {"success": bool, "message": str, "deleted_counts": dict}
        """
        try:
            employee = self.session.query(Employee).filter_by(id=employee_id).first()
            if not employee:
                return {
                    "success": False,
                    "error": "Employee not found",
                    "message": f"Employee with ID {employee_id} not found"
                }

            full_name = f"{employee.first_name} {employee.last_name}"
            if employee.last_name2:
                full_name += f" {employee.last_name2}"

            deleted_counts = {"employees": 0, "payrolls": 0}

            # Delete associated payrolls (cascade)
            payrolls = self.session.query(Payroll).filter_by(employee_id=employee_id).all()
            for payroll in payrolls:
                self.session.delete(payroll)
                deleted_counts["payrolls"] += 1

            # Delete the employee (will cascade to documents, checklist items, etc.)
            self.session.delete(employee)
            deleted_counts["employees"] = 1
            self.session.commit()

            return {
                "success": True,
                "message": f"Successfully deleted employee '{full_name}' and {deleted_counts['payrolls']} payroll(s)",
                "deleted_counts": deleted_counts
            }

        except Exception as e:
            self.session.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete employee: {e}"
            }

    def list_employees(self, company_id: Optional[str] = None, employee_status: Optional[str] = None,
                      limit: int = 100) -> Dict[str, Any]:
        """
        List employees with optional filters

        Args:
            company_id: Filter by company (None = all companies)
            employee_status: Filter by status (None = all, 'Active', 'Terminated', etc.)
            limit: Maximum number of results

        Returns:
            {"success": bool, "data": List[Employee], "count": int, "message": str}
        """
        try:
            query = self.session.query(Employee)

            if company_id:
                query = query.filter_by(company_id=company_id)

            if employee_status:
                query = query.filter_by(employee_status=employee_status)

            employees = query.limit(limit).all()

            return {
                "success": True,
                "data": employees,
                "count": len(employees),
                "message": f"Found {len(employees)} employee(s)"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0,
                "message": f"Failed to list employees: {e}"
            }

    # ========================================
    # CRUD Operations - Payrolls
    # ========================================

    def create_payroll(self, employee_id: int, period_year: int, period_month: int,
                      **kwargs) -> Dict[str, Any]:
        """
        Create a new payroll record

        Args:
            employee_id: Employee ID
            period_year: Payroll year
            period_month: Payroll month (1-12)
            **kwargs: Additional fields (bruto_total, neto_total, etc.)

        Returns:
            {"success": bool, "data": Payroll, "message": str}
        """
        try:
            # Check if employee exists
            employee = self.session.query(Employee).filter_by(id=employee_id).first()
            if not employee:
                return {
                    "success": False,
                    "error": "Employee not found",
                    "message": f"Employee with ID {employee_id} not found"
                }

            # Check if payroll already exists for this period
            existing = self.session.query(Payroll).filter_by(
                employee_id=employee_id,
                period_year=period_year,
                period_month=period_month
            ).first()

            if existing:
                return {
                    "success": False,
                    "error": "Payroll already exists for this period",
                    "message": f"Payroll already exists for {period_year}-{period_month:02d}"
                }

            # Create payroll
            period_start = kwargs.get('period_start', date(period_year, period_month, 1))
            period_end = kwargs.get('period_end', date(period_year, period_month, 28))

            payroll = Payroll(
                employee_id=employee_id,
                period_start=period_start,
                period_end=period_end,
                pay_date=kwargs.get('pay_date', period_end),
                period_year=period_year,
                period_month=period_month,
                period_quarter=((period_month - 1) // 3) + 1,
                bruto_total=kwargs.get('bruto_total', 0.0),
                neto_total=kwargs.get('neto_total', 0.0),
                irpf_base_monetaria=kwargs.get('irpf_base_monetaria', 0.0),
                irpf_retencion_monetaria=kwargs.get('irpf_retencion_monetaria', 0.0),
                ss_trabajador_total=kwargs.get('ss_trabajador_total', 0.0),
                extraction_confidence=kwargs.get('extraction_confidence', 1.0)
            )

            self.session.add(payroll)
            self.session.commit()

            full_name = f"{employee.first_name} {employee.last_name}"
            if employee.last_name2:
                full_name += f" {employee.last_name2}"

            return {
                "success": True,
                "data": payroll,
                "message": f"Successfully created payroll for '{full_name}' - {period_year}-{period_month:02d} (ID: {payroll.id})"
            }

        except IntegrityError as e:
            self.session.rollback()
            return {
                "success": False,
                "error": f"Database integrity error: {e}",
                "message": f"Failed to create payroll: {e}"
            }
        except Exception as e:
            self.session.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create payroll: {e}"
            }

    def get_payroll(self, payroll_id: int) -> Dict[str, Any]:
        """
        Get a specific payroll record

        Args:
            payroll_id: Payroll ID

        Returns:
            {"success": bool, "data": Payroll, "message": str}
        """
        try:
            payroll = self.session.query(Payroll).filter_by(id=payroll_id).first()
            if not payroll:
                return {
                    "success": False,
                    "error": "Payroll not found",
                    "message": f"Payroll with ID {payroll_id} not found"
                }

            return {
                "success": True,
                "data": payroll,
                "message": f"Found payroll {payroll_id}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get payroll: {e}"
            }

    def update_payroll(self, payroll_id: int, **fields) -> Dict[str, Any]:
        """
        Update existing payroll details

        Args:
            payroll_id: Payroll ID
            **fields: Fields to update

        Returns:
            {"success": bool, "data": Payroll, "message": str, "changes": dict}
        """
        try:
            payroll = self.session.query(Payroll).filter_by(id=payroll_id).first()
            if not payroll:
                return {
                    "success": False,
                    "error": "Payroll not found",
                    "message": f"Payroll with ID {payroll_id} not found"
                }

            # Track changes
            changes = {}
            updatable_fields = [
                'period_start', 'period_end', 'pay_date', 'period_year', 'period_month',
                'period_quarter', 'bruto_total', 'neto_total', 'irpf_base_monetaria',
                'irpf_retencion_monetaria', 'ss_trabajador_total', 'extraction_confidence'
            ]

            for field, new_value in fields.items():
                if field in updatable_fields and hasattr(payroll, field):
                    old_value = getattr(payroll, field)
                    if old_value != new_value:
                        changes[field] = {"old": old_value, "new": new_value}
                        setattr(payroll, field, new_value)

            if not changes:
                return {
                    "success": True,
                    "data": payroll,
                    "message": "No changes made (all values same as current)",
                    "changes": {}
                }

            self.session.commit()

            return {
                "success": True,
                "data": payroll,
                "message": f"Successfully updated payroll {payroll_id} ({len(changes)} field(s) changed)",
                "changes": changes
            }

        except Exception as e:
            self.session.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update payroll: {e}"
            }

    def delete_payroll(self, payroll_id: int) -> Dict[str, Any]:
        """
        Delete a payroll record and all associated line items

        This is a hard delete that permanently removes the payroll and cascades
        to all related records (payroll lines, documents, etc.)

        Args:
            payroll_id: Payroll ID

        Returns:
            {"success": bool, "message": str, "deleted_counts": dict}
        """
        try:
            payroll = self.session.query(Payroll).filter_by(id=payroll_id).first()
            if not payroll:
                return {
                    "success": False,
                    "error": "Payroll not found",
                    "message": f"Payroll with ID {payroll_id} not found"
                }

            deleted_counts = {"payrolls": 0, "payroll_lines": 0}

            # Delete associated payroll lines (cascade)
            lines = self.session.query(PayrollLine).filter_by(payroll_id=payroll_id).all()
            for line in lines:
                self.session.delete(line)
                deleted_counts["payroll_lines"] += 1

            # Delete the payroll (will cascade to documents, checklist items, etc.)
            self.session.delete(payroll)
            deleted_counts["payrolls"] = 1
            self.session.commit()

            return {
                "success": True,
                "message": f"Successfully deleted payroll {payroll_id} and {deleted_counts['payroll_lines']} line(s)",
                "deleted_counts": deleted_counts
            }

        except Exception as e:
            self.session.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete payroll: {e}"
            }

    def list_payrolls(self, employee_id: Optional[int] = None, year: Optional[int] = None,
                     month: Optional[int] = None, limit: int = 100) -> Dict[str, Any]:
        """
        List payrolls with optional filters

        Args:
            employee_id: Filter by employee (None = all employees)
            year: Filter by year
            month: Filter by month
            limit: Maximum number of results

        Returns:
            {"success": bool, "data": List[Payroll], "count": int, "message": str}
        """
        try:
            query = self.session.query(Payroll)

            if employee_id:
                query = query.filter_by(employee_id=employee_id)

            if year:
                query = query.filter_by(period_year=year)

            if month:
                query = query.filter_by(period_month=month)

            payrolls = query.order_by(Payroll.period_year.desc(), Payroll.period_month.desc()).limit(limit).all()

            return {
                "success": True,
                "data": payrolls,
                "count": len(payrolls),
                "message": f"Found {len(payrolls)} payroll(s)"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0,
                "message": f"Failed to list payrolls: {e}"
            }

    # ========================================
    # CRUD Operations - Search & Query Helpers
    # ========================================

    def search_employees(self, query: str, company_id: Optional[str] = None,
                        limit: int = 20) -> Dict[str, Any]:
        """
        Search employees by name or ID number (fuzzy search)

        Args:
            query: Search term (name or ID)
            company_id: Filter by company (optional)
            limit: Maximum results

        Returns:
            {"success": bool, "data": List[Employee], "count": int, "message": str}
        """
        try:
            from sqlalchemy import or_, func

            search_query = self.session.query(Employee)

            if company_id:
                search_query = search_query.filter_by(company_id=company_id)

            # Search across multiple fields
            search_pattern = f"%{query}%"
            search_query = search_query.filter(
                or_(
                    Employee.first_name.ilike(search_pattern),
                    Employee.last_name.ilike(search_pattern),
                    Employee.last_name2.ilike(search_pattern),
                    Employee.identity_card_number.ilike(search_pattern),
                    func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_pattern),
                    func.concat(Employee.first_name, ' ', Employee.last_name, ' ', Employee.last_name2).ilike(search_pattern)
                )
            )

            employees = search_query.limit(limit).all()

            return {
                "success": True,
                "data": employees,
                "count": len(employees),
                "message": f"Found {len(employees)} employee(s) matching '{query}'"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0,
                "message": f"Failed to search employees: {e}"
            }

    def get_employee_payrolls(self, employee_id: int, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get all payrolls for a specific employee

        Args:
            employee_id: Employee ID
            year: Filter by year (optional)

        Returns:
            {"success": bool, "data": List[Payroll], "count": int, "message": str}
        """
        try:
            employee = self.session.query(Employee).filter_by(id=employee_id).first()
            if not employee:
                return {
                    "success": False,
                    "error": "Employee not found",
                    "message": f"Employee with ID {employee_id} not found"
                }

            query = self.session.query(Payroll).filter_by(employee_id=employee_id)

            if year:
                query = query.filter_by(period_year=year)

            payrolls = query.order_by(Payroll.period_year.desc(), Payroll.period_month.desc()).all()

            full_name = f"{employee.first_name} {employee.last_name}"
            if employee.last_name2:
                full_name += f" {employee.last_name2}"

            return {
                "success": True,
                "data": payrolls,
                "count": len(payrolls),
                "message": f"Found {len(payrolls)} payroll(s) for {full_name}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0,
                "message": f"Failed to get employee payrolls: {e}"
            }

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get overall database statistics

        Returns:
            {"success": bool, "stats": dict, "message": str}
        """
        try:
            stats = {
                "clients": {
                    "total": self.session.query(Client).count(),
                    "active": self.session.query(Client).filter_by(active=True).count()
                },
                "employees": {
                    "total": self.session.query(Employee).count(),
                    "active": self.session.query(Employee).filter_by(active=True).count()
                },
                "payrolls": {
                    "total": self.session.query(Payroll).count()
                },
                "payroll_lines": {
                    "total": self.session.query(PayrollLine).count()
                },
                "nomina_concepts": {
                    "total": self.session.query(NominaConcept).count()
                }
            }

            return {
                "success": True,
                "stats": stats,
                "message": f"Database contains {stats['clients']['total']} client(s), {stats['employees']['total']} employee(s), {stats['payrolls']['total']} payroll(s)"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stats": {},
                "message": f"Failed to get database stats: {e}"
            }

    # ========================================
    # Conversation memory helpers
    # ========================================

    def _add_to_memory_summary(self, message: Dict[str, str]) -> None:
        """Append an evicted message to the rolling memory summary."""
        snippet = f"{message['role'].capitalize()}: {message['content']}"
        if self.memory_summary:
            self.memory_summary = f"{self.memory_summary}\n{snippet}"
        else:
            self.memory_summary = snippet

        # Trim the summary to avoid unbounded growth
        if len(self.memory_summary) > self._summary_char_limit:
            self.memory_summary = self.memory_summary[-self._summary_char_limit:]

    def _append_conversation_message(self, role: str, content: str) -> None:
        """Store a conversation message, keeping only the most recent turns."""
        cleaned_content = content.strip()
        if not cleaned_content:
            return

        # Evict oldest messages beyond the configured window
        while len(self.conversation_history) >= self._max_history_messages:
            dropped = self.conversation_history.popleft()
            self._add_to_memory_summary(dropped)

        self.conversation_history.append({
            "role": role,
            "content": cleaned_content
        })

    # ========================================
    # Tool result serialization helpers
    # ========================================

    def _sanitize_value(self, value: Any) -> Any:
        """Convert values to JSON-serializable primitives."""
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(value)

    def _model_to_dict(self, instance: Any) -> Dict[str, Any]:
        """Convert a SQLAlchemy model instance into a dict of column values."""
        try:
            mapper = sa_inspect(instance.__class__)
        except Exception:
            return {"repr": str(instance)}

        data = {}
        for column in mapper.columns:
            column_key = column.key
            value = getattr(instance, column_key, None)
            data[column_key] = self._sanitize_value(value)
        return data

    def _serialize_tool_payload(self, value: Any) -> Any:
        """Recursively serialize tool payloads into JSON-friendly structures."""
        if isinstance(value, list):
            return [self._serialize_tool_payload(item) for item in value]
        if isinstance(value, tuple):
            return [self._serialize_tool_payload(item) for item in value]
        if isinstance(value, set):
            return [self._serialize_tool_payload(item) for item in value]
        if isinstance(value, dict):
            return {key: self._serialize_tool_payload(val) for key, val in value.items()}
        if hasattr(value, "__table__") or hasattr(value, "__mapper__"):
            return self._model_to_dict(value)
        return self._sanitize_value(value)

    def _format_clients_list(self, clients: List[Client], count: int) -> str:
        """Format clients list in human-readable table format"""
        if not clients:
            return "No companies found."

        lines = [f"\n📊 Found {count} company/companies:\n"]
        for client in clients:
            lines.append(f"  • {client.name}")
            lines.append(f"    CIF: {client.cif}")
            lines.append(f"    ID: {client.id}")
            if client.email:
                lines.append(f"    Email: {client.email}")
            if client.phone:
                lines.append(f"    Phone: {client.phone}")
            lines.append("")  # Blank line between companies
        return "\n".join(lines)

    def _format_employees_list(self, employees: List[Employee], count: int) -> str:
        """Format employees list in human-readable table format"""
        if not employees:
            return "No employees found."

        lines = [f"\n📊 Found {count} employee(s):\n"]
        for emp in employees:
            full_name = f"{emp.first_name} {emp.last_name}"
            if emp.last_name2:
                full_name += f" {emp.last_name2}"
            lines.append(f"  • {full_name}")
            lines.append(f"    ID: {emp.id} | {emp.identity_card_number}")
            if emp.salary:
                lines.append(f"    Salary: €{emp.salary:.2f}/month")
            if emp.employee_status:
                status_emoji = "✅" if emp.employee_status == "Active" else "❌"
                lines.append(f"    Status: {status_emoji} {emp.employee_status}")
            if emp.begin_date:
                lines.append(f"    Start: {emp.begin_date}")
            if emp.end_date:
                lines.append(f"    End: {emp.end_date}")
            lines.append("")  # Blank line between employees
        return "\n".join(lines)

    def _format_payrolls_list(self, payrolls: List[Payroll], count: int) -> str:
        """Format payrolls list in human-readable table format"""
        if not payrolls:
            return "No payrolls found."

        lines = [f"\n📊 Found {count} payroll(s):\n"]
        for payroll in payrolls:
            lines.append(f"  • Payroll #{payroll.id}")
            lines.append(f"    Employee ID: {payroll.employee_id}")
            lines.append(f"    Period: {payroll.period_month}/{payroll.period_year}")
            if payroll.bruto_total:
                lines.append(f"    Gross: €{payroll.bruto_total:.2f}")
            if payroll.neto_total:
                lines.append(f"    Net: €{payroll.neto_total:.2f}")
            if payroll.irpf_retencion_monetaria:
                lines.append(f"    IRPF: €{payroll.irpf_retencion_monetaria:.2f}")
            lines.append("")  # Blank line between payrolls
        return "\n".join(lines)

    def _format_payslip_results(self, results: List[Dict], processed_count: int, failed_count: int, total_time: float) -> str:
        """Format payslip processing results in human-readable format"""
        if not results:
            return "No payslips processed."

        lines = []

        if processed_count > 0:
            lines.append(f"\n✅ Successfully processed {processed_count} payslip(s):\n")
            for r in results:
                if r.get('status') == 'processed':
                    emp_name = r.get('employee', 'Unknown')
                    period = r.get('period', 'Unknown')
                    gross = r.get('gross')
                    net = r.get('net')
                    concepts = r.get('concepts', 0)

                    # Parse period (format: "YYYY-MM")
                    period_display = period
                    if period and '-' in period:
                        try:
                            from datetime import datetime
                            y, m = period.split('-')
                            dt = datetime(int(y), int(m), 1)
                            period_display = dt.strftime('%B %Y')
                        except:
                            pass

                    lines.append(f"  • {emp_name} - {period_display}")
                    if gross:
                        lines.append(f"    Gross: €{gross:.2f}" + (f" | Net: €{net:.2f}" if net else ""))
                    lines.append(f"    Concepts extracted: {concepts}")
                    lines.append("")

        if failed_count > 0:
            lines.append(f"\n⚠️  Failed to process {failed_count} payslip(s):\n")
            for r in results:
                if r.get('status') != 'processed':
                    emp_name = r.get('employee', 'Unknown')
                    status = r.get('status', 'unknown_error')
                    lines.append(f"  • {emp_name}: {status}")
            lines.append("")

        lines.append(f"⏱️  Processing time: {total_time:.1f}s")

        return "\n".join(lines)

    def _format_missing_payslips(self, missing_data: Dict) -> str:
        """Format missing payslips report in human-readable format"""
        if not missing_data or not missing_data.get('employees'):
            return "\n✅ No missing payslips detected!"

        lines = [f"\n⚠️  Missing Payslips Report:\n"]

        for emp_data in missing_data.get('employees', []):
            emp_name = emp_data.get('name', 'Unknown')
            emp_id = emp_data.get('identity_card_number', '')
            missing = emp_data.get('missing_payslips', [])

            if missing:
                lines.append(f"  👤 {emp_name} ({emp_id}):")
                lines.append(f"     Missing {len(missing)} payslip(s):\n")

                for period in missing:
                    period_str = period.get('period', '')
                    start = period.get('period_start', '')
                    end = period.get('period_end', '')

                    # Format dates nicely
                    date_range = f"{start} to {end}" if start and end else period_str
                    lines.append(f"       • {period_str} ({date_range})")

                lines.append("")

        return "\n".join(lines)

    def _format_processing_summary(self, db_summary: Dict) -> str:
        """Format processing/database summary in human-readable format"""
        lines = ["\n📊 Database Summary:\n"]

        if 'total_clients' in db_summary:
            lines.append(f"  • Companies: {db_summary['total_clients']}")
        if 'total_employees' in db_summary:
            lines.append(f"  • Employees: {db_summary['total_employees']}")
        if 'total_payrolls' in db_summary:
            lines.append(f"  • Payrolls: {db_summary['total_payrolls']}")

        # Show current client stats if available
        if db_summary.get('current_client_employees', 0) > 0:
            lines.append(f"\n  Current company:")
            lines.append(f"    • Employees: {db_summary['current_client_employees']}")
            lines.append(f"    • Payrolls: {db_summary['current_client_payrolls']}")

        return "\n".join(lines)

    def _detect_file_paths(self, user_input: str, debug: bool = False) -> Dict[str, List[str]]:
        """Detect and validate file paths and directories in user input"""
        detected_files = {
            'csv_files': [],
            'pdf_files': [],
            'zip_files': [],
            'directories': [],
            'invalid_files': []
        }

        # Enhanced patterns to detect file paths (ordered by priority)
        patterns = [
            r'"([^"]+\.[a-zA-Z0-9]+)"',                           # Quoted paths
            r"'([^']+\.[a-zA-Z0-9]+)'",                           # Single quoted paths
            r'(\./[^\s]+\.[a-zA-Z0-9]+)',                         # Relative paths starting with ./
            r'([a-zA-Z0-9_][a-zA-Z0-9_/-]*[a-zA-Z0-9_]/[^\s]*\.[a-zA-Z0-9]+)',  # Relative paths like test_data/file.csv
            r'(/[a-zA-Z0-9_][^\s]*\.[a-zA-Z0-9]+)',               # Absolute paths starting with /
            r'\b([a-zA-Z0-9_-]+\.[a-zA-Z0-9]+)\b',                # Simple filenames (word boundaries)
        ]

        # Also detect directory paths (paths without extensions)
        directory_patterns = [
            r'"([^"]+/)"',                                        # Quoted directory paths ending in /
            r"'([^']+/)'",                                        # Single quoted directory paths
            r'(/[a-zA-Z0-9_][^\s]*(?:test_data|payslips|data|docs)[^\s]*)',  # Paths with common directory names
            r'(\./[^\s\.]+/?)',                                   # Relative paths starting with ./ without extension
            r'([a-zA-Z0-9_][a-zA-Z0-9_/-]*[a-zA-Z0-9_]/)',        # Directory-like paths ending in /
        ]

        potential_paths = []
        potential_dirs = []

        for pattern in patterns:
            matches = re.findall(pattern, user_input)
            potential_paths.extend(matches)

        for pattern in directory_patterns:
            matches = re.findall(pattern, user_input)
            potential_dirs.extend(matches)

        # Also check for glob patterns like *.pdf
        glob_patterns = re.findall(r'(\*\.[a-zA-Z0-9]+)', user_input)
        for pattern in glob_patterns:
            try:
                expanded_files = glob.glob(pattern)
                potential_paths.extend(expanded_files)
            except Exception:  # noqa: E722
                pass

        # Debug output
        if debug:
            print(f"DEBUG: Input: {user_input}")
            print(f"DEBUG: Potential file paths found: {potential_paths}")
            print(f"DEBUG: Potential directory paths found: {potential_dirs}")
            print(f"DEBUG: Current working directory: {os.getcwd()}")

        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in potential_paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)

        unique_dirs = []
        for path in potential_dirs:
            if path not in seen:
                seen.add(path)
                unique_dirs.append(path)

        # Validate and categorize files
        allowed_extensions = {'.csv', '.pdf', '.zip'}
        for path in unique_paths:
            path = path.strip().strip(".,;:")
            if not path:
                continue

            ext = Path(path).suffix.lower()
            # Only consider supported file types to avoid false positives (e.g., company names like "ACME S.L.")
            if ext and ext not in allowed_extensions:
                continue

            # Try multiple path resolution strategies
            cwd = os.getcwd()
            test_paths = [
                path,  # Original path (might be absolute)
                os.path.abspath(path),  # Absolute path from CWD
                os.path.join(cwd, path),  # Explicitly join with CWD
                os.path.join(cwd, 'test_data', path),  # Try test_data subdirectory
                os.path.join(cwd, 'data', path),  # Try data subdirectory
            ]

            # Handle pseudo-absolute paths like /test_data/file.pdf
            # These look absolute but are actually project-relative
            if path.startswith('/'):
                stripped_path = path.lstrip('/')
                # Try as relative path
                test_paths.extend([
                    os.path.join(cwd, stripped_path),
                    stripped_path  # Also try from current location
                ])

            found = False
            found_path = None
            for test_path in test_paths:
                if os.path.exists(test_path):
                    ext = Path(test_path).suffix.lower()
                    if debug:
                        print(f"DEBUG: {path} -> {test_path} (exists: True, ext: {ext})")

                    found_path = test_path
                    found = True
                    break

            if found:
                # Use found absolute path for processing
                if ext == '.csv':
                    detected_files['csv_files'].append(found_path)
                elif ext == '.pdf':
                    detected_files['pdf_files'].append(found_path)
                elif ext == '.zip':
                    detected_files['zip_files'].append(found_path)

            if not found:
                # Only flag as invalid if it matches supported extensions
                if ext in allowed_extensions:
                    if debug:
                        abs_path = os.path.abspath(path)
                        print(f"DEBUG: {path} -> {abs_path} (exists: False)")
                    detected_files['invalid_files'].append(path)

        # Validate and categorize directories
        for dir_path in unique_dirs:
            dir_path = dir_path.strip().strip(".,;:")
            if not dir_path:
                continue

            cwd = os.getcwd()
            test_paths = [
                dir_path,
                os.path.abspath(dir_path),
                os.path.join(cwd, dir_path),
                os.path.join(cwd, 'test_data', dir_path),
                os.path.join(cwd, 'data', dir_path),
            ]

            # Handle pseudo-absolute directory paths
            if dir_path.startswith('/'):
                stripped_path = dir_path.lstrip('/')
                test_paths.extend([
                    os.path.join(cwd, stripped_path),
                    stripped_path
                ])

            for test_path in test_paths:
                if os.path.exists(test_path) and os.path.isdir(test_path):
                    if debug:
                        print(f"DEBUG: {dir_path} -> {test_path} (exists: True, is_dir: True)")
                    detected_files['directories'].append(test_path)
                    break

        return detected_files

    def _collect_pdfs_from_paths(self, paths: List[str]) -> List[str]:
        """
        Collect all PDF files from a mix of PDF files, directories, and ZIP archives.

        Args:
            paths: List of paths that can be:
                - Individual PDF files
                - Directories (will recursively find all PDFs)
                - ZIP files (will extract and find PDFs)

        Returns:
            Flat list of absolute paths to PDF files
        """
        pdf_files = []

        for path in paths:
            if not os.path.exists(path):
                print(f"⚠️  Path does not exist: {path}")
                continue

            # Handle directories - recursively find all PDFs
            if os.path.isdir(path):
                print(f"📁 Scanning directory: {path}")
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            full_path = os.path.join(root, file)
                            pdf_files.append(full_path)
                print(f"   Found {len([f for f in pdf_files if f.startswith(path)])} PDF(s)")

            # Handle ZIP files - extract and get PDFs
            elif path.lower().endswith('.zip'):
                print(f"📦 Extracting ZIP: {path}")
                result = self.extract_files_from_zip(path)
                if result.get('success'):
                    extracted_pdfs = result.get('pdf_files', [])
                    pdf_files.extend(extracted_pdfs)
                    print(f"   Extracted {len(extracted_pdfs)} PDF(s)")
                else:
                    print(f"   ❌ Failed to extract: {result.get('error', 'Unknown error')}")

            # Handle individual PDF files
            elif path.lower().endswith('.pdf'):
                pdf_files.append(path)

            else:
                print(f"⚠️  Skipping unsupported file: {path}")

        return pdf_files

    def _auto_process_detected_files(self, detected_files: Dict[str, List[str]]) -> Optional[str]:
        """Auto-process detected files based on workflow state"""
        results = []

        # Process vida laboral CSV if detected and not yet processed
        if detected_files['csv_files'] and not self.processing_state['vida_laboral_processed']:
            csv_file = detected_files['csv_files'][0]  # Take first CSV file
            results.append(f"🔍 Auto-detected vida laboral CSV: {csv_file}")
            result = self.process_vida_laboral_csv(csv_file)
            results.append(f"🔧 process_vida_laboral_csv: {result.get('message', 'Completed')}")

            if result.get('success'):
                next_step = self._get_next_workflow_step()
                if next_step:
                    results.append(f"\n➡️  {next_step}")

            return "\n".join(results)

        # Process nominas if detected and vida laboral is ready
        if self.processing_state['vida_laboral_processed']:
            paths_to_process = []

            # Collect all paths: PDFs, ZIPs, and directories
            if detected_files['zip_files']:
                paths_to_process.extend(detected_files['zip_files'])
                results.append(f"🔍 Auto-detected {len(detected_files['zip_files'])} ZIP file(s)")

            if detected_files['pdf_files']:
                paths_to_process.extend(detected_files['pdf_files'])
                results.append(f"🔍 Auto-detected {len(detected_files['pdf_files'])} PDF file(s)")

            if detected_files['directories']:
                paths_to_process.extend(detected_files['directories'])
                results.append(f"🔍 Auto-detected {len(detected_files['directories'])} directory(ies)")

            # Process all collected paths (expansion happens in process_payslip_batch)
            if paths_to_process:
                process_result = self.process_payslip_batch(paths_to_process)
                results.append(f"🔧 process_payslip_batch: {process_result.get('message', 'Completed')}")

                if process_result.get('success'):
                    # Auto-generate processing report
                    report_result = self.generate_processing_report(output_format="json", save_to_file=True)
                    results.append(f"🔧 generate_processing_report: {report_result.get('message', 'Completed')}")

                    # Auto-generate missing payslips report
                    missing_result = self.generate_missing_payslips_report(output_format="json", save_to_file=True)
                    results.append(f"🔧 generate_missing_payslips_report: {missing_result.get('message', 'Completed')}")

                    results.append("\n✅ **Workflow Complete!** All reports generated successfully.")
                    results.append("💡 You can process more files or type 'quit' to exit.")

                return "\n".join(results)

        # Handle invalid files
        if detected_files['invalid_files']:
            invalid_list = "\n".join([f"  ❌ {f}" for f in detected_files['invalid_files']])
            return f"⚠️  Some files were not found:\n{invalid_list}\n\n💡 Please check the file paths and try again."

        return None

    def _get_next_workflow_step(self) -> Optional[str]:
        """Get the next step in the workflow - only for file processing mode"""
        # Only suggest workflow steps if user seems to be in file processing mode
        # Don't force it on CRUD operations
        if not self.processing_state['vida_laboral_processed']:
            return None  # Don't force CSV on every interaction
        elif self.processing_state['vida_laboral_processed'] and not self.processing_state['nominas_processed']:
            return "Next: Provide nominas PDF files or ZIP file paths (or ask me to manage database instead)"
        elif self.processing_state['nominas_processed'] > 0:
            return None  # Workflow complete, don't force more
        return None

    def run_conversation(self, user_input: str) -> str:
        """Main conversation loop with OpenAI function calling"""
        try:
            # Handle meta commands first
            user_input_lower = user_input.lower().strip()

            # Show details / raw JSON of last operation
            if user_input_lower in ['show details', 'show json', 'show raw', 'show last result', 'details']:
                if self.last_tool_result:
                    func_name = self.last_tool_result.get('function', 'Unknown')
                    result = self.last_tool_result.get('result', {})
                    timestamp = self.last_tool_result.get('timestamp', 'Unknown')

                    response = f"📋 Last Operation: {func_name}\n"
                    response += f"⏰ Timestamp: {timestamp}\n\n"
                    response += "```json\n"
                    response += json.dumps(result, indent=2, ensure_ascii=False, default=str)
                    response += "\n```"

                    return response
                else:
                    return "ℹ️  No previous operation to show details for."

            # Enable verbose mode
            if user_input_lower in ['enable verbose', 'verbose on', 'verbose mode on', 'set verbose']:
                self.verbose_mode = True
                return "✅ Verbose mode enabled. Will show technical details with all outputs.\n💡 Use 'disable verbose' to turn off."

            # Disable verbose mode
            if user_input_lower in ['disable verbose', 'verbose off', 'verbose mode off', 'unset verbose']:
                self.verbose_mode = False
                return "✅ Verbose mode disabled. Showing clean output only.\n💡 Use 'enable verbose' to show technical details."

            # Check for inline verbose request
            force_verbose = any(keyword in user_input_lower for keyword in [
                ' verbose', ' with details', ' show json', ' raw', ' technical'
            ])

            # Detect file paths in user input
            detected_files = self._detect_file_paths(user_input)

            # Build user message with detected file context and store it
            user_message_content = f"""User input: {user_input}

Detected files:
- CSV files: {detected_files['csv_files']}
- PDF files: {detected_files['pdf_files']}
- ZIP files: {detected_files['zip_files']}
- Directories: {detected_files['directories']}
- Invalid files: {detected_files['invalid_files']}"""
            self._append_conversation_message("user", user_message_content)

            # Auto-progression: Process files immediately if detected
            auto_result = self._auto_process_detected_files(detected_files)
            if auto_result:
                self._append_conversation_message("assistant", auto_result)
                return auto_result

            # Build conversation context with strong system prompt
            messages = [
                {
                    "role": "system",
                    "content": """You are **ValerIA AI**, an autonomous AI assistant that processes Spanish payroll documents.

# LANGUAGE
– Always respond in English
– Process Spanish documents but communicate in English only
– Use English for all error messages, guidance, and responses
– Never switch to Spanish regardless of document content

# PERSISTENCE
– Stay in the conversation until payroll processing is complete; never abandon midway.
– Preserve and reuse processing state (vida_laboral_processed, client_id, employees_created, nominas_processed).

# TOOL DISCIPLINE
– If you need to process files, CALL THE RELEVANT TOOL; do **not** guess.

# OPERATION MODES
The agent supports TWO main modes of operation. Intelligently detect user intent:

## MODE 1: PAYROLL PROCESSING WORKFLOW (File-Based)
When user mentions files, documents, processing, or wants to import data:

  1️⃣ If vida laboral CSV mentioned → call **process_vida_laboral_csv**
  2️⃣ After CSV success → ask for nominas (PDFs or ZIP file)
  3️⃣ If ZIP provided → call **extract_files_from_zip** then **process_payslip_batch**
  4️⃣ If PDFs provided → call **process_payslip_batch** directly
  5️⃣ After processing → call **generate_processing_report** (JSON format)
  6️⃣ Then call **generate_missing_payslips_report** (JSON format)
  7️⃣ Ask if user wants to process more files

## MODE 2: DATABASE MANAGEMENT (CRUD Operations)
When user wants to query, manage, or interact with existing data:

  ✅ **Query Operations**: list_clients, list_employees, list_payrolls, search_employees, get_database_stats
  ✅ **Create Operations**: create_client, create_employee, create_payroll
  ✅ **Update Operations**: update_employee, update_client, update_payroll
  ✅ **Delete Operations**: delete_employee, delete_client, delete_payroll

**Examples of MODE 2 user requests:**
  – "Show me all employees"
  – "Create a new company called ACME"
  – "Search for employees named García"
  – "Update Juan's salary to 2500"
  – "Delete employee ID 123"
  – "Show database statistics"
  – "List all payrolls for 2025"

## INTELLIGENT MODE DETECTION

**Detect MODE 1 (File Processing) when user:**
  – Mentions file paths (.csv, .pdf, .zip)
  – Says: "process", "import", "load", "upload", "extract"
  – Provides vida laboral or nominas files
  – Wants to digitize payroll documents

**Detect MODE 2 (Database Operations) when user:**
  – Asks about existing data ("show", "list", "find", "search")
  – Wants to create/update/delete records
  – Asks for statistics or summaries
  – Makes database queries
  – Doesn't mention files

**Can switch modes mid-conversation!** User can process files AND then query data in same session.

## ADAPTIVE GREETING

**First interaction:**
  – Don't immediately ask for CSV file
  – Ask: "What would you like to do today?"
  – Offer both options:
    • "Process payroll documents (vida laboral CSV + nominas PDFs)"
    • "Manage existing database (query, create, update employees/clients)"

**Follow user's lead** – let them decide the mode, don't force the workflow.

# CRUD OPERATION EXAMPLES

**User:** "Show me all employees"
**You:** [call list_employees] → Present results clearly

**User:** "Create a company called Tech Solutions with CIF B12345678"
**You:** [call create_client with name and cif] → Confirm creation

**User:** "Search for employees named García"
**You:** [call search_employees with query="García"] → Show results

**User:** "Update employee 123's salary to 2800"
**You:** [call update_employee with employee_id=123, salary=2800] → Show changes

**User:** "What's in the database?"
**You:** [call get_database_stats] → Show statistics

**Key principles:**
  – Call the appropriate tool immediately
  – Don't ask for confirmation before calling tools
  – Present results clearly and concisely
  – Offer to help with next action

# FILE HANDLING
– Accept file paths in conversation (absolute, relative, or just filenames)
– Validate file existence and guide user if files not found
– Auto-detect file types: .csv for vida laboral, .pdf/.zip for nominas
– Process files immediately when provided, don't wait for additional confirmation

# WORKFLOW PERSISTENCE
– In file processing mode, move to the next step after successful completion
– If errors occur, guide user to fix and retry, don't stop the workflow
– Remember processing state across conversation turns
– Surface workflow guidance only when the user is in file processing mode

# OUTPUT STYLING
– Format ALL responses in GitHub-flavored Markdown
– Use headers (##, ###) to organize sections
– Use bullet lists (-, *) or numbered lists for multiple items
– Use tables for structured/comparative data
– Use code blocks with language tags (```python, ```json, ```sql) for code/data
– Use **bold** for emphasis on key points
– Use `inline code` for technical terms, file paths, function names
– Use > blockquotes for important notes or warnings
– Show processing results as clear, well-formatted summaries
– Present errors with specific guidance for resolution
– Keep conversation professional and workflow-focused

# CURRENT STATE
"""f"""
Processing State: {self.processing_state}
Vida Laboral Processed: {self.processing_state['vida_laboral_processed']}
Employees Created: {self.processing_state['employees_created']}
Nominas Processed: {self.processing_state['nominas_processed']}
"""
                }
            ]

            if self.memory_summary:
                messages.append({
                    "role": "system",
                    "content": f"# MEMORY SUMMARY\n{self.memory_summary}"
                })

            messages.extend({
                "role": entry["role"],
                "content": entry["content"]
            } for entry in self.conversation_history)

            # Call OpenAI with function calling
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.3  # Lower temperature for more consistent workflow
            )

            message = response.choices[0].message

            # Handle function calls
            if message.tool_calls:
                results = []
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    # Call the appropriate tool function
                    if function_name == "process_vida_laboral_csv":
                        result = self.process_vida_laboral_csv(**function_args)
                    elif function_name == "extract_files_from_zip":
                        result = self.extract_files_from_zip(**function_args)
                    elif function_name == "process_payslip_batch":
                        result = self.process_payslip_batch(**function_args)
                    elif function_name == "generate_processing_report":
                        result = self.generate_processing_report(**function_args)
                        # Auto-generate missing payslips report after processing report
                        if result.get('success'):
                            missing_result = self.generate_missing_payslips_report(output_format="json", save_to_file=True)
                            results.append(f"🔧 generate_missing_payslips_report: {missing_result.get('message', 'Completed')}")
                    elif function_name == "generate_missing_payslips_report":
                        result = self.generate_missing_payslips_report(**function_args)
                    # CRUD Operations
                    elif function_name == "create_client":
                        result = self.create_client(**function_args)
                    elif function_name == "create_employee":
                        result = self.create_employee(**function_args)
                    elif function_name == "create_payroll":
                        result = self.create_payroll(**function_args)
                    elif function_name == "update_employee":
                        result = self.update_employee(**function_args)
                    elif function_name == "update_client":
                        result = self.update_client(**function_args)
                    elif function_name == "update_payroll":
                        result = self.update_payroll(**function_args)
                    elif function_name == "delete_employee":
                        result = self.delete_employee(**function_args)
                    elif function_name == "delete_client":
                        result = self.delete_client(**function_args)
                    elif function_name == "delete_payroll":
                        result = self.delete_payroll(**function_args)
                    elif function_name == "list_clients":
                        result = self.list_clients(**function_args)
                    elif function_name == "list_employees":
                        result = self.list_employees(**function_args)
                    elif function_name == "list_payrolls":
                        result = self.list_payrolls(**function_args)
                    elif function_name == "search_employees":
                        result = self.search_employees(**function_args)
                    elif function_name == "get_employee_payrolls":
                        result = self.get_employee_payrolls(**function_args)
                    elif function_name == "get_database_stats":
                        result = self.get_database_stats()
                    else:
                        result = {"success": False, "error": f"Unknown function: {function_name}"}

                    # Store result for on-demand access
                    from datetime import datetime
                    self.last_tool_result = {
                        'function': function_name,
                        'result': result,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    formatted_message = f"🔧 {function_name}: {result.get('message', 'Completed')}"
                    if result.get('error'):
                        formatted_message += f"\n❗ Error: {result['error']}"

                    # Use human-friendly formatters
                    if function_name == "list_clients" and result.get('success') and 'data' in result:
                        formatted_message += self._format_clients_list(result['data'], result.get('count', 0))
                    elif function_name == "list_employees" and result.get('success') and 'data' in result:
                        formatted_message += self._format_employees_list(result['data'], result.get('count', 0))
                    elif function_name == "search_employees" and result.get('success') and 'data' in result:
                        formatted_message += self._format_employees_list(result['data'], result.get('count', 0))
                    elif function_name == "list_payrolls" and result.get('success') and 'data' in result:
                        formatted_message += self._format_payrolls_list(result['data'], result.get('count', 0))
                    elif function_name == "process_payslip_batch" and result.get('success'):
                        formatted_message += self._format_payslip_results(
                            result.get('results', []),
                            result.get('processed_count', 0),
                            result.get('failed_count', 0),
                            result.get('total_time', 0)
                        )
                    elif function_name == "generate_missing_payslips_report" and result.get('success'):
                        # Read the saved report file to get missing payslips data
                        report_file = result.get('report_file')
                        if report_file and os.path.exists(report_file):
                            try:
                                with open(report_file, 'r') as f:
                                    missing_data = json.load(f)
                                formatted_message += self._format_missing_payslips(missing_data)
                            except Exception as e:
                                print(f"Warning: Could not format missing payslips: {e}")
                    elif function_name == "generate_processing_report" and result.get('success'):
                        formatted_message += self._format_processing_summary(result.get('database_summary', {}))
                    else:
                        # For other tools, show compact payload (not full JSON dump)
                        payload_keys = [
                            key for key in result.keys()
                            if key not in {"success", "message", "error", "data"} and result[key] not in (None, [], {})
                        ]
                        if payload_keys:
                            payload = {
                                key: self._serialize_tool_payload(result[key])
                                for key in payload_keys
                            }
                            try:
                                serialized_payload = json.dumps(
                                    payload,
                                    ensure_ascii=False,
                                    default=str,
                                    indent=2
                                )
                            except TypeError:
                                serialized_payload = str(payload)
                            formatted_message += f"\n📊 Result payload:\n{serialized_payload}"

                    # Add technical details if verbose mode or force_verbose
                    show_technical = self.verbose_mode or force_verbose
                    if show_technical:
                        formatted_message += "\n\n📋 Technical Details:"
                        formatted_message += "\n```json\n"
                        formatted_message += json.dumps(result, indent=2, ensure_ascii=False, default=str)
                        formatted_message += "\n```"
                        if not self.verbose_mode:
                            formatted_message += "\n\n💡 Tip: Use 'enable verbose' for persistent technical output"

                    results.append(formatted_message)

                    # Auto-progression: Move to next step after successful completion
                    if result.get('success'):
                        next_step = self._get_next_workflow_step()
                        if next_step:
                            results.append(f"\n➡️  Next step: {next_step}")

                assistant_response = "\n".join(results)
                if assistant_response.strip():
                    self._append_conversation_message("assistant", assistant_response)
                return assistant_response

            # Return regular response with workflow guidance
            response_content = message.content or ""

            # Provide workflow guidance only when in file processing mode
            next_step = self._get_next_workflow_step()
            if next_step:
                response_content += f"\n\n💡 {next_step}"

            if response_content.strip():
                self._append_conversation_message("assistant", response_content)

            return response_content

        except Exception as e:
            error_message = f"Error in conversation: {e}"
            self._append_conversation_message("assistant", error_message)
            return error_message

    def __del__(self):
        """Clean up database session"""
        if hasattr(self, 'session'):
            self.session.close()
