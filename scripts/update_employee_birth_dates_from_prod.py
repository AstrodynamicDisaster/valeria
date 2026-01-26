#!/usr/bin/env python3
"""
Sync local employee birth dates from production by SSN.

Behavior:
- If production has a birth_date for the SSN, update local to that value.
- If production has no birth_date (or no matching employee) and local is empty,
  set local birth_date to the default (1990-01-01).
"""

from __future__ import annotations

import os
import sys
from datetime import date

# Allow running as a script from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_session
from core.models import Employee
from core.normalization import normalize_ssn
from core.production_models import ProductionEmployee, create_production_session


DEFAULT_BIRTH_DATE = date(1990, 1, 1)
DEFAULT_BATCH_SIZE = 500


def _chunk(values: list[str], size: int):
    for idx in range(0, len(values), size):
        yield values[idx:idx + size]


def sync_birth_dates(default_birth_date: date = DEFAULT_BIRTH_DATE, batch_size: int = DEFAULT_BATCH_SIZE) -> dict:
    local_session = get_session(echo=False)
    prod_session = create_production_session()

    updated_from_prod = 0
    defaulted = 0
    unchanged = 0
    skipped_no_ssn = 0
    missing_prod = 0
    missing_prod_birth_date = 0

    try:
        raw_ssns = [
            normalize_ssn(row[0])
            for row in local_session.query(Employee.ss_number)
            .filter(Employee.ss_number.isnot(None))
            .all()
        ]
        ssns = sorted({ssn for ssn in raw_ssns if ssn})
        prod_birth_dates: dict[str, date | None] = {}
        prod_found_ssns: set[str] = set()

        for idx, chunk in enumerate(_chunk(ssns, batch_size), start=1):
            print(f"Fetching production birth dates batch {idx} ({len(chunk)} SSNs)...")
            results = (
                prod_session.query(ProductionEmployee.ss_number, ProductionEmployee.birth_date)
                .filter(ProductionEmployee.ss_number.in_(chunk))
                .all()
            )
            for ssn, birth_date in results:
                normalized = normalize_ssn(ssn)
                if normalized:
                    prod_found_ssns.add(normalized)
                    prod_birth_dates[normalized] = birth_date

        employees = (
            local_session.query(Employee)
            .filter(Employee.ss_number.isnot(None))
            .yield_per(batch_size)
        )
        for employee in employees:
            ssn = normalize_ssn(employee.ss_number)
            if not ssn:
                skipped_no_ssn += 1
                continue

            prod_birth_date = prod_birth_dates.get(ssn)
            if prod_birth_date:
                if employee.birth_date != prod_birth_date:
                    employee.birth_date = prod_birth_date
                    updated_from_prod += 1
                else:
                    unchanged += 1
                continue

            # No production birth_date (or no match)
            if ssn not in prod_found_ssns:
                missing_prod += 1
            else:
                missing_prod_birth_date += 1

            if employee.birth_date is None:
                employee.birth_date = default_birth_date
                defaulted += 1
            else:
                unchanged += 1

        local_session.commit()
        return {
            "success": True,
            "updated_from_prod": updated_from_prod,
            "defaulted": defaulted,
            "unchanged": unchanged,
            "skipped_no_ssn": skipped_no_ssn,
            "missing_prod": missing_prod,
            "missing_prod_birth_date": missing_prod_birth_date,
        }
    except Exception as exc:  # pragma: no cover - operational script
        local_session.rollback()
        return {"success": False, "error": str(exc)}
    finally:
        local_session.close()
        prod_session.close()


def main() -> None:
    result = sync_birth_dates()
    if result.get("success"):
        print("Birth date sync complete.")
        print(f"Updated from prod: {result['updated_from_prod']}")
        print(f"Defaulted to {DEFAULT_BIRTH_DATE.isoformat()}: {result['defaulted']}")
        print(f"Unchanged: {result['unchanged']}")
        print(f"Skipped (no SSN): {result['skipped_no_ssn']}")
        print(f"No prod match: {result['missing_prod']}")
        print(f"Prod match missing birth_date: {result['missing_prod_birth_date']}")
        sys.exit(0)

    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    sys.exit(1)


if __name__ == "__main__":
    main()
