#!/usr/bin/env python3
"""
Example script showing how to use the missing payslip detection functionality
"""

import os
import sys

# Add parent directory to path to import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import ValeriaAgent

def example_missing_payslip_workflow():
    """Demonstrate the complete workflow for missing payslip detection"""

    print("📋 Missing Payslip Detection - Example Workflow")
    print("=" * 60)

    # Initialize the ValerIA agent
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        return

    agent = ValeriaAgent(api_key)

    print("🤖 ValerIA Agent initialized")
    print("\n📝 Example workflow steps:")
    print("1. Process vida laboral CSV (to establish employment periods)")
    print("2. Process some nomina PDFs (partial processing to create gaps)")
    print("3. Run missing payslip detection")
    print("4. Generate comprehensive reports")

    print(f"\n💡 Function calls available to the AI agent:")
    print(f"   • process_vida_laboral_csv")
    print(f"   • process_payslip_batch")
    print(f"   • generate_missing_payslips_report")

    print(f"\n🎯 Sample conversation prompts:")
    print(f'   "Process this vida laboral CSV: test_data/vida_laboral_18523126183558_2025.csv"')
    print(f'   "Process these nomina PDFs: [list_of_pdf_files]"')
    print(f'   "Check for missing payslips and generate a report"')
    print(f'   "Generate missing payslips report in CSV format"')

    print(f"\n📊 Report formats supported:")
    print(f"   • Console: Human-readable with statistics and details")
    print(f"   • CSV: Spreadsheet-compatible for further analysis")
    print(f"   • JSON: Machine-readable for integration")

    print(f"\n🔍 What the system detects:")
    print(f"   • Employment periods from vida laboral CSV")
    print(f"   • Processed nomina months from database")
    print(f"   • Missing months where nominas should exist")
    print(f"   • Employment gaps and completion rates")

    print(f"\n✅ Integration complete!")
    print(f"   The AI agent can now intelligently detect missing payslips")
    print(f"   by comparing vida laboral employment data with processed nominas.")

if __name__ == "__main__":
    example_missing_payslip_workflow()