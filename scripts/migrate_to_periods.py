#!/usr/bin/env python3
"""
Migration Script: Employee Periods Refactoring (Simplified)

This script prepares the database for the new EmployeePeriod structure:
1. Creates the employee_periods table
2. Drops old columns from employees table
3. Drops vacation_periods table

After running this script, reprocess the vida laboral CSV to populate periods.

IMPORTANT: Make a database backup before running!
"""

import os
import sys
from datetime import datetime

# Add parent directory to path to import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect

from core.database import create_database_engine
from core.models import Base, EmployeePeriod


def create_employee_periods_table(engine):
    """Create the employee_periods table."""
    print("\n" + "="*70)
    print("STEP 1: CREATING EMPLOYEE_PERIODS TABLE")
    print("="*70)

    # Create only the EmployeePeriod table
    EmployeePeriod.__table__.create(engine, checkfirst=True)
    print("✓ employee_periods table created")

    # Create indexes
    with engine.connect() as conn:
        print("\nCreating indexes...")

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_employee_periods_employee_id ON employee_periods(employee_id)",
            "CREATE INDEX IF NOT EXISTS idx_employee_periods_company_id ON employee_periods(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_employee_periods_dates ON employee_periods(period_begin_date, period_end_date)",
            "CREATE INDEX IF NOT EXISTS idx_employee_periods_type ON employee_periods(period_type)",
        ]

        for idx_sql in indexes:
            conn.execute(text(idx_sql))
            print(f"  ✓ Created index")

        conn.commit()

    print("\n✓ Indexes created")


def drop_old_employees_columns(engine):
    """Drop old columns from employees table."""
    print("\n" + "="*70)
    print("STEP 2: DROPPING OLD COLUMNS FROM EMPLOYEES TABLE")
    print("="*70)

    columns_to_drop = [
        'company_id',
        'begin_date',
        'end_date',
        'employee_status',
        'tipo_contrato',
        'salary',
        'role'
    ]

    with engine.connect() as conn:
        for column in columns_to_drop:
            try:
                conn.execute(text(f"ALTER TABLE employees DROP COLUMN IF EXISTS {column} CASCADE"))
                print(f"  ✓ Dropped column: {column}")
            except Exception as e:
                print(f"  ⚠️  Error dropping column {column}: {e}")

        conn.commit()

    print("\n✓ Old columns dropped from employees table")


def drop_vacation_periods_table(engine):
    """Drop the vacation_periods table."""
    print("\n" + "="*70)
    print("STEP 3: DROPPING VACATION_PERIODS TABLE")
    print("="*70)

    with engine.connect() as conn:
        try:
            conn.execute(text("DROP TABLE IF EXISTS vacation_periods CASCADE"))
            conn.commit()
            print("✓ vacation_periods table dropped")
        except Exception as e:
            print(f"⚠️  Error dropping vacation_periods table: {e}")


def verify_schema(engine):
    """Verify the new schema."""
    print("\n" + "="*70)
    print("STEP 4: VERIFYING SCHEMA")
    print("="*70)

    inspector = inspect(engine)

    # Check employee_periods table exists
    tables = inspector.get_table_names()
    if 'employee_periods' in tables:
        print("✓ employee_periods table exists")

        columns = [col['name'] for col in inspector.get_columns('employee_periods')]
        print(f"  Columns: {', '.join(columns)}")
    else:
        print("❌ employee_periods table NOT found!")

    # Check employees table schema
    print("\nEmployees table:")
    if 'employees' in tables:
        emp_columns = [col['name'] for col in inspector.get_columns('employees')]
        print(f"  Columns: {', '.join(emp_columns)}")

        old_columns = ['company_id', 'begin_date', 'end_date', 'employee_status',
                      'tipo_contrato', 'salary', 'role']
        remaining = [col for col in old_columns if col in emp_columns]

        if remaining:
            print(f"  ⚠️  WARNING: Old columns still exist: {remaining}")
        else:
            print("  ✓ All old columns removed")

    # Check vacation_periods is gone
    if 'vacation_periods' in tables:
        print("\n⚠️  WARNING: vacation_periods table still exists")
    else:
        print("\n✓ vacation_periods table removed")

    print("\n" + "="*70)
    print("SCHEMA VERIFICATION COMPLETE")
    print("="*70)


def main():
    """Run the migration."""
    print("\n" + "="*70)
    print("EMPLOYEE PERIODS MIGRATION SCRIPT (SIMPLIFIED)")
    print("="*70)
    print("\nThis script will:")
    print("1. Create the employee_periods table")
    print("2. Drop old columns from employees table:")
    print("   - company_id, begin_date, end_date, employee_status")
    print("   - tipo_contrato, salary, role")
    print("3. Drop vacation_periods table")
    print("\nAfter this migration:")
    print("- Employees table will only contain identity/contact info")
    print("- You MUST reprocess vida laboral CSV to populate periods")
    print("- Existing payroll data will be preserved")

    print("\n⚠️  WARNING: Make sure you have a database backup!")
    print("⚠️  Employee period data will be regenerated from vida laboral CSV!")

    response = input("\nType 'MIGRATE' to proceed: ")
    if response != 'MIGRATE':
        print("Migration aborted.")
        return

    try:
        # Create engine
        print("\nConnecting to database...")
        engine = create_database_engine()
        print("✓ Connected!")

        # Step 1: Create employee_periods table
        create_employee_periods_table(engine)

        # Step 2: Drop old columns
        drop_old_employees_columns(engine)

        # Step 3: Drop vacation_periods table
        drop_vacation_periods_table(engine)

        # Step 4: Verify
        verify_schema(engine)

        print("\n" + "="*70)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\n📋 NEXT STEPS:")
        print("1. Run the updated vida laboral processing script with --skip-create-employees flag")
        print("2. Reprocess your vida laboral CSV file")
        print("3. Verify that periods are created correctly")
        print("4. Check that payroll matching still works")

    except Exception as e:
        print(f"\n❌ ERROR during migration: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  Migration failed! Restore from backup.")
        sys.exit(1)


if __name__ == "__main__":
    main()
