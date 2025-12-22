#!/usr/bin/env python3
"""
Production Database Models (Read-Only)
Maps to the production Valeria database schema for companies and company_employees.
These models are READ-ONLY and should never be used for writes.
"""

import os
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String, Text, create_engine
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.orm import declarative_base, sessionmaker

from core.models import Client, ClientLocation

ProductionBase = declarative_base()


class ProductionCompany(ProductionBase):
    """Read-only model for production 'companies' table"""
    __tablename__ = 'companies'

    # Primary identification
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    cif = Column(String, nullable=False)

    # Contact and location
    fiscal_address = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    company_country = Column(String)
    company_city = Column(String)
    company_postal_code = Column(String)

    # Legal representative
    legal_repr_first_name = Column(String, nullable=False)
    legal_repr_last_name1 = Column(String, nullable=False)
    legal_repr_last_name2 = Column(String)
    legal_repr_nif = Column(String)
    legal_repr_role = Column(String)
    legal_repr_phone = Column(String)
    legal_repr_email = Column(String)

    # Status and metadata
    status = Column(String)
    begin_date = Column(DateTime, nullable=False)
    managed_by = Column(String)
    payslips = Column(String)  # boolean in prod
    created_at = Column(DateTime)

    def __repr__(self):
        return f"<ProductionCompany(id={self.id}, name={self.name}, cif={self.cif})>"

class ProductionLocation(ProductionBase):
    """Read-only model for production company locations table.

    Based on the columns in `location_table_example.csv`.
    """

    __tablename__ = "company_locations"

    id = Column(Numeric, primary_key=True)
    address = Column(String)
    postal_code = Column(String)
    city = Column(String)

    company_id = Column(String, nullable=False)

    deleted_at = Column(DateTime)
    created_at = Column(DateTime)

    # Social Security / CCC for the location
    ccc = Column(String)

    country = Column(String)
    red_authorisation_status = Column(String)
    agreement_id = Column(Numeric)
    regime = Column(String)
    professional_group = Column(String)
    municipality = Column(String)
    location_address_id = Column(String)

    def __repr__(self):
        return f"<ProductionLocation(id={self.id}, company_id={self.company_id}, ccc={self.ccc})>"


class ProductionEmployee(ProductionBase):
    """Read-only model for production 'company_employees' table"""
    __tablename__ = 'company_employees'

    # Primary identification
    id = Column(Numeric, primary_key=True)
    company_id = Column(String, nullable=False)

    # Personal information
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    last_name2 = Column(String)
    identity_card_number = Column(String, nullable=False)
    identity_doc_type = Column(String)
    ss_number = Column(String, nullable=False)
    birth_date = Column(Date)
    sex = ENUM('male', 'female', name='sex_enum', create_type=False)
    nationality = Column(String)

    # Contact information
    address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    mail = Column(String, nullable=False)
    location_address = Column(String)

    # Employment details
    begin_date = Column(Date, nullable=False)
    end_date = Column(Date)
    salary = Column(Numeric, nullable=False)
    role = Column(String, nullable=False)
    salary_frequency = Column(String)
    weekly_hours = Column(Numeric)
    employee_status = Column(String)
    contribution_group = Column(String)

    # Additional fields
    education_level = Column(String)
    education_level_key = Column(String)
    employee_location = Column(String)
    contract_code = Column(String)
    bank_account = Column(String)
    created_at = Column(DateTime)
    registered_by = Column(String)

    def __repr__(self):
        return f"<ProductionEmployee(id={self.id}, name={self.first_name} {self.last_name}, identity_card={self.identity_card_number})>"


class ProductionEmployeeTermination(ProductionBase):
    """Read-only model for production 'company_employee_termination' table."""

    __tablename__ = "company_employee_termination"

    employee_id = Column(Integer, nullable=False)
    old_id = Column(Integer, nullable=False)
    date_of_termination = Column(Date, nullable=False)
    created_at = Column(DateTime)
    termination_type = Column(String(255), nullable=False)
    notice_period = Column(Integer)
    id = Column(String(16), primary_key=True)
    pending_vacation_days = Column(Numeric(5, 2), default=0)
    certifica_resolution_file_id = Column(String)
    certifica_sent_at = Column(DateTime)
    deleted_at = Column(DateTime)
    details = Column(Text)

    def __repr__(self):
        return (
            f"<ProductionEmployeeTermination(id={self.id}, employee_id={self.employee_id}, "
            f"termination_type={self.termination_type})>"
        )


class ProductionEmployeeContractHistory(ProductionBase):
    """Read-only model for production 'employee_contract_history' table."""

    __tablename__ = "employee_contract_history"

    id = Column(String(255), primary_key=True)
    company_employee_id = Column(String(255), nullable=False)
    change_code = Column(String(32), nullable=False)
    description = Column(String(255))
    new_value = Column(JSONB, nullable=False)
    previous_value = Column(JSONB, nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    effective_date = Column(Date)
    employee_document_id = Column(String(255))

    def __repr__(self):
        return (
            f"<ProductionEmployeeContractHistory(id={self.id}, employee_id={self.company_employee_id}, "
            f"change_code={self.change_code})>"
        )


class ProductionEmploymentContract(ProductionBase):
    """Read-only model for production 'employment_contract' table."""

    __tablename__ = "employment_contract"

    id = Column(String(16), primary_key=True)
    employee_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    status = Column(Integer, nullable=False)
    update_time = Column(DateTime, nullable=False)
    signature_id = Column(Numeric)
    signature_landing_url = Column(Text)
    deleted_at = Column(DateTime)

    def __repr__(self):
        return (
            f"<ProductionEmploymentContract(id={self.id}, employee_id={self.employee_id}, status={self.status})>"
        )


def create_production_engine(database_url: str = None, echo: bool = False):
    """
    Create read-only engine for production database.
    Uses PROD_URL from environment if not provided.
    """
    if database_url is None:
        database_url = os.getenv('PROD_URL')
        if not database_url:
            raise ValueError("PROD_URL not found in environment variables")

    # Create engine with read-only intent
    engine = create_engine(database_url, echo=echo, pool_pre_ping=True)
    return engine


def create_production_session(engine=None):
    """Create a session for production database queries"""
    if engine is None:
        engine = create_production_engine()

    Session = sessionmaker(bind=engine)
    return Session()


# Utility functions for common queries

def get_production_company_by_cif(session, cif: str) -> ProductionCompany:
    """Get company from production by CIF"""
    return session.query(ProductionCompany).filter_by(cif=cif).all()


def get_production_company_by_id(session, company_id: str) -> ProductionCompany:
    """Get company from production by ID"""
    return session.query(ProductionCompany).filter_by(id=company_id).first()


def get_production_employee_by_identity_card(session, identity_card: str) -> ProductionEmployee:
    """Get employee from production by identity card number"""
    return session.query(ProductionEmployee).filter_by(identity_card_number=identity_card).first()


def list_production_employees_for_company(session, company_id: str):
    """List all employees for a company in production"""
    return session.query(ProductionEmployee).filter_by(company_id=company_id).all()


def list_production_locations_for_company(session, company_id: str, include_deleted: bool = False):
    """List all locations for a company in production."""
    query = session.query(ProductionLocation).filter_by(company_id=company_id)
    if not include_deleted:
        query = query.filter(ProductionLocation.deleted_at.is_(None))
    return query.all()


def _coerce_prod_bool(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    raw = str(value).strip().lower()
    if raw in {"true", "t", "1", "yes", "y"}:
        return True
    if raw in {"false", "f", "0", "no", "n"}:
        return False
    return None


def insert_company_locations_into_local_clients(
    prod_session,
    cif: str,
    local_session=None,
    *,
    commit: bool = True,
    skip_existing: bool = True,
    include_deleted_locations: bool = False,
):
    """Insert a production company into local Client and ClientLocation tables.

    Steps:
    - Fetch the production company with `get_production_company_by_cif`
    - Create or update ONE Client record (unique by CIF)
    - Fetch all production locations for that company ID
    - For each location, create a ClientLocation with the CCC
    """

    owns_local_session = local_session is None
    if local_session is None:
        from core.database import get_session

        local_session = get_session(echo=False)

    try:
        prod_companies = get_production_company_by_cif(prod_session, cif)
        if not prod_companies:
            raise ValueError(f"No production company found for CIF={cif!r}")

        prod_company = prod_companies[0]
        company_id = prod_company.id

        # Get or create the Client record (one per CIF)
        client = local_session.query(Client).filter_by(cif=cif).first()
        if client is None:
            client = Client(id=uuid4(), cif=cif)
            local_session.add(client)

        # Update client data from production
        client.name = prod_company.name
        client.fiscal_address = prod_company.fiscal_address
        client.email = prod_company.email
        client.phone = prod_company.phone
        client.begin_date = prod_company.begin_date
        client.managed_by = prod_company.managed_by
        client.payslips = _coerce_prod_bool(getattr(prod_company, "payslips", None))

        client.legal_repr_first_name = prod_company.legal_repr_first_name
        client.legal_repr_last_name1 = prod_company.legal_repr_last_name1
        client.legal_repr_last_name2 = prod_company.legal_repr_last_name2
        client.legal_repr_nif = prod_company.legal_repr_nif
        client.legal_repr_role = prod_company.legal_repr_role
        client.legal_repr_phone = prod_company.legal_repr_phone
        client.legal_repr_email = prod_company.legal_repr_email

        client.status = prod_company.status

        local_session.flush()  # Ensure client.id is available

        # Get production locations and create ClientLocation records
        prod_locations = list_production_locations_for_company(
            prod_session,
            company_id,
            include_deleted=include_deleted_locations,
        )

        locations_created = []
        for loc in prod_locations:
            ccc = (loc.ccc or "").strip()
            if not ccc:
                continue

            # Check if location already exists
            existing_location = local_session.query(ClientLocation).filter_by(ccc_ss=ccc).first()
            if existing_location:
                if skip_existing:
                    continue
                # Update existing location to point to this client
                existing_location.company_id = client.id
            else:
                # Create new location
                location = ClientLocation(company_id=client.id, ccc_ss=ccc)
                local_session.add(location)
                locations_created.append(location)

        if commit:
            local_session.commit()
        else:
            local_session.flush()

        return {"client": client, "locations_created": len(locations_created)}
    finally:
        if owns_local_session:
            local_session.close()


if __name__ == "__main__":
    """Test production connection and models"""
    try:
        print("Testing production database connection...")
        engine = create_production_engine(echo=True)
        session = create_production_session(engine)

        # Test query
        companies = session.query(ProductionCompany).limit(2).all()
        print(f"\nFound {len(companies)} companies:")
        for company in companies:
            print(f"  - {company.name} (CIF: {company.cif})")

            # Get employees for first company
            if companies:
                employees = list_production_employees_for_company(session, companies[0].id)
                print(f"\nFirst company has {len(employees)} employees")
                for emp in employees[:3]:
                    print(f"  - {emp.first_name} {emp.last_name} ({emp.identity_card_number})")

        session.close()
        print("\n✓ Production database connection successful!")

    except Exception as e:
        print(f"\n✗ Error connecting to production database: {e}")
