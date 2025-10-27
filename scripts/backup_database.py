#!/usr/bin/env python3
"""
Database Backup Utility

Creates a full PostgreSQL database dump using pg_dump.
Backups are saved to ./backups/ directory with timestamp.

Usage:
    python3 scripts/backup_database.py
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path


def backup_database():
    """Create a timestamped backup of the PostgreSQL database."""

    # Get database connection details from environment
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB', 'valeria')
    db_user = os.getenv('POSTGRES_USER', 'valeria')
    db_password = os.getenv('POSTGRES_PASSWORD', 'YourStrongPassw0rd!')

    # Create backups directory
    backups_dir = Path('./backups')
    backups_dir.mkdir(exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'valeria_backup_{timestamp}.sql'
    backup_path = backups_dir / backup_filename

    print(f"🔄 Starting database backup...")
    print(f"   Database: {db_name}@{db_host}:{db_port}")
    print(f"   Output: {backup_path}")
    print()

    # Prepare pg_dump command
    env = os.environ.copy()
    env['PGPASSWORD'] = db_password

    cmd = [
        'pg_dump',
        '-h', db_host,
        '-p', db_port,
        '-U', db_user,
        '-d', db_name,
        '--clean',  # Include DROP statements
        '--if-exists',  # Use IF EXISTS for DROP statements
        '--no-owner',  # Don't include ownership commands
        '--no-privileges',  # Don't include privilege commands
        '-f', str(backup_path)
    ]

    try:
        # Run pg_dump
        result = subprocess.run(
            cmd,
            env=env,
            check=True,
            capture_output=True,
            text=True
        )

        # Get file size
        file_size = backup_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        print(f"✅ Backup completed successfully!")
        print(f"   File: {backup_path}")
        print(f"   Size: {file_size_mb:.2f} MB")
        print()
        print(f"📋 To restore this backup, run:")
        print(f"   psql -h {db_host} -p {db_port} -U {db_user} -d {db_name} -f {backup_path}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Backup failed!")
        print(f"   Error: {e}")
        if e.stderr:
            print(f"   Details: {e.stderr}")
        return False

    except FileNotFoundError:
        print(f"❌ pg_dump command not found!")
        print(f"   Make sure PostgreSQL client tools are installed.")
        print(f"   On macOS: brew install postgresql")
        print(f"   On Ubuntu: apt-get install postgresql-client")
        return False


if __name__ == '__main__':
    success = backup_database()
    sys.exit(0 if success else 1)
