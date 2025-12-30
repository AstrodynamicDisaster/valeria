Very good, works.

  Now I'd like to add some functionality to the report where we can also identify whether we need severance/settlement documents (finiquito) on top of the
  payslips. This would be the case every time an employee baja falls within the period or month for which the report is requested.

  Come up with a conceptual plan of what logic you'd use and what you'd implement BUT DONT MAKE ANY CHANGES YET


──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

• Here’s a concise plan to add “finiquito needed” detection alongside missing payslips, without touching code yet.

  Scope

  - Extend the existing missing-payslips logic (both cutoff and single-month modes) to also flag employees whose BAJA falls in the analyzed window.
  - Output should show, per employee, whether a finiquito is required and for which BAJA date(s).

  Data points to use

  - EmployeePeriod rows of type baja (and possibly alta→baja transitions).
  - The analysis window:
      - Cutoff mode: from each period start to cutoff_date (or today).
      - Single-month mode: the target month’s first/last day.
  - Optional: Payrolls for that final month to see if a settlement payslip already exists (if there’s a specific code or separate “finiquito” payroll record).

  Logic (cutoff mode)

  1. Determine window end: cutoff_date if provided, else today.
  2. For each employee with periods:
      - Find BAJA periods whose period_end_date is not null and period_end_date <= window end.
      - For each qualifying BAJA, mark finiquito_needed = True and capture baja_date = period_end_date.
      - If multiple BAJAs, include them all.
  3. (Optional) If you have a way to identify settlement payrolls (e.g., a specific concepto or a special Payroll.periodo marker), cross-check: if a settlement is
  already present for that month, mark finiquito_needed as “satisfied” instead of “needed”.

  Logic (single-month mode)

  1. Determine month window: first_day / last_day of the requested month.
  2. For each employee with overlapping periods in that month:
      - If any BAJA has period_end_date within [first_day, last_day], flag finiquito needed for that BAJA date.
  3. Same optional cross-check for an existing settlement payroll in that month.

  Output additions

  - In per-employee entries:
      - finiquito_needed: bool
      - baja_dates: [YYYY-MM-DD, ...] (only the ones in window)
      - (Optional) finiquito_status: "needed" | "satisfied" if we detect a settlement payslip.
  - In summary:
      - employees_needing_finiquito
      - total_finiquitos_needed (count of BAJA events in window)
      - (Optional) finiquitos_satisfied if cross-checking.

  Surface area to touch (conceptually)

  - core/missing_payslips.py:
      - detect_missing_payslips (cutoff mode) and detect_missing_payslips_for_month (single-month mode):
          - While iterating employees, collect BAJAs in window and add the finiquito fields to the result objects and summary.
  - Optional detection of “settlement already present”:
      - Requires a rule to recognize a settlement payslip. If such a marker exists (e.g., a concepto code or a dedicated Payroll.periodo), add a helper to check
  the target month for that payroll.

  Open questions to clarify before coding

  - How to recognize a settlement/finiquito payslip in your data? Is there a special concepto or a dedicated payroll record? If not, we’ll just flag need without
  checking fulfillment.
  - Should multiple BAJAs for the same employee in the window all be reported, or just the latest?

  Once these are answered, implementation will be straightforward: iterate BAJAs in window, enrich the existing report structures, and adjust summaries
  accordingly.