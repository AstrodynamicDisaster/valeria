"""
Agentless missing payslips report generation.

This module provides standalone functionality for detecting and reporting
missing payslips without requiring the ValeriaAgent or agent dependencies.
"""

from __future__ import annotations

import json
import os
from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from core.models import ClientLocation, Employee, EmployeePeriod, Payroll
from core.utils.periods import period_reference_date


def detect_missing_payslips(
    session: Session,
    *,
    client_id: str | UUID,
    last_month: Optional[str] = None,
    start_month: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Detect missing payslips by comparing vida laboral employment periods
    with processed nomina records in the database.

    Args:
        session: SQLAlchemy session
        client_id: Client ID to analyze
        last_month: Optional cutoff month in MM/YYYY format (e.g., "05/2024")
                   to stop calculating missing payslips after this month

    Returns:
        Dict with success status, summary, and list of missing payslips
    """
    try:
        # Parse last_month if provided
        cutoff_date = None
        if last_month:
            try:
                # Parse MM/YYYY format
                cutoff_date = datetime.strptime(last_month, "%m/%Y").date()

                # Set to last day of that month using monthrange
                last_day = monthrange(cutoff_date.year, cutoff_date.month)[1]
                cutoff_date = cutoff_date.replace(day=last_day)

                print(f"📅 Cutoff date set to: {cutoff_date.strftime('%Y-%m-%d')}")
                print(f"   Only checking for missing payslips up to {cutoff_date.strftime('%B %Y')}")
            except (ValueError, ImportError) as e:
                return {
                    "success": False,
                    "error": f"Invalid last_month format: {last_month}",
                    "message": "Use MM/YYYY format (e.g., '05/2024')"
                }

        # Parse start_month if provided
        start_date_cap = None
        if start_month:
            try:
                start_date_cap = datetime.strptime(start_month, "%m/%Y").date()
                start_date_cap = start_date_cap.replace(day=1)
                if cutoff_date and start_date_cap > cutoff_date:
                    return {
                        "success": False,
                        "error": f"start_month is after last_month: {start_month} > {last_month}",
                        "message": "Start month must be on or before the cutoff month"
                    }
            except (ValueError, ImportError):
                return {
                    "success": False,
                    "error": f"Invalid start_month format: {start_month}",
                    "message": "Use MM/YYYY format (e.g., '01/2025')"
                }

        # Get all employees for this client with employment periods
        # CRITICAL FIX: Join through ClientLocation to filter by company
        query = session.query(Employee).join(EmployeePeriod).join(ClientLocation).filter(
            ClientLocation.company_id == client_id
        ).distinct()

        # Filter by cutoff_date if provided
        if cutoff_date:
            # Only include employees who had a period starting on or before cutoff_date
            query = query.filter(
                EmployeePeriod.period_begin_date <= cutoff_date
            )

        employees = query.all()

        if not employees:
            return {
                "success": False,
                "error": "No employees found with employment periods",
                "message": "Process vida laboral CSV first to establish employment periods"
            }

        missing_payslips = []
        total_missing = 0
        employees_with_missing_payslips = 0
        total_finiquitos_needed = 0
        total_finiquitos_satisfied = 0
        employees_needing_finiquito = 0
        current_date = cutoff_date if cutoff_date else date.today()

        print(f"🔍 Analyzing missing payslips for {len(employees)} employees...")

        start_date_cap = date(2025, 1, 1)

        for employee in employees:
            # Build full name from components
            full_name = f"{employee.first_name} {employee.last_name}"
            if employee.last_name2:
                full_name += f" {employee.last_name2}"

            print(f"   📋 Checking {full_name} ({employee.identity_card_number})...")

            # Query employment periods for this employee (alta/baja only, not vacaciones)
            periods = session.query(EmployeePeriod).filter(
                EmployeePeriod.employee_id == employee.id,
                EmployeePeriod.period_type.in_(['alta', 'baja'])
            ).order_by(EmployeePeriod.period_begin_date).all()

            if not periods:
                print(f"      ⚠️  No employment periods found, skipping...")
                continue

            # Generate expected months across all employment periods
            expected_months = set()
            for period in periods:
                start_date = period.period_begin_date
                if start_date_cap and start_date and start_date < start_date_cap:
                    start_date = start_date_cap
                end_date = period.period_end_date or current_date

                # Cap end_date at cutoff_date if provided
                if cutoff_date:
                    end_date = min(end_date, cutoff_date)

                # Generate months for this period
                period_months = _generate_expected_months(start_date, end_date)
                expected_months.update(period_months)

            processed_nominas = session.query(Payroll).filter_by(
                employee_id=employee.id
            ).all()

            processed_months, settlement_months = _collect_payroll_months(processed_nominas)

            # Find missing months
            missing_months = []
            for year, month in expected_months:
                if (year, month) not in processed_months:
                    missing_months.append(f"{year}-{month:02d}")

            window_start = min(
                (p.period_begin_date for p in periods if p.period_begin_date and (not start_date_cap or p.period_begin_date >= start_date_cap)),
                default=start_date_cap,
            )
            finiquitos = _collect_finiquitos_for_window(
                periods=periods,
                window_start=window_start,
                window_end=current_date,
                settlement_months=settlement_months,
            )

            finiquito_needed = any(f["finiquito_status"] == "needed" for f in finiquitos)
            if finiquito_needed:
                employees_needing_finiquito += 1
            for finiquito in finiquitos:
                if finiquito["finiquito_status"] == "needed":
                    total_finiquitos_needed += 1
                else:
                    total_finiquitos_satisfied += 1

            if missing_months:
                employees_with_missing_payslips += 1

            if missing_months or finiquitos:
                # Get earliest and latest periods for display
                first_period = periods[0]
                last_period = periods[-1]

                employee_missing = {
                    "employee_id": employee.id,
                    "employee_name": full_name,
                    "identity_card_number": employee.identity_card_number,
                    "documento": employee.identity_card_number,  # Alias for report formatting
                    "employment_start": first_period.period_begin_date.strftime('%Y-%m-%d') if first_period else None,
                    "employment_end": last_period.period_end_date.strftime('%Y-%m-%d') if last_period and last_period.period_end_date else "Active",
                    "expected_months": len(expected_months),
                    "processed_months": len(processed_months),
                    "missing_months": missing_months,
                    "missing_count": len(missing_months),
                    "finiquitos": finiquitos,
                    "finiquito_needed": finiquito_needed,
                }
                missing_payslips.append(employee_missing)
                total_missing += len(missing_months)

        # Generate summary
        total_employees = len(employees)
        employees_with_gaps = employees_with_missing_payslips

        summary = {
            "total_employees_analyzed": total_employees,
            "employees_with_missing_payslips": employees_with_gaps,
            "total_missing_payslips": total_missing,
            "employees_needing_finiquito": employees_needing_finiquito,
            "total_finiquitos_needed": total_finiquitos_needed,
            "total_finiquitos_satisfied": total_finiquitos_satisfied,
            "analysis_date": current_date.strftime('%Y-%m-%d')
        }

        return {
            "success": True,
            "summary": summary,
            "missing_payslips": missing_payslips,
            "message": f"Found {total_missing} missing payslips across {employees_with_gaps} employees"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to detect missing payslips: {e}"
        }


def detect_missing_payslips_for_month(
    session: Session,
    client_id: str,
    month: str,
) -> Dict[str, Any]:
    """
    Detect missing payslips restricted to a single month.

    Args:
        session: SQLAlchemy session
        client_id: Client ID to analyze
        month: Target month in MM/YYYY format (e.g., "12/2025")
    """
    try:
        # Normalize and parse month input
        raw_month = (month or "").strip()
        parse_formats = ["%m/%Y", "%m-%Y", "%Y-%m", "%Y/%m"]
        target_date = None
        for fmt in parse_formats:
            try:
                target_date = datetime.strptime(raw_month, fmt).date()
                break
            except ValueError:
                continue
        if not target_date:
            return {
                "success": False,
                "error": f"Invalid month format: {month}",
                "message": "Use MM/YYYY (e.g., '05/2024'); also accepted: MM-YYYY, YYYY-MM, YYYY/MM"
            }

        first_day = target_date.replace(day=1)
        last_day = target_date.replace(day=monthrange(target_date.year, target_date.month)[1])

        # Employees with periods overlapping the target month
        employees = (
            session.query(Employee)
            .join(EmployeePeriod)
            .join(ClientLocation)
            .filter(ClientLocation.company_id == client_id)
            .filter(
                EmployeePeriod.period_type.in_(["alta", "baja"]),
                EmployeePeriod.period_begin_date <= last_day,
                (EmployeePeriod.period_end_date.is_(None) | (EmployeePeriod.period_end_date >= first_day)),
            )
            .distinct()
            .all()
        )

        if not employees:
            return {
                "success": False,
                "error": "No employees found with employment periods for the target month",
                "message": "Process vida laboral CSV first to establish employment periods"
            }

        missing_payslips = []
        total_missing = 0
        employees_with_missing_payslips = 0
        total_finiquitos_needed = 0
        total_finiquitos_satisfied = 0
        employees_needing_finiquito = 0

        print(f"🔍 Analyzing missing payslips for {len(employees)} employees in {month}...")

        for employee in employees:
            full_name = f"{employee.first_name} {employee.last_name}"
            if employee.last_name2:
                full_name += f" {employee.last_name2}"

            # employment periods overlapping the month
            periods = (
                session.query(EmployeePeriod)
                .filter(
                    EmployeePeriod.employee_id == employee.id,
                    EmployeePeriod.period_type.in_(["alta", "baja"]),
                    EmployeePeriod.period_begin_date <= last_day,
                    (EmployeePeriod.period_end_date.is_(None) | (EmployeePeriod.period_end_date >= first_day)),
                )
                .order_by(EmployeePeriod.period_begin_date)
                .all()
            )

            if not periods:
                continue  # not employed that month

            expected_month = (target_date.year, target_date.month)

            processed_months, settlement_months = _collect_payroll_months(
                session.query(Payroll).filter_by(employee_id=employee.id).all()
            )

            missing_months = []
            if expected_month not in processed_months:
                missing_months.append(f"{expected_month[0]}-{expected_month[1]:02d}")

            finiquitos = _collect_finiquitos_for_window(
                periods=periods,
                window_start=first_day,
                window_end=last_day,
                settlement_months=settlement_months,
            )

            finiquito_needed = any(f["finiquito_status"] == "needed" for f in finiquitos)
            if finiquito_needed:
                employees_needing_finiquito += 1
            for finiquito in finiquitos:
                if finiquito["finiquito_status"] == "needed":
                    total_finiquitos_needed += 1
                else:
                    total_finiquitos_satisfied += 1

            if missing_months:
                employees_with_missing_payslips += 1

            if missing_months or finiquitos:
                first_period = periods[0]
                last_period = periods[-1]

                employee_missing = {
                    "employee_id": employee.id,
                    "employee_name": full_name,
                    "identity_card_number": employee.identity_card_number,
                    "documento": employee.identity_card_number,
                    "employment_start": first_period.period_begin_date.strftime("%Y-%m-%d") if first_period else None,
                    "employment_end": last_period.period_end_date.strftime("%Y-%m-%d") if last_period and last_period.period_end_date else "Active",
                    "expected_months": 1,
                    "processed_months": len(processed_months.intersection({expected_month})),
                    "missing_months": missing_months,
                    "missing_count": len(missing_months),
                    "finiquitos": finiquitos,
                    "finiquito_needed": finiquito_needed,
                }
                missing_payslips.append(employee_missing)
                total_missing += len(missing_months)

        summary = {
            "total_employees_analyzed": len(employees),
            "employees_with_missing_payslips": employees_with_missing_payslips,
            "total_missing_payslips": total_missing,
            "employees_needing_finiquito": employees_needing_finiquito,
            "total_finiquitos_needed": total_finiquitos_needed,
            "total_finiquitos_satisfied": total_finiquitos_satisfied,
            "analysis_date": first_day.strftime("%Y-%m-%d"),
            "target_month": month,
        }

        return {
            "success": True,
            "summary": summary,
            "missing_payslips": missing_payslips,
            "message": f"Found {total_missing} missing payslips in {month} across {len(missing_payslips)} employees",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to detect missing payslips for {month}: {e}",
        }


def generate_missing_payslips_report(
    session: Session,
    *,
    client_id: Optional[str | UUID] = None,
    output_format: str = "json",
    save_to_file: bool = False,
    filename: Optional[str] = None,
    last_month: Optional[str] = None,
    start_month: Optional[str] = None,
    reports_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Generate a comprehensive report of missing payslips with multiple output formats.

    Args:
        session: SQLAlchemy session
        client_id: Client ID to analyze
        output_format: "console", "csv", or "json"
        save_to_file: Whether to save the report to a file
        filename: Custom filename (auto-generated if not provided)
        last_month: Optional cutoff month in MM/YYYY format (e.g., "05/2024")
        reports_dir: Directory to save reports (default: "./reports")

    Returns:
        Dict with success status, report content, summary, and file path
    """
    try:
        if not client_id:
            return {
                "success": False,
                "error": "client_id is required",
                "message": "Please specify a client_id to analyze"
            }

        # Get missing payslip data
        result = detect_missing_payslips(
            session,
            client_id=client_id,
            last_month=last_month,
            start_month=start_month,
        )

        if not result["success"]:
            return result

        summary = result["summary"]
        missing_data = result["missing_payslips"]

        report_content = ""

        if output_format == "console":
            report_content = _format_console_report(summary, missing_data)
        elif output_format == "csv":
            report_content = _format_csv_report(missing_data)
        elif output_format == "json":
            report_content = json.dumps({
                "summary": summary,
                "missing_payslips": missing_data
            }, indent=2, default=str)
        else:
            return {
                "success": False,
                "error": f"Unsupported output format: {output_format}",
                "message": "Supported formats: console, csv, json"
            }

        # Save to file if requested
        file_path = None
        if save_to_file:
            # Create reports directory
            os.makedirs(reports_dir, exist_ok=True)

            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                extension = "json" if output_format == "json" else "csv" if output_format == "csv" else "txt"
                filename = f"missing_payslips_report_{timestamp}.{extension}"

            file_path = os.path.join(reports_dir, filename)

            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to write file: {e}",
                    "message": f"Report generated but file writing failed: {e}"
                }

        return {
            "success": True,
            "format": output_format,
            "report_content": report_content,
            "summary": summary,
            "file_path": file_path,
            "message": f"Generated {output_format} report with {summary['total_missing_payslips']} missing payslips" + (f" - Saved to {file_path}" if file_path else "")
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate report: {e}"
        }


def _generate_expected_months(start_date: date, end_date: date) -> List[Tuple[int, int]]:
    """Generate list of (year, month) tuples for expected payslip months"""
    if not start_date:
        return []

    expected_months = []
    current = start_date.replace(day=1)  # Start from first day of month
    end = end_date.replace(day=1) if end_date else date.today().replace(day=1)

    while current <= end:
        expected_months.append((current.year, current.month))
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    return expected_months


def _format_console_report(summary: Dict, missing_data: List[Dict]) -> str:
    """Format missing payslips report for console output"""
    lines = []
    lines.append("📊 MISSING PAYSLIPS & FINIQUITOS REPORT")
    lines.append("=" * 50)
    lines.append("")

    # Summary section
    lines.append(f"📈 SUMMARY ({summary['analysis_date']})")
    lines.append("-" * 30)
    lines.append(f"  Total employees analyzed: {summary['total_employees_analyzed']}")
    lines.append(f"  Employees with missing payslips: {summary['employees_with_missing_payslips']}")
    lines.append(f"  Total missing payslips: {summary['total_missing_payslips']}")
    lines.append(f"  Employees needing finiquito: {summary.get('employees_needing_finiquito', 0)}")
    lines.append(f"  Total finiquitos needed: {summary.get('total_finiquitos_needed', 0)}")
    lines.append(f"  Total finiquitos satisfied: {summary.get('total_finiquitos_satisfied', 0)}")

    if summary['total_employees_analyzed'] > 0:
        completion_rate = ((summary['total_employees_analyzed'] - summary['employees_with_missing_payslips'])
                         / summary['total_employees_analyzed'] * 100)
        lines.append(f"  Payslip completion rate: {completion_rate:.1f}%")
    lines.append("")

    # Detailed section
    if missing_data:
        lines.append("🔍 DETAILED MISSING PAYSLIPS & FINIQUITOS")
        lines.append("-" * 40)

        for emp in missing_data:
            lines.append(f"\n👤 {emp['employee_name']} ({emp['documento']})")
            lines.append(f"   Employment: {emp['employment_start']} to {emp['employment_end']}")
            lines.append(f"   Expected: {emp['expected_months']} | Processed: {emp['processed_months']} | Missing: {emp['missing_count']}")

            # Group missing months by year for readability
            missing_by_year = {}
            for month_str in emp['missing_months']:
                year = month_str.split('-')[0]
                month = month_str.split('-')[1]
                if year not in missing_by_year:
                    missing_by_year[year] = []
                missing_by_year[year].append(month)

            for year, months in sorted(missing_by_year.items()):
                months_str = ", ".join(sorted(months))
                lines.append(f"   📅 {year}: {months_str}")

            if emp.get("finiquitos"):
                lines.append("   📄 Finiquitos:")
                for finiquito in emp["finiquitos"]:
                    status = finiquito.get("finiquito_status", "needed")
                    lines.append(f"      - {finiquito.get('baja_date')} ({status})")
    else:
        lines.append("✅ No missing payslips found! All employees have complete records.")

    return "\n".join(lines)


def _format_csv_report(missing_data: List[Dict]) -> str:
    """Format missing payslips data as CSV"""
    lines = []
    lines.append("employee_name,documento,employment_start,employment_end,expected_months,processed_months,missing_count,missing_months,finiquito_needed,finiquitos_needed_count,finiquitos_satisfied_count,finiquito_baja_dates")

    for emp in missing_data:
        missing_months_str = "|".join(emp['missing_months'])
        finiquitos = emp.get("finiquitos", [])
        finiquitos_needed = [f for f in finiquitos if f.get("finiquito_status") == "needed"]
        finiquitos_satisfied = [f for f in finiquitos if f.get("finiquito_status") == "satisfied"]
        finiquito_dates = "|".join(f.get("baja_date", "") for f in finiquitos)
        line = (
            f"\"{emp['employee_name']}\",{emp['documento']},{emp['employment_start']},{emp['employment_end']},"
            f"{emp['expected_months']},{emp['processed_months']},{emp['missing_count']},\"{missing_months_str}\","
            f"{str(emp.get('finiquito_needed', False)).lower()},{len(finiquitos_needed)},{len(finiquitos_satisfied)},\"{finiquito_dates}\""
        )
        lines.append(line)

    return "\n".join(lines)


def _collect_payroll_months(payrolls: List[Payroll]) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
    processed_months: Set[Tuple[int, int]] = set()
    settlement_months: Set[Tuple[int, int]] = set()

    for payroll in payrolls:
        ref_date = period_reference_date(getattr(payroll, "periodo", None))
        if not ref_date:
            continue
        month_key = (ref_date.year, ref_date.month)
        processed_months.add(month_key)
        if payroll.type in {"settlement", "hybrid"}:
            settlement_months.add(month_key)

    return processed_months, settlement_months


def _collect_finiquitos_for_window(
    *,
    periods: List[EmployeePeriod],
    window_start: Optional[date],
    window_end: date,
    settlement_months: Set[Tuple[int, int]],
) -> List[Dict[str, Any]]:
    finiquitos = []

    for period in periods:
        if period.period_type != "baja" or not period.period_end_date:
            continue

        baja_date = period.period_end_date
        if window_start and baja_date < window_start:
            continue
        if baja_date > window_end:
            continue

        month_key = (baja_date.year, baja_date.month)
        status = "satisfied" if month_key in settlement_months else "needed"
        finiquitos.append(
            {
                "baja_date": baja_date.strftime("%Y-%m-%d"),
                "baja_month": f"{baja_date.year}-{baja_date.month:02d}",
                "finiquito_status": status,
            }
        )

    return finiquitos
