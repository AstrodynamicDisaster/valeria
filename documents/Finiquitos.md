Plan: Finiquito Detection in Missing Payslips Report

Goal
Add finiquito (settlement) requirements to the missing payslips report. A finiquito is required when an employee has a BAJA whose termination date falls within the report window. Use Payroll.type to detect whether a settlement document already exists for that month.

Scope
- Applies to both cutoff mode (detect_missing_payslips) and single-month mode (detect_missing_payslips_for_month).
- Output should include per-employee finiquito needs plus summary counts.

Inputs and rules
- Employment periods: EmployeePeriod with period_type == "baja".
- BAJA date: EmployeePeriod.period_end_date (must be not null).
- Report window:
  - Cutoff mode: start from employee period begin to window_end where window_end = cutoff_date if provided else today.
  - Single-month mode: first_day..last_day of target month.
- Settlement detection: Payroll.type in {"settlement", "hybrid"} counts as a settlement document for that month. "payslip" alone does not.

Logic: cutoff mode (detect_missing_payslips)
1) Set window_end = cutoff_date if provided else today.
2) For each employee:
   - Collect all BAJA periods with period_end_date in range [employee_period_start, window_end].
   - For each qualifying BAJA:
     - Mark finiquito_needed = True.
     - Record baja_date (period_end_date).
     - Determine baja_month = YYYY-MM.
     - Check if any Payroll for that employee has Payroll.type in {"settlement","hybrid"} for that baja_month.
       - If yes: finiquito_status = "satisfied"
       - If no: finiquito_status = "needed"
3) If multiple BAJAs, report all of them (one finiquito per BAJA).

Logic: single-month mode (detect_missing_payslips_for_month)
1) Set window = [first_day, last_day] of target month.
2) For each employee with any period overlapping the month:
   - Collect BAJA periods with period_end_date in [first_day, last_day].
   - For each BAJA in that month:
     - Same settlement cross-check using Payroll.type for that month.

Output changes
Per employee:
- finiquitos: list of objects, each with:
  - baja_date (YYYY-MM-DD)
  - baja_month (YYYY-MM)
  - finiquito_status: "needed" | "satisfied"
- finiquito_needed: bool (true if any finiquito_status == "needed")

Summary:
- employees_needing_finiquito (count of employees with any needed finiquito)
- total_finiquitos_needed (count of BAJAs in window with status == "needed")
- total_finiquitos_satisfied (count with status == "satisfied")

Surface area (conceptual)
- core/missing_payslips.py:
  - detect_missing_payslips
  - detect_missing_payslips_for_month
  - add a small helper to compute settlement status for a given (employee_id, year, month)

Assumptions to confirm before coding
- Payroll.type values are exactly: "settlement", "payslip", "hybrid".
- For a BAJA in month M, any Payroll in month M with type settlement/hybrid is sufficient to mark the finiquito as satisfied.
- Reporting should include all BAJAs in the window, not just latest.

If all assumptions are correct, implementation is straightforward and low-risk.
