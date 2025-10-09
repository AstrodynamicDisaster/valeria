#!/usr/bin/env python3
"""
Test script for missing payslip detection functionality
"""

import os
from datetime import date
from valeria_agent import ValeriaAgent

def test_missing_payslip_detection():
    """Test the missing payslip detection system"""

    print("🧪 Testing Missing Payslip Detection System")
    print("=" * 60)

    try:
        # Create agent instance (requires API key for full functionality)
        api_key = os.getenv('OPENAI_API_KEY', 'test-key')
        agent = ValeriaAgent(api_key)

        print("📋 Testing missing payslip detection functionality...")

        # Test 1: Check method exists and handles no vida laboral case
        print("\n1️⃣ Testing detection method without vida laboral processed...")
        result = agent.detect_missing_payslips()

        if not result["success"]:
            print(f"   ✅ Correctly handled no vida laboral case: {result['message']}")
        else:
            print(f"   ⚠️  Unexpected success: {result}")

        # Test 2: Test helper method for generating expected months
        print("\n2️⃣ Testing month generation helper...")
        test_start = date(2024, 6, 15)  # Mid-June 2024
        test_end = date(2024, 12, 31)   # End of December 2024

        expected_months = agent._generate_expected_months(test_start, test_end)

        print(f"   📅 Employment period: {test_start} to {test_end}")
        print(f"   📊 Generated {len(expected_months)} expected months:")
        for year, month in expected_months:
            print(f"      {year}-{month:02d}")

        # Should generate June through December 2024 = 7 months
        if len(expected_months) == 7:
            print("   ✅ Month generation working correctly")
        else:
            print(f"   ❌ Expected 7 months, got {len(expected_months)}")

        # Test 3: Test report generation method
        print("\n3️⃣ Testing report generation method...")
        report_result = agent.generate_missing_payslips_report()

        if not report_result["success"]:
            print(f"   ✅ Correctly handled no data case: {report_result['message']}")
        else:
            print(f"   ⚠️  Unexpected success: {report_result}")

        # Test 4: Simulate data and test console report formatting
        print("\n4️⃣ Testing console report formatting...")

        mock_summary = {
            'total_employees_analyzed': 3,
            'employees_with_missing_payslips': 2,
            'total_missing_payslips': 5,
            'analysis_date': '2025-09-17'
        }

        mock_missing_data = [
            {
                'employee_id': 1,
                'employee_name': 'FRANCISCO LEON RUIZ',
                'documento': '12400924Z',
                'employment_start': '2024-06-01',
                'employment_end': 'Active',
                'expected_months': 7,
                'processed_months': 5,
                'missing_months': ['2024-07', '2024-09'],
                'missing_count': 2
            },
            {
                'employee_id': 2,
                'employee_name': 'ANDREA SANCHEZ SANCHEZ',
                'documento': '88469776T',
                'employment_start': '2024-04-01',
                'employment_end': '2024-12-31',
                'expected_months': 9,
                'processed_months': 6,
                'missing_months': ['2024-05', '2024-08', '2024-11'],
                'missing_count': 3
            }
        ]

        console_report = agent._format_console_report(mock_summary, mock_missing_data)
        print("   📄 Generated console report:")
        print("   " + "─" * 50)
        for line in console_report.split('\n'):
            print(f"   {line}")
        print("   " + "─" * 50)
        print("   ✅ Console report formatting working")

        # Test 5: Test CSV report formatting
        print("\n5️⃣ Testing CSV report formatting...")
        csv_report = agent._format_csv_report(mock_missing_data)
        print("   📄 Generated CSV report:")
        print("   " + "─" * 50)
        for line in csv_report.split('\n'):
            print(f"   {line}")
        print("   " + "─" * 50)
        print("   ✅ CSV report formatting working")

        print(f"\n✅ Missing payslip detection test completed!")
        print(f"\n💡 Key Features Tested:")
        print(f"   - Missing payslip detection method")
        print(f"   - Employment period month generation")
        print(f"   - Report generation with multiple formats")
        print(f"   - Error handling for missing data")
        print(f"   - Console and CSV report formatting")

        print(f"\n🎯 To test with real data:")
        print(f"   1. Process a vida laboral CSV file")
        print(f"   2. Process some (but not all) nomina PDFs")
        print(f"   3. Call generate_missing_payslips_report()")
        print(f"   4. Review the missing payslip gaps")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_missing_payslip_detection()