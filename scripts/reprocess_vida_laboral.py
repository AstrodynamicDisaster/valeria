#!/usr/bin/env python3
"""
Reprocess Vida Laboral CSV Script

Standalone script to process vida laboral CSV files without launching the full agent.
Useful for:
- Reprocessing after schema migration
- Updating employee periods with --skip-create-employees flag
- Bulk processing multiple CSV files

Usage:
    # Normal mode - create new employees if not found
    python scripts/reprocess_vida_laboral.py path/to/vida_laboral.csv "Company Name"

    # Skip mode - only match existing employees, don't create new ones
    python scripts/reprocess_vida_laboral.py path/to/vida_laboral.csv "Company Name" --skip-create-employees
"""

import os
import sys
import csv
import argparse
from pathlib import Path

# Add parent directory to path to import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker

from core.database import create_database_engine
from core.models import Client
import core.vida_laboral as vida_laboral
from core.vida_laboral import VidaLaboralContext


def process_vida_laboral_csv(
    csv_path: str,
    client_identifier: str,
    create_employees: bool = True
) -> dict:
    """
    Process vida laboral CSV file and create employee periods.

    Args:
        csv_path: Path to the vida laboral CSV file
        client_identifier: Client name or CIF to assign employees to
        create_employees: If True, create new employees; if False, only match existing

    Returns:
        Dict with processing results
    """
    # Validate file exists
    if not os.path.exists(csv_path):
        return {
            "success": False,
            "error": f"File not found: {csv_path}"
        }

    # Create database connection
    engine = create_database_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Find client by name or CIF
        client = session.query(Client).filter(
            (Client.name == client_identifier) | (Client.cif == client_identifier)
        ).first()

        if not client:
            return {
                "success": False,
                "error": f"Client '{client_identifier}' not found",
                "message": "Company not found in database. Please check the name/CIF."
            }

        print(f"\n{'='*70}")
        print(f"PROCESSING VIDA LABORAL CSV")
        print(f"{'='*70}")
        print(f"File: {csv_path}")
        print(f"Client: {client.name} ({client.cif})")
        print(f"Mode: {'CREATE EMPLOYEES' if create_employees else 'MATCH EXISTING ONLY'}")
        print(f"{'='*70}\n")

        # Create context
        context = VidaLaboralContext(
            create_employees=create_employees
        )

        # Process CSV
        row_count = 0
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vida_laboral.process_row(session, client.id, row, context)
                row_count += 1

        # Commit changes
        session.commit()

        print(f"\n{'='*70}")
        print("PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"Rows processed: {row_count}")
        print(f"Employees created: {context.employees_created}")
        print(f"Employees updated: {context.employees_updated}")
        print(f"Periods created: {context.periods_created}")
        print(f"Vacation periods: {context.vacation_periods_created}")
        if not create_employees:
            print(f"Employees not found (skipped): {context.employees_not_found}")
        print(f"{'='*70}\n")

        return {
            "success": True,
            "client_id": client.id,
            "client_name": client.name,
            "rows_processed": row_count,
            "employees_created": context.employees_created,
            "employees_updated": context.employees_updated,
            "periods_created": context.periods_created,
            "vacation_periods_created": context.vacation_periods_created,
            "employees_not_found": context.employees_not_found
        }

    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        session.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Reprocess vida laboral CSV file to create employee periods',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normal mode - create employees if not found
  python scripts/reprocess_vida_laboral.py data/vida_laboral.csv "ACME Corp"

  # Skip mode - only match existing employees
  python scripts/reprocess_vida_laboral.py data/vida_laboral.csv "ACME Corp" --skip-create-employees

  # Using CIF instead of name
  python scripts/reprocess_vida_laboral.py data/vida_laboral.csv "B12345678" --skip-create-employees
        """
    )

    parser.add_argument(
        'csv_path',
        help='Path to the vida laboral CSV file'
    )

    parser.add_argument(
        'client',
        help='Client name or CIF (as it appears in the database)'
    )

    parser.add_argument(
        '--skip-create-employees',
        action='store_true',
        help='Only match existing employees, do not create new ones'
    )

    args = parser.parse_args()

    # Process the CSV
    result = process_vida_laboral_csv(
        csv_path=args.csv_path,
        client_identifier=args.client,
        create_employees=not args.skip_create_employees
    )

    # Exit with appropriate code
    if result["success"]:
        sys.exit(0)
    else:
        print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
