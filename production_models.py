#!/usr/bin/env python3
"""
Production Database Models (Read-Only)
Maps to the production Valeria database schema for companies and company_employees.
These models are READ-ONLY and should never be used for writes.
"""

import os
from sqlalchemy import Column, String, Date, Numeric, DateTime, create_engine
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import declarative_base, sessionmaker

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
    return session.query(ProductionCompany).filter_by(cif=cif).first()


def get_production_company_by_id(session, company_id: str) -> ProductionCompany:
    """Get company from production by ID"""
    return session.query(ProductionCompany).filter_by(id=company_id).first()


def get_production_employee_by_identity_card(session, identity_card: str) -> ProductionEmployee:
    """Get employee from production by identity card number"""
    return session.query(ProductionEmployee).filter_by(identity_card_number=identity_card).first()


def list_production_employees_for_company(session, company_id: str):
    """List all employees for a company in production"""
    return session.query(ProductionEmployee).filter_by(company_id=company_id).all()


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
