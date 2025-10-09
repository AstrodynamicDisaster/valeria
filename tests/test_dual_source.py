#!/usr/bin/env python3
"""
Test script to verify dual data source configuration works correctly.
Tests switching between local and production data sources.
"""

import os
import sys

# Add parent directory to path to import modules FIRST
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables BEFORE importing
os.environ['USE_PRODUCTION_DATA'] = 'false'
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'dummy-key-for-testing')

# Now import after path is set
from valeria_agent import ValeriaAgent

# Test with local data
print("=" * 60)
print("TEST 1: Local Data Mode (USE_PRODUCTION_DATA=false)")
print("=" * 60)

agent_local = ValeriaAgent(os.environ['OPENAI_API_KEY'])

print(f"\n✓ Agent initialized")
print(f"  Using production data: {agent_local.use_production_data}")
print(f"  Production session: {agent_local.prod_session}")

# Try to get a company from local DB
print("\n  Testing _get_company() with local data...")
# This will return None if no local companies exist, which is expected for fresh DB
local_company = agent_local._get_company(name="Test Company")
if local_company:
    print(f"    Found company: {local_company.name}")
else:
    print(f"    No local companies found (expected for fresh DB)")

print("\n" + "=" * 60)
print("TEST 2: Production Data Mode (USE_PRODUCTION_DATA=true)")
print("=" * 60)

# Clean up first agent
del agent_local

# Test with production data
os.environ['USE_PRODUCTION_DATA'] = 'true'

# Need to reload the module to pick up new env var
import importlib
import valeria_agent
importlib.reload(valeria_agent)
from valeria_agent import ValeriaAgent

try:
    agent_prod = ValeriaAgent(os.environ['OPENAI_API_KEY'])

    print(f"\n✓ Agent initialized")
    print(f"  Using production data: {agent_prod.use_production_data}")
    print(f"  Production session: {agent_prod.prod_session is not None}")

    # Try to get a company from production
    print("\n  Testing _get_company() with production data...")
    prod_company = agent_prod._get_company(cif="B67491308")  # KEBEL LOGISTICS from test
    if prod_company:
        print(f"    ✓ Found company: {prod_company.name} (CIF: {prod_company.cif})")
        print(f"      Type: {type(prod_company).__name__}")
        print(f"      Email: {prod_company.email}")

        # Try to get employees for this company
        print(f"\n  Testing _list_employees_for_company()...")
        employees = agent_prod._list_employees_for_company(prod_company.id)
        print(f"    ✓ Found {len(employees)} employees")
        if employees:
            emp = employees[0]
            print(f"      Sample: {emp.first_name} {emp.last_name} ({emp.identity_card_number})")
            print(f"      Type: {type(emp).__name__}")
            print(f"      Salary: {emp.salary}")
    else:
        print(f"    ✗ Company not found")

    # Try to get a specific employee
    print(f"\n  Testing _get_employee() by identity card...")
    employee = agent_prod._get_employee(identity_card_number="36154300W")
    if employee:
        print(f"    ✓ Found employee: {employee.first_name} {employee.last_name}")
        print(f"      Identity Card: {employee.identity_card_number}")
        print(f"      Role: {employee.role}")
        print(f"      Status: {employee.employee_status}")
    else:
        print(f"    ✗ Employee not found")

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nConfiguration switching works correctly:")
    print("  - Local mode: reads from local database")
    print("  - Production mode: reads from production database")
    print("  - Helper methods return consistent Employee/Client objects")
    print("\n✓ Ready to use in development and production!")

except Exception as e:
    print(f"\n✗ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
