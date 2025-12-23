#!/usr/bin/env python3
"""
Script to generate missing payslips report for a client.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uuid
from dotenv import load_dotenv

from core.database import get_session
from core.missing_payslips import generate_missing_payslips_report

# Load environment variables
load_dotenv()


def generate_missing_payslips_report_programmatically(
    *,
    client_id: uuid.UUID | str | None = None,
    output_format: str = "console",
    save_to_file: bool = False,
    filename: str | None = None,
    last_month: str | None = None,
) -> dict:
    """
    Run the missing payslips report without the CLI.

    Args mirror the CLI flags:
        client_id: UUID or string (required).
        output_format: "console", "csv", or "json". Default "console".
        save_to_file: Save the report to ./reports (same behavior as CLI).
        filename: Optional custom filename when saving.
        last_month: Optional cutoff month in MM/YYYY (e.g., "05/2024").

    Returns dict with success status, report content, summary, and file path.
    """
    # Normalize client_id
    if client_id and isinstance(client_id, str):
        client_id = str(client_id)  # Keep as string for UUID compatibility

    if not client_id:
        raise ValueError("client_id is required")

    # Create database session
    session = get_session(echo=False)

    try:
        return generate_missing_payslips_report(
            session,
            client_id=client_id,
            output_format=output_format,
            save_to_file=save_to_file,
            filename=filename,
            last_month=last_month,
        )
    finally:
        session.close()


def main():
    """Generate missing payslips report."""

    # Parse command line arguments
    client_id = None
    output_format = "console"
    save_to_file = False
    filename = None
    last_month = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--client-id":
            i += 1
            try:
                client_id = uuid.UUID(args[i])
            except ValueError:
                print(f"Error: Invalid UUID format: {args[i]}")
                sys.exit(1)
        elif args[i] == "--format":
            i += 1
            output_format = args[i]
        elif args[i] == "--save":
            save_to_file = True
        elif args[i] == "--filename":
            i += 1
            filename = args[i]
        elif args[i] == "--last-month":
            i += 1
            last_month = args[i]
        elif args[i] == "--help":
            print_usage()
            return
        i += 1

    # Validate client_id is provided
    if not client_id:
        print("Error: --client-id is required")
        print("Run with --help for usage instructions")
        sys.exit(1)

    # Generate report
    print(f"Generating missing payslips report...")
    print(f"Client ID: {client_id}")
    if last_month:
        print(f"Cutoff month: {last_month}")
    print()

    # Create database session
    session = get_session(echo=False)

    try:
        result = generate_missing_payslips_report(
            session,
            client_id=str(client_id),
            output_format=output_format,
            save_to_file=save_to_file,
            filename=filename,
            last_month=last_month
        )
    finally:
        session.close()

    if not result["success"]:
        print(f"Error: {result.get('error', 'Unknown error')}")
        print(f"Message: {result.get('message', '')}")
        sys.exit(1)

    # Display results
    if output_format == "console":
        print(result["report_content"])
    elif output_format == "json":
        print(result["report_content"])
    elif output_format == "csv":
        print(result["report_content"])

    if save_to_file and result.get("file_path"):
        print(f"\nReport saved to: {result['file_path']}")


def print_usage():
    """Print usage instructions."""
    print("""
Usage: python generate_missing_payslips_report.py --client-id UUID [OPTIONS]

Required:
  --client-id UUID       Client ID to analyze (required)

Options:
  --format FORMAT        Output format: console, csv, or json (default: console)
  --save                 Save report to file
  --filename FILENAME    Custom filename for saved report
  --last-month MM/YYYY   Cutoff month (e.g., "05/2024")
  --help                 Show this help message

Examples:
  # Generate console report for a client
  python scripts/generate_missing_payslips_report.py --client-id 12345678-1234-1234-1234-123456789abc

  # Generate CSV report and save to file
  python scripts/generate_missing_payslips_report.py --client-id 12345678-1234-1234-1234-123456789abc --format csv --save

  # Generate report with cutoff date
  python scripts/generate_missing_payslips_report.py --client-id 12345678-1234-1234-1234-123456789abc --last-month 12/2024

  # Generate JSON report with custom filename
  python scripts/generate_missing_payslips_report.py --client-id 12345678-1234-1234-1234-123456789abc --format json --save --filename my_report.json
""")


if __name__ == "__main__":
    main()
