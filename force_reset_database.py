#!/usr/bin/env python3
"""
Force reset database - handles active connections more aggressively
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def force_reset_database():
    """Force reset database by terminating connections and dropping tables"""

    print("🔄 Force resetting database...")

    try:
        # Get database connection details
        db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/valeria')

        # Create engine with autocommit for administrative commands
        engine = create_engine(db_url, isolation_level="AUTOCOMMIT")

        print("✓ Database connection established")

        with engine.connect() as conn:

            # First, terminate all other connections to the database
            print("🔌 Terminating active connections...")
            try:
                conn.execute(text("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = 'valeria'
                    AND pid <> pg_backend_pid();
                """))
                print("✓ Active connections terminated")
            except Exception as e:
                print(f"⚠️  Could not terminate connections: {e}")

            # Drop tables in dependency order (manually specified)
            tables_to_drop = [
                'payroll_lines',
                'documents',
                'checklist_items',
                'payrolls',
                'employees',
                'clients',
                'nomina_concepts'
            ]

            print("🗑️  Dropping tables...")
            for table in tables_to_drop:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                    print(f"  ✓ Dropped table: {table}")
                except Exception as e:
                    print(f"  ⚠️  Could not drop table {table}: {e}")

            # Drop any remaining sequences
            print("🗑️  Dropping sequences...")
            try:
                result = conn.execute(text("""
                    SELECT sequence_name FROM information_schema.sequences
                    WHERE sequence_schema = 'public';
                """))

                sequences = result.fetchall()
                for (seq_name,) in sequences:
                    try:
                        conn.execute(text(f"DROP SEQUENCE IF EXISTS {seq_name} CASCADE;"))
                        print(f"  ✓ Dropped sequence: {seq_name}")
                    except Exception as e:
                        print(f"  ⚠️  Could not drop sequence {seq_name}: {e}")
            except Exception as e:
                print(f"⚠️  Could not query sequences: {e}")

        print("✅ Force reset completed successfully!")
        print()
        print("💡 You can now run: python setup_database.py")

        return True

    except Exception as e:
        print(f"❌ Force reset failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("⚠️  WARNING: This will forcefully reset the database!")
    response = input("Type 'FORCE' to confirm: ")

    if response.strip() == 'FORCE':
        force_reset_database()
    else:
        print("❌ Reset cancelled.")