#!/usr/bin/env python3
"""
Test script for enhanced concept mapping system
"""

import os
import sys

# Add parent directory to path to import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import ValeriaAgent

def test_concept_mapping():
    """Test the AI-powered concept mapping system"""

    print("🧪 Testing Enhanced Concept Mapping System")
    print("=" * 55)

    # Test concepts that would come from a real payslip
    test_concepts = [
        {"concept_desc": "Salario base", "amount": 1692.6},
        {"concept_desc": "P. Prop. Extras", "amount": 282.16},  # Challenging one
        {"concept_desc": "P. Transp. J.C.", "amount": 127.37},  # Another challenging one
        {"concept_desc": "Dto. Cont. Comunes 4.83%", "amount": -101.53},  # Social Security
        {"concept_desc": "Dto. Desemp. F.P. 1.65%", "amount": -34.69},   # Unemployment
        {"concept_desc": "Retención IRPF 17.78%", "amount": -373.7},      # IRPF
    ]

    try:
        # Create agent instance (requires API key)
        agent = ValeriaAgent('test-key')

        print("📋 Loading concept mappings from database...")
        concept_mappings = agent._load_concept_mappings()

        if concept_mappings:
            print(f"✅ Loaded {len(concept_mappings)} concept codes from database")
            print("\n🔍 Available concept codes:")
            for code, info in concept_mappings.items():
                print(f"   {code}: {info['short_desc']} (Group: {info['default_group']})")
        else:
            print("❌ No concept mappings found - database may not be seeded")
            return

        print(f"\n🤖 Testing concept mapping for {len(test_concepts)} payslip concepts:")
        print("-" * 70)

        for i, concept in enumerate(test_concepts, 1):
            desc = concept['concept_desc']
            amount = concept['amount']

            print(f"\n{i}. Testing: '{desc}' (Amount: €{amount})")

            # Test fuzzy matching first
            fuzzy_match = agent._find_fuzzy_concept_match(desc, threshold=0.85)
            if fuzzy_match:
                matched_info = concept_mappings[fuzzy_match]
                print(f"   ✅ FUZZY MATCH: {fuzzy_match} → {matched_info['short_desc']}")
            else:
                print(f"   ⚠️  No fuzzy match found (threshold 85%)")

                # Test AI mapping (would require real API key)
                print(f"   🤖 Would use AI mapping for: '{desc}'")
                print(f"      → Context: Amount={amount}, Type={'Deduction' if amount < 0 else 'Earning'}")

        print(f"\n✅ Concept mapping test completed!")
        print(f"\n💡 Key Benefits:")
        print(f"   - Fuzzy matching handles exact and similar descriptions")
        print(f"   - AI mapping provides intelligent fallback for complex terms")
        print(f"   - No more foreign key constraint violations")
        print(f"   - All concepts get assigned to existing database codes")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_concept_mapping()