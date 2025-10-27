#!/usr/bin/env python3
"""
Update Social Security Numbers from .msj File

This script safely updates ONLY the ss_number field in existing Employee records
by reading NAF (Social Security Number) data from a .msj file and matching by DNI.

Features:
- Updates ONLY ss_number field (no other fields are modified)
- Matches employees by identity_card_number (DNI)
- Handles leading zero issue (tries both with and without leading zero)
- No deletions, no insertions
- Detailed reporting of results

Usage:
    python3 scripts/update_ssn_from_msj.py <path_to_file.msj> [--company-id <uuid>]

Examples:
    python3 scripts/update_ssn_from_msj.py test_data/danik.msj
    python3 scripts/update_ssn_from_msj.py test_data/danik.msj --company-id eea29097-940c-4d2c-a598-59a0be40a78b
"""

import re
import sys
import argparse
from typing import Dict, Tuple
from core.database import create_database_engine
from sqlalchemy.orm import sessionmaker
from core.models import Employee


def parse_msj_for_naf_mapping(filepath: str) -> Dict[str, str]:
    """
    Parse .msj file and extract NAF → DNI mapping.

    Args:
        filepath: Path to .msj file

    Returns:
        Dictionary mapping DNI to NAF
    """
    dni_to_naf = {}

    with open(filepath, 'r', encoding='latin1') as f:
        for line in f:
            line = line.rstrip("\n")

            # Detect employee header line:
            # Format: XX XXXXXXXXXX  X XXXXXXXXXN NAME...
            if re.match(r'^\s*\d{2}\s+\d{10}\s+\d+\s+', line):
                tokens = line.split()
                if len(tokens) >= 5:
                    # Extract NAF (Social Security Number): provincia code + NAF number
                    naf = tokens[0] + " " + tokens[1]
                    dni = tokens[3]

                    # Store mapping
                    dni_to_naf[dni] = naf

    return dni_to_naf


def update_employee_ssn(
    session,
    dni_to_naf: Dict[str, str],
    company_id: str = None,
    dry_run: bool = False
) -> Tuple[int, int, int, int]:
    """
    Update ss_number for employees based on DNI → NAF mapping.

    Args:
        session: SQLAlchemy session
        dni_to_naf: Dictionary mapping DNI to NAF
        company_id: Optional company ID to filter employees
        dry_run: If True, don't commit changes

    Returns:
        Tuple of (updated_count, already_correct_count, not_found_count, skipped_count)
    """
    updated_count = 0
    already_correct_count = 0
    not_found_count = 0
    skipped_count = 0

    for dni, naf in dni_to_naf.items():
        # Try to find employee with this DNI
        # Handle leading zero issue: try both with and without leading zero
        dni_variations = [dni]

        # If DNI starts with '0', also try without the leading zero
        if dni.startswith('0'):
            dni_variations.append(dni[1:])
        # If DNI doesn't start with '0', also try with a leading zero
        else:
            dni_variations.append('0' + dni)

        employee = None
        matched_dni = None

        for dni_variant in dni_variations:
            query = session.query(Employee).filter_by(identity_card_number=dni_variant)

            # Filter by company if specified
            if company_id:
                query = query.filter_by(company_id=company_id)

            # Get first matching employee (there might be multiple employment periods)
            employee = query.first()

            if employee:
                matched_dni = dni_variant
                break

        if not employee:
            not_found_count += 1
            print(f"⚠️  DNI {dni} not found in database (tried: {', '.join(dni_variations)})")
            continue

        # Check if ss_number is already correct
        if employee.ss_number == naf:
            already_correct_count += 1
            print(f"✓  {employee.first_name} {employee.last_name} ({matched_dni}): Already correct")
            continue

        # Check if ss_number is already set to something else
        if employee.ss_number and not employee.ss_number.startswith('SS'):
            skipped_count += 1
            print(f"⊘  {employee.first_name} {employee.last_name} ({matched_dni}): Already has SS# '{employee.ss_number}' - skipped")
            continue

        # Update ss_number
        old_ssn = employee.ss_number
        employee.ss_number = naf
        updated_count += 1

        print(f"✅ {employee.first_name} {employee.last_name} ({matched_dni}): {old_ssn or 'NULL'} → {naf}")

    if not dry_run:
        session.commit()
        print(f"\n💾 Changes committed to database")
    else:
        session.rollback()
        print(f"\n🔍 DRY RUN - No changes committed")

    return updated_count, already_correct_count, not_found_count, skipped_count


def main():
    parser = argparse.ArgumentParser(
        description='Update employee Social Security Numbers from .msj file'
    )
    parser.add_argument('msj_file', help='Path to .msj file')
    parser.add_argument('--company-id', help='Filter employees by company ID (optional)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without committing')

    args = parser.parse_args()

    # Parse .msj file
    print(f"📄 Parsing {args.msj_file}...")
    dni_to_naf = parse_msj_for_naf_mapping(args.msj_file)
    print(f"✅ Found {len(dni_to_naf)} employees with NAF in .msj file\n")

    if not dni_to_naf:
        print("❌ No employee data found in .msj file")
        sys.exit(1)

    # Connect to database
    engine = create_database_engine(echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Update employees
        print(f"🔄 Updating employee records...")
        if args.company_id:
            print(f"   Filtering by company: {args.company_id}")
        if args.dry_run:
            print(f"   ⚠️  DRY RUN MODE - No changes will be committed\n")
        print()

        updated, already_correct, not_found, skipped = update_employee_ssn(
            session,
            dni_to_naf,
            company_id=args.company_id,
            dry_run=args.dry_run
        )

        # Print summary
        print(f"\n" + "="*60)
        print(f"📊 SUMMARY")
        print(f"="*60)
        print(f"   Total in .msj file:     {len(dni_to_naf)}")
        print(f"   ✅ Updated:             {updated}")
        print(f"   ✓  Already correct:     {already_correct}")
        print(f"   ⊘  Skipped (has SS#):   {skipped}")
        print(f"   ⚠️  Not found in DB:     {not_found}")
        print(f"="*60)

        if not args.dry_run and updated > 0:
            print(f"\n✅ Successfully updated {updated} employee record(s)")
        elif args.dry_run:
            print(f"\n🔍 Dry run complete. Use without --dry-run to commit changes.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == '__main__':
    main()
