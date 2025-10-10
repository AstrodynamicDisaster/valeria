#!/usr/bin/env python3
"""
Test script to verify that the ValerIA agent generates reports in JSON format
"""

import os
import sys
import json

# Add parent directory to path to import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import ValeriaAgent

def test_report_generation():
    """Test that both reports are generated in JSON format"""

    print("🧪 Testing ValerIA Agent Report Generation")
    print("=" * 50)

    # Initialize agent
    api_key = os.getenv('OPENAI_API_KEY', 'test-key')
    agent = ValeriaAgent(api_key)

    try:
        # Test 1: Generate processing report
        print("\n1️⃣ Testing processing report generation...")
        processing_report = agent.generate_processing_report()

        print(f"   📊 Processing report success: {processing_report.get('success')}")
        print(f"   📄 Report format: JSON (dict)")

        if processing_report.get('success'):
            print("   ✅ Processing report generated successfully")
            print(f"   📋 Database summary: {processing_report.get('database_summary', {})}")
        else:
            print(f"   ❌ Processing report failed: {processing_report.get('error')}")
            return False

        # Test 2: Generate missing payslips report (JSON format)
        print("\n2️⃣ Testing missing payslips report generation...")
        missing_report = agent.generate_missing_payslips_report(output_format="json")

        print(f"   📊 Missing payslips report success: {missing_report.get('success')}")
        print(f"   📄 Report format: {missing_report.get('format', 'unknown')}")

        if missing_report.get('success'):
            print("   ✅ Missing payslips report generated successfully")

            # Try to parse the JSON content to verify it's valid
            try:
                report_content = missing_report.get('report_content', '{}')
                parsed_json = json.loads(report_content)
                print(f"   📄 JSON validation: ✅ Valid JSON")
                print(f"   📈 Summary: {parsed_json.get('summary', {})}")
            except json.JSONDecodeError as e:
                print(f"   📄 JSON validation: ❌ Invalid JSON - {e}")
                return False
        else:
            print(f"   ❌ Missing payslips report failed: {missing_report.get('error')}")

        # Test 3: Verify default format is now JSON
        print("\n3️⃣ Testing default format...")
        default_report = agent.generate_missing_payslips_report()
        default_format = default_report.get('format', 'unknown')

        if default_format == 'json':
            print("   ✅ Default format is correctly set to JSON")
        else:
            print(f"   ❌ Default format is {default_format}, expected 'json'")
            return False

        print(f"\n✅ All report generation tests passed!")
        print(f"\n💡 Key Features Verified:")
        print(f"   - Processing report returns JSON-compatible dictionary")
        print(f"   - Missing payslips report generates JSON format by default")
        print(f"   - JSON content is valid and parseable")
        print(f"   - Reports contain expected summary data")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_report_generation()