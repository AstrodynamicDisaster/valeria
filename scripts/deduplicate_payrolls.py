#!/usr/bin/env python3
"""
Deduplicate payroll records and add uniqueness constraint.

This script:
1. Finds duplicate payrolls (same employee + overlapping periods)
2. Keeps the most complete record (most payroll lines)
3. Deletes duplicates
4. Adds a unique constraint to prevent future duplicates
"""

import os
import sys
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import text, Index
from core.database import create_database_engine
from core.models import Payroll, PayrollLine, Base

load_dotenv()


def find_duplicates(session):
    """Find duplicate payrolls (same employee + same period)."""

    # Query to find duplicates based on employee_id and periodo dates
    query = text("""
        SELECT
            employee_id,
            periodo->>'desde' as desde,
            periodo->>'hasta' as hasta,
            COUNT(*) as count,
            ARRAY_AGG(id ORDER BY created_at DESC) as payroll_ids
        FROM payrolls
        WHERE periodo IS NOT NULL
          AND periodo->>'desde' IS NOT NULL
          AND periodo->>'hasta' IS NOT NULL
        GROUP BY employee_id, periodo->>'desde', periodo->>'hasta'
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """)

    result = session.execute(query)
    duplicates = result.fetchall()

    return duplicates


def get_payroll_line_counts(session, payroll_ids):
    """Get the number of payroll lines for each payroll."""
    counts = {}
    for payroll_id in payroll_ids:
        count = session.query(PayrollLine).filter_by(payroll_id=payroll_id).count()
        counts[payroll_id] = count
    return counts


def deduplicate_payrolls(session, dry_run=True):
    """Remove duplicate payrolls, keeping the most complete one."""

    print("🔍 Searching for duplicate payrolls...")
    duplicates = find_duplicates(session)

    if not duplicates:
        print("✅ No duplicates found!")
        return 0

    print(f"\n⚠️  Found {len(duplicates)} sets of duplicate payrolls")

    total_to_delete = 0

    for dup in duplicates:
        employee_id = dup.employee_id
        desde = dup.desde
        hasta = dup.hasta
        payroll_ids = dup.payroll_ids
        count = dup.count

        print(f"\n📋 Employee {employee_id}, Period {desde} to {hasta}: {count} duplicates")
        print(f"   Payroll IDs: {payroll_ids}")

        # Get line counts for each payroll
        line_counts = get_payroll_line_counts(session, payroll_ids)

        # Sort by line count (descending), then by created_at (most recent first)
        # The first one in payroll_ids is already sorted by created_at DESC
        # So we sort by line count, keeping the one with most lines
        payrolls_with_counts = [(pid, line_counts[pid]) for pid in payroll_ids]
        payrolls_with_counts.sort(key=lambda x: (x[1], -list(payroll_ids).index(x[0])), reverse=True)

        keep_id = payrolls_with_counts[0][0]
        delete_ids = [p[0] for p in payrolls_with_counts[1:]]

        print(f"   ✅ Keeping payroll {keep_id} ({line_counts[keep_id]} lines)")
        print(f"   🗑️  Deleting {len(delete_ids)} duplicate(s):")

        for del_id in delete_ids:
            print(f"      - Payroll {del_id} ({line_counts[del_id]} lines)")
            total_to_delete += 1

            if not dry_run:
                # Delete payroll lines first
                session.query(PayrollLine).filter_by(payroll_id=del_id).delete()
                # Delete payroll
                session.query(Payroll).filter_by(id=del_id).delete()

    if dry_run:
        print(f"\n🔍 DRY RUN: Would delete {total_to_delete} duplicate payroll(s)")
        print("   Run with --execute to actually delete them")
    else:
        session.commit()
        print(f"\n✅ Deleted {total_to_delete} duplicate payroll(s)")

    return total_to_delete


def add_unique_constraint(engine):
    """Add a unique index to prevent future duplicates."""

    print("\n🔧 Adding unique constraint to prevent future duplicates...")

    with engine.connect() as conn:
        # Drop old constraint if it exists
        drop_old_query = text("""
            DROP INDEX IF EXISTS idx_unique_employee_period
        """)
        conn.execute(drop_old_query)
        conn.commit()

        # Check if new index already exists
        check_query = text("""
            SELECT 1 FROM pg_indexes
            WHERE indexname = 'idx_unique_employee_period_amount'
        """)
        exists = conn.execute(check_query).fetchone()

        if exists:
            print("   ℹ️  Unique index already exists")
            return

        # Create unique index on employee_id + period dates + liquido_a_percibir
        # This allows same period with different amounts (corrections/updates)
        create_index_query = text("""
            CREATE UNIQUE INDEX idx_unique_employee_period_amount
            ON payroll (employee_id, (periodo->>'desde'), (periodo->>'hasta'), liquido_a_percibir)
            WHERE periodo IS NOT NULL
              AND periodo->>'desde' IS NOT NULL
              AND periodo->>'hasta' IS NOT NULL
              AND liquido_a_percibir IS NOT NULL
        """)

        conn.execute(create_index_query)
        conn.commit()

        print("   ✅ Unique index created successfully!")
        print("   📝 Prevents exact duplicates (same employee + period + amount)")
        print("   ✅ Allows corrections with different liquido_a_percibir")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Deduplicate payroll records")
    parser.add_argument("--execute", action="store_true",
                       help="Actually delete duplicates (default is dry run)")
    parser.add_argument("--skip-constraint", action="store_true",
                       help="Skip adding the unique constraint")
    args = parser.parse_args()

    print("="*60)
    print("PAYROLL DEDUPLICATION SCRIPT")
    print("="*60)

    if not args.execute:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
        print("   Use --execute to actually delete duplicates\n")

    # Create engine and session
    engine = create_database_engine()
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Step 1: Deduplicate
        deleted_count = deduplicate_payrolls(session, dry_run=not args.execute)

        # Step 2: Add constraint (only if executing and not skipped)
        if args.execute and not args.skip_constraint:
            add_unique_constraint(engine)
        elif args.skip_constraint:
            print("\n⏭️  Skipping unique constraint creation")

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Duplicates found: {deleted_count}")

        if args.execute:
            print(f"Status: ✅ Deleted")
            if not args.skip_constraint:
                print(f"Constraint: ✅ Added")
        else:
            print(f"Status: 🔍 Dry run only")
            print(f"\nTo apply changes, run:")
            print(f"  python scripts/deduplicate_payrolls.py --execute")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
