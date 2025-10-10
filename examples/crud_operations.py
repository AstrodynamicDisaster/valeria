#!/usr/bin/env python3
"""
CRUD Operations Examples for ValerIA Agent

This script demonstrates how to use the programmatic CRUD API
for managing clients, employees, and payrolls.
"""

import os
import sys
from datetime import date

# Add parent directory to path to import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import ValeriaAgent


def example_client_operations(agent):
    """
    Example: Client/Company CRUD operations
    """
    print("\n" + "=" * 60)
    print("CLIENT CRUD OPERATIONS")
    print("=" * 60)

    # CREATE CLIENT
    print("\n1. Creating a new client...")
    result = agent.create_client(
        name="ACME Solutions SL",
        cif="B87654321",
        fiscal_address="Calle Gran Vía 123, Madrid",
        email="contact@acmesolutions.es",
        phone="+34912345678"
    )

    if result['success']:
        print(f"✓ {result['message']}")
        client_id = result['data'].id
    else:
        print(f"✗ {result['message']}")
        return None

    # LIST CLIENTS
    print("\n2. Listing all active clients...")
    result = agent.list_clients(active_only=True)

    if result['success']:
        print(f"✓ {result['message']}")
        for client in result['data']:
            print(f"   - {client.name} (CIF: {client.cif}, ID: {client.id})")
    else:
        print(f"✗ {result['message']}")

    # UPDATE CLIENT
    print("\n3. Updating client information...")
    result = agent.update_client(
        client_id=client_id,
        email="info@acmesolutions.es",
        phone="+34987654321"
    )

    if result['success']:
        print(f"✓ {result['message']}")
        if result.get('changes'):
            print(f"   Changes made:")
            for field, change in result['changes'].items():
                print(f"     - {field}: {change['old']} → {change['new']}")
    else:
        print(f"✗ {result['message']}")

    return client_id


def example_employee_operations(agent, client_id):
    """
    Example: Employee CRUD operations
    """
    print("\n" + "=" * 60)
    print("EMPLOYEE CRUD OPERATIONS")
    print("=" * 60)

    # CREATE EMPLOYEE
    print("\n1. Creating a new employee...")
    result = agent.create_employee(
        company_id=client_id,
        first_name="Juan",
        last_name="García",
        last_name2="Pérez",
        identity_card_number="12345678Z",
        salary=2500.00,
        role="Software Developer",
        begin_date=date(2024, 1, 1)
    )

    if result['success']:
        print(f"✓ {result['message']}")
        employee_id = result['data'].id
    else:
        print(f"✗ {result['message']}")
        return None

    # CREATE ANOTHER EMPLOYEE
    print("\n2. Creating another employee...")
    result = agent.create_employee(
        company_id=client_id,
        first_name="María",
        last_name="López",
        last_name2="Martínez",
        identity_card_number="87654321Y",
        salary=3000.00,
        role="Project Manager",
        begin_date=date(2023, 6, 15)
    )

    if result['success']:
        print(f"✓ {result['message']}")
        employee_id_2 = result['data'].id
    else:
        print(f"✗ {result['message']}")
        employee_id_2 = None

    # LIST EMPLOYEES
    print("\n3. Listing all employees for this company...")
    result = agent.list_employees(company_id=client_id, active_only=True)

    if result['success']:
        print(f"✓ {result['message']}")
        for emp in result['data']:
            full_name = f"{emp.first_name} {emp.last_name}"
            if emp.last_name2:
                full_name += f" {emp.last_name2}"
            print(f"   - {full_name} ({emp.identity_card_number}) - €{emp.salary}/month - {emp.role}")
    else:
        print(f"✗ {result['message']}")

    # SEARCH EMPLOYEES
    print("\n4. Searching for employees by name...")
    result = agent.search_employees(query="García")

    if result['success']:
        print(f"✓ {result['message']}")
        for emp in result['data']:
            full_name = f"{emp.first_name} {emp.last_name}"
            if emp.last_name2:
                full_name += f" {emp.last_name2}"
            print(f"   - {full_name} ({emp.identity_card_number})")
    else:
        print(f"✗ {result['message']}")

    # UPDATE EMPLOYEE
    print("\n5. Updating employee salary...")
    result = agent.update_employee(
        employee_id=employee_id,
        salary=2800.00,
        role="Senior Software Developer"
    )

    if result['success']:
        print(f"✓ {result['message']}")
        if result.get('changes'):
            print(f"   Changes made:")
            for field, change in result['changes'].items():
                print(f"     - {field}: {change['old']} → {change['new']}")
    else:
        print(f"✗ {result['message']}")

    return employee_id, employee_id_2


def example_payroll_operations(agent, employee_id, employee_id_2):
    """
    Example: Payroll CRUD operations
    """
    print("\n" + "=" * 60)
    print("PAYROLL CRUD OPERATIONS")
    print("=" * 60)

    # CREATE PAYROLL
    print("\n1. Creating payroll for employee...")
    result = agent.create_payroll(
        employee_id=employee_id,
        period_year=2025,
        period_month=1,
        bruto_total=2800.00,
        neto_total=2150.00,
        irpf_base_monetaria=2800.00,
        irpf_retencion_monetaria=350.00,
        ss_trabajador_total=300.00
    )

    if result['success']:
        print(f"✓ {result['message']}")
        payroll_id = result['data'].id
    else:
        print(f"✗ {result['message']}")
        payroll_id = None

    # CREATE MULTIPLE PAYROLLS
    print("\n2. Creating payrolls for multiple months...")
    for month in range(2, 5):  # Feb, March, April
        result = agent.create_payroll(
            employee_id=employee_id,
            period_year=2025,
            period_month=month,
            bruto_total=2800.00,
            neto_total=2150.00
        )

        if result['success']:
            print(f"✓ Created payroll for 2025-{month:02d}")
        else:
            print(f"✗ Failed to create payroll for 2025-{month:02d}: {result['message']}")

    # CREATE PAYROLLS FOR SECOND EMPLOYEE
    if employee_id_2:
        print("\n3. Creating payrolls for second employee...")
        for month in range(1, 4):
            result = agent.create_payroll(
                employee_id=employee_id_2,
                period_year=2025,
                period_month=month,
                bruto_total=3000.00,
                neto_total=2300.00
            )

            if result['success']:
                print(f"✓ Created payroll for employee 2, month {month}")

    # LIST ALL PAYROLLS
    print("\n4. Listing all payrolls...")
    result = agent.list_payrolls(limit=50)

    if result['success']:
        print(f"✓ {result['message']}")
        for payroll in result['data'][:10]:  # Show first 10
            print(f"   - Employee {payroll.employee_id} | {payroll.period_year}-{payroll.period_month:02d} | €{payroll.bruto_total} gross")
    else:
        print(f"✗ {result['message']}")

    # LIST PAYROLLS FOR SPECIFIC EMPLOYEE
    print("\n5. Listing payrolls for specific employee...")
    result = agent.list_payrolls(employee_id=employee_id)

    if result['success']:
        print(f"✓ {result['message']}")
        for payroll in result['data']:
            print(f"   - {payroll.period_year}-{payroll.period_month:02d} | Gross: €{payroll.bruto_total} | Net: €{payroll.neto_total}")
    else:
        print(f"✗ {result['message']}")

    # GET EMPLOYEE PAYROLLS (helper method)
    print("\n6. Using helper method to get employee payrolls...")
    result = agent.get_employee_payrolls(employee_id=employee_id, year=2025)

    if result['success']:
        print(f"✓ {result['message']}")
        for payroll in result['data']:
            print(f"   - {payroll.period_year}-{payroll.period_month:02d}")
    else:
        print(f"✗ {result['message']}")

    # UPDATE PAYROLL
    if payroll_id:
        print("\n7. Updating payroll amounts...")
        result = agent.update_payroll(
            payroll_id=payroll_id,
            bruto_total=2850.00,
            neto_total=2180.00
        )

        if result['success']:
            print(f"✓ {result['message']}")
            if result.get('changes'):
                print(f"   Changes made:")
                for field, change in result['changes'].items():
                    print(f"     - {field}: {change['old']} → {change['new']}")
        else:
            print(f"✗ {result['message']}")

    return payroll_id


def example_database_stats(agent):
    """
    Example: Get database statistics
    """
    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)

    result = agent.get_database_stats()

    if result['success']:
        print(f"\n✓ {result['message']}\n")
        stats = result['stats']

        print("📊 Summary:")
        print(f"   Clients: {stats['clients']['total']} total, {stats['clients']['active']} active")
        print(f"   Employees: {stats['employees']['total']} total, {stats['employees']['active']} active")
        print(f"   Payrolls: {stats['payrolls']['total']} total")
        print(f"   Payroll Lines: {stats['payroll_lines']['total']} total")
        print(f"   Nomina Concepts: {stats['nomina_concepts']['total']} total")
    else:
        print(f"✗ {result['message']}")


def example_delete_operations(agent, employee_id):
    """
    Example: Delete operations (soft delete by default)
    """
    print("\n" + "=" * 60)
    print("DELETE OPERATIONS")
    print("=" * 60)

    # SOFT DELETE EMPLOYEE
    print("\n1. Soft deleting employee (mark as inactive)...")
    result = agent.delete_employee(employee_id=employee_id, soft_delete=True)

    if result['success']:
        print(f"✓ {result['message']}")
        print(f"   Deleted counts: {result['deleted_counts']}")
    else:
        print(f"✗ {result['message']}")

    # VERIFY EMPLOYEE IS INACTIVE
    print("\n2. Listing active employees (should not include deleted employee)...")
    result = agent.list_employees(active_only=True)

    if result['success']:
        print(f"✓ Found {result['count']} active employees")
    else:
        print(f"✗ {result['message']}")

    # LIST ALL EMPLOYEES (INCLUDING INACTIVE)
    print("\n3. Listing all employees (including inactive)...")
    result = agent.list_employees(active_only=False)

    if result['success']:
        print(f"✓ Found {result['count']} total employees")
        for emp in result['data']:
            full_name = f"{emp.first_name} {emp.last_name}"
            if emp.last_name2:
                full_name += f" {emp.last_name2}"
            status = "Active" if emp.active else "Inactive"
            print(f"   - {full_name} ({emp.identity_card_number}) - {status}")
    else:
        print(f"✗ {result['message']}")


def main():
    """Main example runner"""
    print("\n" + "=" * 60)
    print("ValerIA CRUD Operations - Programmatic API Examples")
    print("=" * 60)

    # Get API key
    api_key = os.getenv('OPENAI_API_KEY', 'test-key')

    # Initialize agent
    print("\n🤖 Initializing ValerIA Agent...")
    agent = ValeriaAgent(api_key)
    print("✓ Agent initialized successfully")

    # Run examples
    client_id = example_client_operations(agent)

    if client_id:
        employee_id, employee_id_2 = example_employee_operations(agent, client_id)

        if employee_id:
            payroll_id = example_payroll_operations(agent, employee_id, employee_id_2)
            example_database_stats(agent)

            # Optionally run delete examples
            # Uncomment the following line to test delete operations
            # example_delete_operations(agent, employee_id)

    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)
    print("\n💡 You can now:")
    print("   - Use these methods in your own scripts")
    print("   - Call them via the conversational interface")
    print("   - Build custom workflows combining CRUD + payroll processing\n")


if __name__ == "__main__":
    main()
