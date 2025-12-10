#!/usr/bin/env python3
"""
Simple script to process payroll PDFs without interactive mode

Usage:
    python examples/process_pdfs.py /path/to/pdfs
    python examples/process_pdfs.py /path/to/file.zip
    python examples/process_pdfs.py /path/to/file1.pdf /path/to/file2.pdf
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import ValeriaAgent


def process_pdfs(pdf_paths):
    """
    Process payroll PDFs programmatically

    Args:
        pdf_paths: List of paths (can be PDF files, directories, or ZIP files)
    """
    # Load environment variables
    load_dotenv()

    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("   Please set it in your .env file or export it:")
        print("   export OPENAI_API_KEY='your-key-here'")
        return 1

    # Initialize agent
    print("🤖 Initializing ValerIA Agent...")
    agent = ValeriaAgent(api_key)
    print("✓ Agent initialized\n")

    # Check if employees exist
    from core.models import Employee
    employee_count = agent.session.query(Employee).count()
    if employee_count == 0:
        print("⚠️  Warning: No employees found in database")
        print("   You may need to import vida laboral CSV first")
        print("   Or create employees manually")
        print()

        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("❌ Aborted")
            return 1
    else:
        print(f"✓ Found {employee_count} employees in database\n")

    # Process the PDFs
    print(f"📄 Processing {len(pdf_paths)} path(s)...")
    print(f"   Paths: {', '.join(pdf_paths)}\n")

    result = agent.process_payslip_batch(pdf_files=pdf_paths)

    # Display results
    print("\n" + "="*60)
    print("PROCESSING RESULTS")
    print("="*60)

    if result['success']:
        print(f"\n✅ {result['message']}")
        print(f"\n📊 Summary:")
        print(f"   Processed: {result['processed_count']} payslips")
        print(f"   Failed: {result['failed_count']} payslips")
        print(f"   Total time: {result['total_time']:.1f}s")
        print(f"   Average: {result['avg_time_per_file']:.1f}s per file")

        # Show detailed results if there were failures
        if result['failed_count'] > 0:
            print(f"\n⚠️  Failed items:")
            for item in result['results']:
                if item.get('status') != 'processed':
                    status = item.get('status', 'unknown')
                    file = item.get('file', 'unknown')
                    print(f"   - {file}: {status}")
                    if 'error' in item:
                        print(f"     Error: {item['error']}")

        return 0
    else:
        print(f"\n❌ Processing failed: {result.get('message', 'Unknown error')}")
        return 1


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python examples/process_pdfs.py <pdf_path> [pdf_path2] [pdf_path3] ...")
        print()
        print("Examples:")
        print("  python examples/process_pdfs.py /path/to/pdfs/")
        print("  python examples/process_pdfs.py /path/to/file.zip")
        print("  python examples/process_pdfs.py file1.pdf file2.pdf file3.pdf")
        print()
        print("Supported inputs:")
        print("  - Individual PDF files")
        print("  - Directories (will scan recursively for PDFs)")
        print("  - ZIP archives (will extract PDFs)")
        return 1

    pdf_paths = sys.argv[1:]

    # Validate paths exist
    for path in pdf_paths:
        if not os.path.exists(path):
            print(f"❌ Error: Path does not exist: {path}")
            return 1

    return process_pdfs(pdf_paths)


if __name__ == "__main__":
    sys.exit(main())
