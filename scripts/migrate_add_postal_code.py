#!/usr/bin/env python3
"""
Add postal_code columns to clients and client_locations.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from core.database import create_database_engine


def main() -> int:
    engine = create_database_engine()
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE clients ADD COLUMN IF NOT EXISTS postal_code TEXT;"))
        conn.execute(text("ALTER TABLE client_locations ADD COLUMN IF NOT EXISTS postal_code TEXT;"))
    print("Added postal_code columns (if missing).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
