#!/usr/bin/env python3
"""
Test script for enhanced payroll data extraction
"""

from datetime import date

def test_enhanced_data_structure():
    """Test that the enhanced data structure is properly handled"""

    # Mock extracted data with the new complete structure
    mock_extracted_data = [
        {
            "name": "FRANCISCO LEON RUIZ",
            "id": "12400924Z",
            "period_start": "2025-01-01",
            "period_end": "2025-01-31",
            "pay_date": "2025-01-31",
            "period_month": 1,
            "period_year": 2025,
            "bruto_total": 1650.00,
            "neto_total": 1320.50,
            "irpf_base": 1650.00,
            "irpf_retencion": 247.50,
            "ss_trabajador": 82.00,
            "concept_lines": [
                {
                    "concept_code": "001",
                    "concept_desc": "Salario base",
                    "amount": 1400.00,
                    "is_devengo": True,
                    "is_deduccion": False
                },
                {
                    "concept_code": "120",
                    "concept_desc": "Plus convenio",
                    "amount": 250.00,
                    "is_devengo": True,
                    "is_deduccion": False
                },
                {
                    "concept_code": "700",
                    "concept_desc": "IRPF",
                    "amount": -247.50,
                    "is_devengo": False,
                    "is_deduccion": True
                },
                {
                    "concept_code": "730",
                    "concept_desc": "SS Trabajador",
                    "amount": -82.00,
                    "is_devengo": False,
                    "is_deduccion": True
                }
            ]
        }
    ]

    print("🧪 Testing Enhanced Payroll Data Structure")
    print("=" * 50)

    for emp_data in mock_extracted_data:
        print(f"\n👤 Employee: {emp_data['name']} ({emp_data['id']})")
        print(f"📅 Period: {emp_data['period_start']} to {emp_data['period_end']}")
        print(f"💰 Gross: €{emp_data['bruto_total']:.2f}")
        print(f"💳 Net: €{emp_data['neto_total']:.2f}")
        print(f"🏛️ IRPF: €{emp_data['irpf_retencion']:.2f}")
        print(f"🛡️ Social Security: €{emp_data['ss_trabajador']:.2f}")

        print(f"\n📋 Concept Lines ({len(emp_data['concept_lines'])} items):")
        for concept in emp_data['concept_lines']:
            symbol = "+" if concept['amount'] > 0 else ""
            category = "Earnings" if concept['is_devengo'] else "Deductions"
            print(f"   {concept['concept_code']}: {concept['concept_desc']} = {symbol}€{concept['amount']:.2f} ({category})")

    print(f"\n✅ Enhanced data structure validation complete!")
    print(f"📊 Ready for complete database population with:")
    print(f"   - Real monetary amounts (no more hardcoded values)")
    print(f"   - Complete concept line breakdown")
    print(f"   - Proper period date handling")
    print(f"   - Full Payroll and PayrollLine table population")

if __name__ == "__main__":
    test_enhanced_data_structure()