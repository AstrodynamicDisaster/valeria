#!/usr/bin/env python3
"""
Quick test script to verify enhanced payslip extraction
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add core to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import create_database_engine
from core.valeria_agent import ValeriaAgent
from core.models import Client, Employee, Payroll, PayrollLine
from sqlalchemy.orm import sessionmaker

def main():
    print("🧪 Testing Enhanced Payslip Extraction")
    print("=" * 60)

    # Get OpenAI API key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return 1

    try:
        # Create agent (it will create its own session)
        agent = ValeriaAgent(openai_api_key)

        # Create test client
        print("\n📋 Creating test client...")
        agent.create_client(
            name="Test Company SL",
            cif="B12345678",
            email="test@company.com"
        )
        client = agent.session.query(Client).filter_by(cif="B12345678").first()
        print(f"✓ Client created: {client.name} (ID: {client.id})")

        # Create a test employee matching the payslip
        print("\n👤 Creating test employee (matching testslip.pdf)...")
        test_employee = Employee(
            company_id=client.id,
            first_name="Mª ELENA",
            last_name="FERREIRA",
            identity_card_number="Z1584320Q",
            employee_status="Active",
            begin_date="2020-01-01"
        )
        agent.session.add(test_employee)
        agent.session.commit()
        print(f"✓ Employee created: {test_employee.first_name} {test_employee.last_name} (ID: {test_employee.identity_card_number})")

        # Process testslip.pdf
        print(f"\n📄 Processing testslip.pdf...")
        pdf_path = "./testslip.pdf"

        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return 1

        result = agent.process_payslip_batch(
            pdf_files=[pdf_path],
            batch_size=50,
            use_cache=True  # Enable caching
        )

        print(f"\n✓ Processing complete!")
        print(f"   Processed: {result.get('processed', 0)} payrolls")
        print(f"   Matched: {result.get('matched', 0)} employees")
        print(f"   Unmatched: {result.get('unmatched', 0)} employees")

        # Query and display extracted data
        print(f"\n📊 Verifying Extracted Data")
        print("=" * 60)

        payrolls = agent.session.query(Payroll).all()
        print(f"\nTotal payrolls extracted: {len(payrolls)}")

        for i, payroll in enumerate(payrolls, 1):
            employee = agent.session.query(Employee).filter_by(id=payroll.employee_id).first()

            print(f"\n--- Payroll #{i} ---")
            if employee:
                print(f"Employee: {employee.first_name} {employee.last_name}")
                print(f"DNI: {employee.identity_card_number}")

            print(f"Period: {payroll.period_year}/{payroll.period_month:02d}")
            print(f"Days worked: {payroll.days_worked}")
            print(f"SS Group: {payroll.ss_group}")

            print(f"\n💰 Core Amounts:")
            print(f"  Devengos total: €{payroll.devengos_total:.2f}" if payroll.devengos_total else "  Devengos total: N/A")
            print(f"  Deducciones total: €{payroll.deducciones_total:.2f}" if payroll.deducciones_total else "  Deducciones total: N/A")
            print(f"  Neto total: €{payroll.neto_total:.2f}" if payroll.neto_total else "  Neto total: N/A")

            print(f"\n📊 Contribution Bases:")
            print(f"  Base cotización total: €{payroll.base_cotizacion_total:.2f}" if payroll.base_cotizacion_total else "  Base cotización total: N/A")
            print(f"  Base cotización accidentes: €{payroll.base_cotizacion_accidentes:.2f}" if payroll.base_cotizacion_accidentes else "  Base cotización accidentes: N/A")
            print(f"  Prorrata pagas extras: €{payroll.prorrata_pagas_extras:.2f}" if payroll.prorrata_pagas_extras else "  Prorrata pagas extras: N/A")

            print(f"\n👷 Worker SS Contributions:")
            print(f"  Contingencias comunes: €{payroll.ss_trabajador_contingencias_comunes:.2f}" if payroll.ss_trabajador_contingencias_comunes else "  Contingencias comunes: N/A")
            print(f"  Desempleo: €{payroll.ss_trabajador_desempleo:.2f}" if payroll.ss_trabajador_desempleo else "  Desempleo: N/A")
            print(f"  Formación: €{payroll.ss_trabajador_formacion:.2f}" if payroll.ss_trabajador_formacion else "  Formación: N/A")
            print(f"  Total: €{payroll.ss_trabajador_total:.2f}" if payroll.ss_trabajador_total else "  Total: N/A")

            print(f"\n🏢 Employer SS Contributions (NEW):")
            print(f"  Contingencias comunes: €{payroll.ss_empresa_contingencias_comunes:.2f}" if payroll.ss_empresa_contingencias_comunes else "  Contingencias comunes: N/A")
            print(f"  AT/EP: €{payroll.ss_empresa_at_ep:.2f}" if payroll.ss_empresa_at_ep else "  AT/EP: N/A")
            print(f"  Desempleo: €{payroll.ss_empresa_desempleo:.2f}" if payroll.ss_empresa_desempleo else "  Desempleo: N/A")
            print(f"  Formación: €{payroll.ss_empresa_formacion:.2f}" if payroll.ss_empresa_formacion else "  Formación: N/A")
            print(f"  FOGASA: €{payroll.ss_empresa_fogasa:.2f}" if payroll.ss_empresa_fogasa else "  FOGASA: N/A")
            print(f"  Total: €{payroll.ss_empresa_total:.2f}" if payroll.ss_empresa_total else "  Total: N/A")

            print(f"\n💼 Total Employer Cost:")
            print(f"  Total coste empresa: €{payroll.total_coste_empresa:.2f}" if payroll.total_coste_empresa else "  Total coste empresa: N/A")

            # Show payroll lines
            lines = agent.session.query(PayrollLine).filter_by(payroll_id=payroll.id).all()
            print(f"\n📝 Payroll Lines ({len(lines)} concepts):")

            for line in lines:
                amount = line.importe_devengo if line.importe_devengo else -line.importe_deduccion if line.importe_deduccion else 0

                details = []
                if line.units:
                    details.append(f"{line.units} units")
                if line.unit_price:
                    details.append(f"@€{line.unit_price:.2f}")
                if line.contribution_rate:
                    details.append(f"{line.contribution_rate}%")

                details_str = f" ({', '.join(details)})" if details else ""

                print(f"  • {line.concept_desc}: €{amount:.2f}{details_str}")

        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")

        return 0

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        agent.session.close()

if __name__ == "__main__":
    exit(main())
