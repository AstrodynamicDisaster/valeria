#!/usr/bin/env python3
"""
ValerIA Database Setup Script
Creates tables, indexes, views, and seeds initial data.
This is an admin/setup script - not for runtime use.
"""

import os
import sys

# Add parent directory to path to import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import Index, text
from sqlalchemy.orm import sessionmaker

# Import from core module
from core.models import (
    Base, Client, Employee, VacationPeriod, NominaConcept, Document,
    Payroll, PayrollLine, ChecklistItem
)
from core.database import (
    create_database_engine, ensure_documents_directory,
    BASIC_NOMINA_CONCEPTS
)


def create_tables(engine):
    """Create all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("✓ Database tables created successfully!")


def create_indexes(engine):
    """Create performance indexes"""
    print("Creating database indexes...")

    indexes = [
        Index('idx_employees_company_id', Employee.company_id),
        Index('idx_employees_identity_card', Employee.identity_card_number),
        Index('idx_employees_status', Employee.employee_status),
        Index('idx_employees_dates', Employee.begin_date, Employee.end_date),
        Index('idx_vacation_periods_employee_id', VacationPeriod.employee_id),
        Index('idx_vacation_periods_dates', VacationPeriod.start_date, VacationPeriod.end_date),
        Index('idx_documents_client_id', Document.client_id),
        Index('idx_documents_employee_id', Document.employee_id),
        Index('idx_documents_status', Document.status),
        Index('idx_payrolls_employee_id', Payroll.employee_id),
        Index('idx_payrolls_created_at', Payroll.created_at),
        Index('idx_payroll_lines_payroll_id', PayrollLine.payroll_id),
        Index('idx_payroll_lines_category', PayrollLine.category),
        Index('idx_payroll_lines_concepto', PayrollLine.concepto),
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
        WITH payroll_periods AS (
            SELECT
                p.id,
                p.employee_id,
                COALESCE((p.periodo->>'hasta')::date, (p.periodo->>'desde')::date) AS period_date
            FROM payrolls p
        )
        SELECT
            e.company_id,
            e.id as employee_id,
            CONCAT(e.first_name, ' ', e.last_name, COALESCE(' ' || e.last_name2, '')) as full_name,
            COALESCE(EXTRACT(YEAR FROM pp.period_date), EXTRACT(YEAR FROM CURRENT_DATE))::int as period_year,
            COUNT(pp.id) as payrolls_received,
            FALSE as complete_year
        FROM employees e
        LEFT JOIN payroll_periods pp ON e.id = pp.employee_id
        WHERE e.employee_status = 'Active'
        GROUP BY e.company_id, e.id, e.first_name, e.last_name, e.last_name2, period_year
        ORDER BY e.company_id, full_name, period_year;
        """,

        # Model 111 quarterly data
        """
        CREATE OR REPLACE VIEW model111_quarterly_data AS
        WITH payroll_periods AS (
            SELECT
                p.id,
                p.employee_id,
                COALESCE((p.periodo->>'hasta')::date, (p.periodo->>'desde')::date) AS period_date,
                p.devengo_total,
                p.deduccion_total,
                p.aportacion_empresa_total,
                p.liquido_a_percibir
            FROM payrolls p
        )
        SELECT
            c.id as client_id,
            c.name as fiscal_name,
            c.cif,
            EXTRACT(YEAR FROM pp.period_date)::int as period_year,
            EXTRACT(QUARTER FROM pp.period_date)::int as period_quarter,
            COUNT(DISTINCT e.id) as employee_count,
            COUNT(pp.id) as payroll_count,
            SUM(COALESCE(pp.devengo_total, 0)) as devengo_total,
            SUM(COALESCE(pp.deduccion_total, 0)) as deduccion_total,
            SUM(COALESCE(pp.aportacion_empresa_total, 0)) as aportacion_empresa_total,
            SUM(COALESCE(pp.liquido_a_percibir, 0)) as liquido_total
        FROM clients c
        JOIN employees e ON c.id = e.company_id
        JOIN payroll_periods pp ON e.id = pp.employee_id
        WHERE c.active = true AND e.employee_status = 'Active' AND pp.period_date IS NOT NULL
        GROUP BY c.id, c.name, c.cif, period_year, period_quarter
        ORDER BY c.name, period_year, period_quarter;
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

    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
