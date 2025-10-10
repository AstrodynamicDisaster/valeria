#!/usr/bin/env python3
"""
Test script for robust JSON parsing functionality
"""

import os
import sys

# Add parent directory to path to import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process_payroll import _clean_json_response, _repair_json, _robust_json_parse

def test_json_parsing():
    """Test various malformed JSON scenarios that OpenAI might return"""

    print("🧪 Testing Robust JSON Parsing")
    print("=" * 50)

    # Test cases covering common JSON parsing errors
    test_cases = [
        {
            "name": "Valid JSON",
            "input": '[{"name": "John", "amount": 1500.00}]',
            "should_work": True
        },
        {
            "name": "Single quotes",
            "input": "[{'name': 'John', 'amount': 1500.00}]",
            "should_work": True
        },
        {
            "name": "Unquoted property names",
            "input": '[{name: "John", amount: 1500.00}]',
            "should_work": True
        },
        {
            "name": "Trailing commas",
            "input": '[{"name": "John", "amount": 1500.00,}]',
            "should_work": True
        },
        {
            "name": "Markdown code blocks",
            "input": '```json\n[{"name": "John", "amount": 1500.00}]\n```',
            "should_work": True
        },
        {
            "name": "Mixed quotes and extra text",
            "input": 'Here is the data:\n[{\'name\': "John", amount: 1500.00,}]\nEnd of data.',
            "should_work": True
        },
        {
            "name": "Multiple objects with errors",
            "input": "[{'concept_desc': 'Salario base', amount: 1692.6,}, {concept_desc: \"IRPF\", 'amount': -225.00}]",
            "should_work": True
        },
        {
            "name": "Real payslip example with errors",
            "input": """```json
[
  {
    name: "FRANCISCO LEON RUIZ",
    'id': "12400924Z",
    period_start: "2025-01-01",
    concept_lines: [
      {concept_code: "001", 'concept_desc': "Salario base", amount: 1692.6,},
      {"concept_code": "700", concept_desc: 'IRPF', "amount": -373.7}
    ],
  }
]
```""",
            "should_work": True
        }
    ]

    success_count = 0
    total_count = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Input: {test_case['input'][:60]}{'...' if len(test_case['input']) > 60 else ''}")

        try:
            result = _robust_json_parse(test_case['input'])

            if result and isinstance(result, list):
                print(f"   ✅ SUCCESS: Parsed {len(result)} objects")
                if result:
                    first_obj = result[0]
                    print(f"   📄 Sample: {list(first_obj.keys())[:3]}...")
                success_count += 1
            else:
                print(f"   ❌ FAILED: Returned {type(result)} - {result}")

        except Exception as e:
            print(f"   💥 ERROR: {e}")

    print(f"\n📊 Results: {success_count}/{total_count} test cases passed")

    if success_count == total_count:
        print("🎉 All tests passed! Robust JSON parsing is working correctly.")
    else:
        print("⚠️  Some tests failed. JSON parsing may need improvement.")

    return success_count == total_count

def test_individual_functions():
    """Test individual JSON repair functions"""

    print("\n🔧 Testing Individual Repair Functions")
    print("-" * 50)

    # Test _clean_json_response
    dirty_json = "```json\n[{'test': 'value'}]\n```\nExtra text here"
    cleaned = _clean_json_response(dirty_json)
    print(f"Cleaning: '{cleaned}'")

    # Test _repair_json
    broken_json = "[{name: 'value', test: \"another\",}]"
    repaired = _repair_json(broken_json)
    print(f"Repaired: '{repaired}'")

if __name__ == "__main__":
    test_json_parsing()
    test_individual_functions()
    print("\n✅ JSON parsing tests completed!")