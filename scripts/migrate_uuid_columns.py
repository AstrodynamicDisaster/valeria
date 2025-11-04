#!/usr/bin/env python3
"""
Migration script to convert String UUID columns to proper UUID type.
Converts:
- clients.id: String -> UUID
- employee_periods.company_id: String -> UUID (and adds FK constraint)
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from core.database import create_database_engine
from dotenv import load_dotenv

load_dotenv()


def run_migration():
    """Execute the migration to convert String columns to UUID."""

    engine = create_database_engine(echo=False)

    print("Starting UUID column migration...")
    print("=" * 60)

    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()

        try:
            # Step 1: Drop existing foreign key constraints on client_id columns
            print("\n1. Dropping existing foreign key constraints...")

            # Drop FK on documents.client_id
            conn.execute(text("""
                ALTER TABLE documents
                DROP CONSTRAINT IF EXISTS documents_client_id_fkey
            """))
            print("   ✓ Dropped documents.client_id FK")

            # Drop FK on checklist_items.client_id
            conn.execute(text("""
                ALTER TABLE checklist_items
                DROP CONSTRAINT IF EXISTS checklist_items_client_id_fkey
            """))
            print("   ✓ Dropped checklist_items.client_id FK")

            # Step 2: Convert all client_id columns to UUID
            print("\n2. Converting all client_id columns to UUID type...")

            # Convert documents.client_id
            conn.execute(text("""
                ALTER TABLE documents
                ALTER COLUMN client_id TYPE UUID USING client_id::uuid
            """))
            print("   ✓ documents.client_id converted to UUID")

            # Convert checklist_items.client_id
            conn.execute(text("""
                ALTER TABLE checklist_items
                ALTER COLUMN client_id TYPE UUID USING client_id::uuid
            """))
            print("   ✓ checklist_items.client_id converted to UUID")

            # Convert employee_periods.company_id
            conn.execute(text("""
                ALTER TABLE employee_periods
                ALTER COLUMN company_id TYPE UUID USING company_id::uuid
            """))
            print("   ✓ employee_periods.company_id converted to UUID")

            # Step 3: Convert clients.id to UUID (primary key)
            print("\n3. Converting clients.id to UUID type...")
            conn.execute(text("""
                ALTER TABLE clients
                ALTER COLUMN id TYPE UUID USING id::uuid
            """))
            print("   ✓ clients.id converted to UUID")

            # Step 4: Re-add all foreign key constraints
            print("\n4. Adding foreign key constraints...")

            # Add FK on documents.client_id
            conn.execute(text("""
                ALTER TABLE documents
                ADD CONSTRAINT documents_client_id_fkey
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            """))
            print("   ✓ Added documents.client_id FK")

            # Add FK on checklist_items.client_id
            conn.execute(text("""
                ALTER TABLE checklist_items
                ADD CONSTRAINT checklist_items_client_id_fkey
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            """))
            print("   ✓ Added checklist_items.client_id FK")

            # Add FK on employee_periods.company_id
            conn.execute(text("""
                ALTER TABLE employee_periods
                ADD CONSTRAINT fk_employee_periods_company_id
                FOREIGN KEY (company_id) REFERENCES clients(id) ON DELETE CASCADE
            """))
            print("   ✓ Added employee_periods.company_id FK")

            # Commit transaction
            trans.commit()
            print("\n" + "=" * 60)
            print("✓ Migration completed successfully!")
            print("\nChanges made:")
            print("  - clients.id: String → UUID")
            print("  - documents.client_id: String → UUID")
            print("  - checklist_items.client_id: String → UUID")
            print("  - employee_periods.company_id: String → UUID")
            print("  - All foreign key constraints re-added")

        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"\n✗ Migration failed: {e}")
            print("All changes rolled back.")
            sys.exit(1)


def main():
    """Main entry point."""
    print("UUID Column Migration Script")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Drop existing foreign key constraints")
    print("  2. Convert all client_id columns to UUID type:")
    print("     - documents.client_id")
    print("     - checklist_items.client_id")
    print("     - employee_periods.company_id")
    print("  3. Convert clients.id to UUID type")
    print("  4. Re-add all foreign key constraints")
    print("\n" + "=" * 60)

    # Ask for confirmation
    response = input("\nProceed with migration? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Migration cancelled.")
        sys.exit(0)

    run_migration()


if __name__ == "__main__":
    main()
