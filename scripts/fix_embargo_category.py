#!/usr/bin/env python3
"""
Fix embargo category script
Checks that all PayrollLine entries with 'embargo' in Concepto have Category='deduccion'
and updates any that are incorrectly set to 'devengo'.
"""

import sys
from pathlib import Path

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from core.database import create_database_engine
from core.models import PayrollLine


def check_and_fix_embargo_categories():
    """Check and fix embargo entries with wrong category"""

    engine = create_database_engine(echo=True)

    with Session(engine) as session:
        # Find all payroll lines with 'embargo' in concepto (case insensitive)
        embargo_lines = session.query(PayrollLine).filter(
            PayrollLine.concepto.ilike('%embargo%')
        ).all()

        print(f"\nFound {len(embargo_lines)} payroll lines containing 'embargo'")

        # Check categories
        devengo_count = 0
        deduccion_count = 0
        other_count = 0

        incorrect_lines = []

        for line in embargo_lines:
            if line.category == 'devengo':
                devengo_count += 1
                incorrect_lines.append(line)
                print(f"  ❌ ID {line.id}: '{line.concepto}' - Category: {line.category} (INCORRECT)")
            elif line.category == 'deduccion':
                deduccion_count += 1
                print(f"  ✓ ID {line.id}: '{line.concepto}' - Category: {line.category} (correct)")
            else:
                other_count += 1
                print(f"  ? ID {line.id}: '{line.concepto}' - Category: {line.category} (unexpected)")

        print(f"\nSummary:")
        print(f"  Correct (deduccion): {deduccion_count}")
        print(f"  Incorrect (devengo): {devengo_count}")
        print(f"  Other categories: {other_count}")

        # Update incorrect entries
        if incorrect_lines:
            print(f"\nUpdating {len(incorrect_lines)} incorrect entries...")

            for line in incorrect_lines:
                print(f"  Updating ID {line.id}: '{line.concepto}' from 'devengo' to 'deduccion'")
                line.category = 'deduccion'

            session.commit()
            print(f"\n✓ Successfully updated {len(incorrect_lines)} entries")
        else:
            print("\n✓ No updates needed - all embargo entries have correct category")

        return {
            'total': len(embargo_lines),
            'correct': deduccion_count,
            'incorrect': devengo_count,
            'other': other_count,
            'updated': len(incorrect_lines)
        }


if __name__ == '__main__':
    result = check_and_fix_embargo_categories()
    print(f"\nFinal stats: {result}")
