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

from openai import OpenAI
from tqdm import tqdm
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Reuse existing modules
from .models import (
    Base, Client, Employee, Payroll, PayrollLine,
    NominaConcept, Document
)
from .database import create_database_engine
from .production_models import (
    create_production_engine, ProductionCompany, ProductionEmployee
)
from .process_payroll import extract_payroll_info


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

        # Cache for concept mappings
        self._concept_mappings = None

        # Define tools for OpenAI function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "process_vida_laboral_csv",
                    "description": "Process a vida laboral CSV file and insert employee records into database. Automatically extracts company name from test_data_summary.txt if available.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the vida laboral CSV file"
                            },
                            "client_name": {
                                "type": "string",
                                "description": "Name of the client company (optional, will try to infer from filename)"
                            }
                        },
                        "required": ["file_path"]
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
                    "description": "Process multiple nomina PDF files and extract payroll data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdf_files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of paths to PDF files to process"
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
        """Process vida laboral CSV file - reuses existing database models"""
        try:
            # Infer client name from filename if not provided
            if not client_name:
                filename = Path(file_path).stem

                # Try to find company name from test data summary file
                file_dir = Path(file_path).parent
                summary_file = file_dir / "test_data_summary.txt"

                if summary_file.exists():
                    try:
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.startswith("Company:"):
                                    client_name = line.split(":", 1)[1].strip()
                                    break
                    except Exception:
                        pass

                # Fallback: extract CCC code and use descriptive name
                if not client_name:
                    import re
                    ccc_match = re.search(r'(\d{14})', filename)
                    if ccc_match:
                        ccc_code = ccc_match.group(1)
                        client_name = f"Company CCC-{ccc_code}"
                    else:
                        client_name = f"Client from {filename}"

            # Create or get client (updated for new schema)
            client = self.session.query(Client).filter_by(name=client_name).first()  # Updated from fiscal_name
            if not client:
                client = Client(
                    id=str(uuid.uuid4()),  # UUID string to match production
                    name=client_name,  # Updated from fiscal_name
                    cif=f"B{uuid.uuid4().hex[:8].upper()}",  # Generate fake CIF
                    ccc_ss=f"{uuid.uuid4().hex[:14].upper()}",  # Generate fake CCC (local only)
                    fiscal_address="Calle Ficticia 123",
                    email=f"contact@{client_name.lower().replace(' ', '')[:20]}.com",
                    phone="34900000000",
                    active=True
                )
                self.session.add(client)
                self.session.commit()

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
                            company_id=client.id,  # Updated from client_id
                            first_name=first_name,
                            last_name=last_name,
                            last_name2=last_name2,
                            identity_card_number=documento,  # Updated from documento
                            identity_doc_type=identity_doc_type,
                            ss_number=f"SS{uuid.uuid4().hex[:10].upper()}",  # Updated from nss
                            active=(situacion == 'ALTA'),
                            begin_date=begin_date,  # Updated from employment_start_date
                            end_date=end_date,  # Updated from employment_end_date
                            salary=1500.00,  # Default salary
                            role="Empleado",  # Default role
                            employee_status='Active' if situacion == 'ALTA' else 'Terminated'
                        )
                        self.session.add(employee)
                        employees_created += 1
                    else:
                        # Update existing employee
                        employee.first_name = first_name
                        employee.last_name = last_name
                        employee.last_name2 = last_name2
                        employee.active = (situacion == 'ALTA')
                        employee.begin_date = begin_date
                        employee.end_date = end_date
                        employee.employee_status = 'Active' if situacion == 'ALTA' else 'Terminated'
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
            from datetime import date, timedelta
            from dateutil.relativedelta import relativedelta

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
        """Process multiple nomina PDFs - reuses existing process_payroll.py"""
        if not self.processing_state['vida_laboral_processed']:
            return {
                "success": False,
                "message": "Please process vida laboral CSV first to create employee records"
            }

        processed_count = 0
        failed_count = 0
        results = []

        # Initialize progress tracking
        total_files = len(pdf_files)
        start_time = time.time()

        print(f"🔄 Processing {total_files} nomina PDF files...")

        # Create progress bar
        with tqdm(total=total_files, desc="Processing nominas", unit="file") as pbar:
            for i, pdf_file in enumerate(pdf_files):
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

        print(f"\n✅ Processing completed!")
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
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
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
                except:
                    # If YYYY-MM-DD fails, try DD-MM-YYYY
                    try:
                        return datetime.strptime(date_str, '%d-%m-%Y').date()
                    except:
                        pass

            # Try DD/MM/YYYY format
            if '/' in date_str and len(date_str) == 10:
                return datetime.strptime(date_str, '%d/%m/%Y').date()

            return None
        except Exception:
            return None

    def _find_matching_employee(self, emp_info: Dict) -> Optional[Employee]:
        """Match extracted employee info with database records"""
        client_id = self.processing_state.get('client_id')
        if not client_id:
            return None

        name = emp_info.get('name', '').strip()
        emp_id = emp_info.get('id', '').strip()

        # Try to match by ID first
        if emp_id:
            employee = self.session.query(Employee).filter_by(
                client_id=client_id,
                documento=emp_id
            ).first()
            if employee:
                return employee

        # Try to match by name (fuzzy matching could be added here)
        if name:
            # Search across first_name and last_name fields
            from sqlalchemy import or_, func
            employee = self.session.query(Employee).filter(
                Employee.company_id == client_id,  # Updated from client_id
                or_(
                    Employee.first_name.ilike(f"%{name}%"),
                    Employee.last_name.ilike(f"%{name}%"),
                    func.concat(Employee.first_name, ' ', Employee.last_name).ilike(f"%{name}%")
                )
            ).first()
            if employee:
                return employee

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
                client_employees = self.session.query(Employee).filter_by(client_id=client_id).count()
                client_payrolls = self.session.query(Payroll).join(Employee).filter(
                    Employee.client_id == client_id
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
                "message": f"Processing report generated successfully" + (f" - Saved to {file_path}" if file_path else "")
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to generate report: {e}"
            }

    def _detect_file_paths(self, user_input: str, debug: bool = False) -> Dict[str, List[str]]:
        """Detect and validate file paths in user input"""
        detected_files = {
            'csv_files': [],
            'pdf_files': [],
            'zip_files': [],
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

        potential_paths = []
        for pattern in patterns:
            matches = re.findall(pattern, user_input)
            potential_paths.extend(matches)

        # Also check for glob patterns like *.pdf
        glob_patterns = re.findall(r'(\*\.[a-zA-Z0-9]+)', user_input)
        for pattern in glob_patterns:
            try:
                expanded_files = glob.glob(pattern)
                potential_paths.extend(expanded_files)
            except:
                pass

        # Debug output
        if debug:
            print(f"DEBUG: Input: {user_input}")
            print(f"DEBUG: Potential paths found: {potential_paths}")
            print(f"DEBUG: Current working directory: {os.getcwd()}")

        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in potential_paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)

        # Validate and categorize files
        for path in unique_paths:
            path = path.strip()

            # Try original path first, then absolute path
            test_paths = [path, os.path.abspath(path)]

            found = False
            for test_path in test_paths:
                if os.path.exists(test_path):
                    ext = Path(test_path).suffix.lower()
                    if debug:
                        print(f"DEBUG: {path} -> {test_path} (exists: True, ext: {ext})")

                    # Use original path for user-friendly display
                    if ext == '.csv':
                        detected_files['csv_files'].append(path)
                    elif ext == '.pdf':
                        detected_files['pdf_files'].append(path)
                    elif ext == '.zip':
                        detected_files['zip_files'].append(path)
                    found = True
                    break

            if not found:
                if debug:
                    abs_path = os.path.abspath(path)
                    print(f"DEBUG: {path} -> {abs_path} (exists: False)")
                detected_files['invalid_files'].append(path)

        return detected_files

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
            processed_files = []

            # Handle ZIP files first
            if detected_files['zip_files']:
                zip_file = detected_files['zip_files'][0]
                results.append(f"🔍 Auto-detected nominas ZIP: {zip_file}")
                extract_result = self.extract_files_from_zip(zip_file)
                results.append(f"🔧 extract_files_from_zip: {extract_result.get('message', 'Completed')}")

                if extract_result.get('success'):
                    pdf_files = extract_result.get('pdf_files', [])
                    if pdf_files:
                        processed_files.extend(pdf_files)

            # Add directly provided PDF files
            if detected_files['pdf_files']:
                processed_files.extend(detected_files['pdf_files'])
                results.append(f"🔍 Auto-detected {len(detected_files['pdf_files'])} PDF files")

            # Process all collected PDF files
            if processed_files:
                process_result = self.process_payslip_batch(processed_files)
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
        """Get the next step in the workflow"""
        if not self.processing_state['vida_laboral_processed']:
            return "Please provide a vida laboral CSV file path"
        elif self.processing_state['vida_laboral_processed'] and not self.processing_state['nominas_processed']:
            return "Please provide nominas PDF files or ZIP file paths"
        elif self.processing_state['nominas_processed'] > 0:
            return "Workflow complete! You can process more files or generate additional reports"
        return None

    def run_conversation(self, user_input: str) -> str:
        """Main conversation loop with OpenAI function calling"""
        try:
            # Detect file paths in user input
            detected_files = self._detect_file_paths(user_input)

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
– Tool sequence:
  1️⃣ Greet → ask for vida laboral CSV file path
  2️⃣ Once CSV provided → call **process_vida_laboral_csv** immediately
  3️⃣ After successful CSV processing → ask for nominas (PDFs or ZIP file)
  4️⃣ If ZIP provided → call **extract_files_from_zip** then **process_payslip_batch**
  5️⃣ If PDFs provided → call **process_payslip_batch** directly
  6️⃣ After processing → call **generate_processing_report** automatically (JSON format)
  7️⃣ Then call **generate_missing_payslips_report** automatically (JSON format)
  8️⃣ Ask if user wants to process more files or exit

# FILE HANDLING
– Accept file paths in conversation (absolute, relative, or just filenames)
– Validate file existence and guide user if files not found
– Auto-detect file types: .csv for vida laboral, .pdf/.zip for nominas
– Process files immediately when provided, don't wait for additional confirmation

# WORKFLOW PERSISTENCE
– Always move to next step after successful completion
– If errors occur, guide user to fix and retry, don't stop the workflow
– Remember processing state across conversation turns
– Show current workflow step and what's needed next

# OUTPUT STYLING
– Show processing results as clear summaries
– Present errors with specific guidance for resolution
– Keep conversation professional and workflow-focused

# CURRENT STATE
"""f"""
Processing State: {self.processing_state}
Vida Laboral Processed: {self.processing_state['vida_laboral_processed']}
Employees Created: {self.processing_state['employees_created']}
Nominas Processed: {self.processing_state['nominas_processed']}
"""
                },
                {
                    "role": "user",
                    "content": f"""User input: {user_input}

Detected files:
- CSV files: {detected_files['csv_files']}
- PDF files: {detected_files['pdf_files']}
- ZIP files: {detected_files['zip_files']}
- Invalid files: {detected_files['invalid_files']}"""
                }
            ]

            # Auto-progression: Process files immediately if detected
            auto_result = self._auto_process_detected_files(detected_files)
            if auto_result:
                return auto_result

            # Call OpenAI with function calling
            response = self.client.chat.completions.create(
                model="gpt-4.1",
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
                    else:
                        result = {"success": False, "error": f"Unknown function: {function_name}"}

                    results.append(f"🔧 {function_name}: {result.get('message', 'Completed')}")

                    # Auto-progression: Move to next step after successful completion
                    if result.get('success'):
                        next_step = self._get_next_workflow_step()
                        if next_step:
                            results.append(f"\n➡️  Next step: {next_step}")

                return "\n".join(results)

            # Return regular response with workflow guidance
            response_content = message.content

            # Add workflow guidance if no files detected and not processed
            if not any(detected_files.values()) and not self.processing_state['vida_laboral_processed']:
                response_content += "\n\n💡 **Next step**: Please provide the path to your vida laboral CSV file (e.g., `/path/to/vida_laboral.csv` or drag and drop the file path here)"
            elif self.processing_state['vida_laboral_processed'] and not self.processing_state['nominas_processed']:
                response_content += "\n\n💡 **Next step**: Please provide nominas PDF files or ZIP file paths (e.g., `/path/to/nominas.zip` or `/path/to/*.pdf`)"

            return response_content

        except Exception as e:
            return f"Error in conversation: {e}"

    def __del__(self):
        """Clean up database session"""
        if hasattr(self, 'session'):
            self.session.close()


def main():
    """Example usage"""
    import argparse
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    parser = argparse.ArgumentParser(description="ValerIA AI Agent for Spanish Payroll Processing")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY in .env file)")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")

    args = parser.parse_args()

    # Get API key from argument or environment variable
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ Error: OpenAI API key not found!")
        print("   Please either:")
        print("   1. Set OPENAI_API_KEY in your .env file")
        print("   2. Use --api-key argument")
        return

    agent = ValeriaAgent(api_key)

    if args.interactive:
        print("🤖 ValerIA Agent initialized. Type 'quit' to exit.")
        print("📋 Start by providing a vida laboral CSV file, then nominas PDFs or ZIP files.")

        while True:
            user_input = input("\n👤 You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break

            response = agent.run_conversation(user_input)
            print(f"\n🤖 ValerIA: {response}")
    else:
        print("Use --interactive for interactive mode")


if __name__ == "__main__":
    main()