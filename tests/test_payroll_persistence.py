#!/usr/bin/env python3
"""
Test script to verify that multiple payroll records are properly persisted
"""

import os
from datetime import date
from valeria_agent import ValeriaAgent
from setup_database import Employee, Payroll, create_database_engine

def test_payroll_persistence():
    """Test that multiple payroll records are properly saved"""

    print("🧪 Testing Payroll Record Persistence")
    print("=" * 50)

    # Initialize agent
    api_key = os.getenv('OPENAI_API_KEY', 'test-key')
    agent = ValeriaAgent(api_key)

    try:
        # Check current payroll count
        initial_count = agent.session.query(Payroll).count()
        print(f"📊 Initial payroll count: {initial_count}")

        # Check if we have any employees to work with
        employees = agent.session.query(Employee).all()
        if not employees:
            print("❌ No employees found. Please process vida laboral CSV first.")
            return False

        print(f"👥 Found {len(employees)} employees")

        # Let's manually create a few test payroll records to verify persistence
        test_payrolls = []
        for i, employee in enumerate(employees[:2]):  # Test with first 2 employees
            for month in [1, 2, 3]:  # Create 3 months of payroll for each
                payroll = Payroll(
                    employee_id=employee.id,
                    period_start=date(2025, month, 1),
                    period_end=date(2025, month, 28),
                    pay_date=date(2025, month, 28),
                    period_year=2025,
                    period_month=month,
                    period_quarter=((month - 1) // 3) + 1,
                    bruto_total=1500.00 + (i * 100) + (month * 50),  # Vary amounts
                    neto_total=1200.00 + (i * 80) + (month * 40),
                    extraction_confidence=0.9
                )
                agent.session.add(payroll)
                test_payrolls.append(payroll)
                print(f"   📋 Created payroll for {employee.full_name} - {month:02d}/2025")

        # Commit the changes
        agent.session.commit()
        print(f"✅ Committed {len(test_payrolls)} payroll records")

        # Verify they were saved
        final_count = agent.session.query(Payroll).count()
        added_count = final_count - initial_count

        print(f"📊 Final payroll count: {final_count}")
        print(f"📈 Added records: {added_count}")

        if added_count == len(test_payrolls):
            print("✅ All payroll records were successfully persisted!")

            # Show details of saved records
            print("\n📋 Saved payroll records:")
            for payroll in agent.session.query(Payroll).order_by(Payroll.id.desc()).limit(added_count):
                employee = agent.session.query(Employee).filter_by(id=payroll.employee_id).first()
                print(f"   • {employee.full_name if employee else 'Unknown'} - {payroll.period_year}-{payroll.period_month:02d} - €{payroll.bruto_total}")

            return True
        else:
            print(f"❌ Expected {len(test_payrolls)} records, but only {added_count} were saved")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_payroll_persistence()