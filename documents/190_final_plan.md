
  ## 1) Decide the exact inputs and config (make this explicit in code)

  1. CLI/API inputs

  - company_cif (declarante)
  - ejercicio (typically 2024 for a file filed in 2025)
  - Either:
      - --year 2024 (recommended), or
      - --from YYYY-MM-DD --to YYYY-MM-DD (custom period)

  2. Concept mapping config (externalize to JSON)

  - concepts_to_clave_subclave: list of {clave, subclave, concepts[]}; anything not matched defaults to A (subclave blank).
  - ss_tax_concepts: list of concept strings treated as “SS taxes / gastos deducibles”.
  - Normalize match keys the same way every time: upper(), collapse whitespace, strip accents (same normalization you’ll use for AEAT text fields).

  3. Two clarifications you should resolve up-front (because the doc text is inconsistent)

  - In instructions_190.md, “Percepción integra IT” says is_sickpay is false (that’s almost certainly a typo). Implement IT as PayrollLine.is_sickpay -> ANSWER: it is indeed sickpay = true
    == True.
  - “Gastos deducibles” says “sum of devengo items” but the example is a deducción. Implement gastos deducibles as deducciones whose concept ∈
    ss_tax_concepts (configurable). -> ANSWER: you are right, these are deducciones

  ———

  ## 2) Build the DB extraction layer (SQLAlchemy) for “payrolls belonging to a CIF”

  Because Payroll has no client_id, you must attribute payrolls to a client via EmployeePeriod overlap (same logic used in scripts/
  ingest_payrolls_mapped.py:_has_valid_employee_period).

  1. Define the payroll period overlap filter

  - Parse payroll.periodo['desde'] / ['hasta'] (strings) as dates in SQL (cast) and filter by overlap with [range_start, range_end].
  - Join path: Payroll -> Employee -> EmployeePeriod -> ClientLocation -> Client
  - Client match: Client.cif == company_cif
  - Overlap match (same as ingestion):
    EmployeePeriod.period_begin_date <= payroll_period_end AND
    (EmployeePeriod.period_end_date IS NULL OR EmployeePeriod.period_end_date >= payroll_period_start)

  2. Fetch all rows needed for aggregation in one pass
     Select (at minimum):

  - Employee identity: Employee.identity_card_number (NIF), names, birth_date, address
  - Payroll: Payroll.id, Payroll.tipo_irpf, Payroll.periodo
  - Payroll lines: PayrollLine.category, PayrollLine.concept, PayrollLine.amount, PayrollLine.is_taxable_income, PayrollLine.is_sickpay,
    PayrollLine.is_in_kind

  3. De-duplication
     Joining through EmployeePeriod can duplicate rows if multiple periods overlap. Plan for:

  - distinct(PayrollLine.id) style selection, or
  - subquery of eligible Payroll.ids first, then join PayrollLine from that subquery. -> ANSWER: This is the way

  Deliverable: a function like fetch_payroll_lines_for_cif_period(session, cif, start, end) -> iterable[Row].

  ———

  ## 3) Implement classification helpers (clave/subclave + flags)

  1. normalize_concept_key(concept: str) -> str
  2. classify_clave_subclave(line) -> (clave, subclave)

  - If line is sickpay (is_sickpay=True): force clave A (because IL fields are only valid for clave A / B.01 per the diseño; you’re not implementing
    B.01).
  - Else: match concept against configured mapping; default (A, None).

  3. is_ss_tax(line) -> bool

  - PayrollLine.category == 'deduccion' AND normalized concept ∈ ss_tax_concepts.

  ———

  ## 4) Implement the 5 aggregates exactly as requested, but mapped to Modelo 190 fields

  You’ll compute per employee and per (clave, subclave) group. Use Decimal end-to-end.

  ### 4.1 Percepción íntegra NO IT

  - Sum of PayrollLine.amount where:
      - category == 'devengo'
      - is_sickpay == False
      - classified into that clave/subclave
  - Modelo 190 mapping: PerceptorRecordInput.dinerario_no_incapacidad.base → type-2 positions 82–94 (sign at 81 blank).

  ### 4.2 Retenciones practicadas NO IT

  - For each payroll separately:
      - taxable_base = sum(devengo.amount where is_taxable_income==True AND is_sickpay==False AND same clave/subclave)
      - retencion_payroll = taxable_base * (Payroll.tipo_irpf / 100)
  - Sum across payrolls for the period.
  - Modelo 190 mapping: PerceptorRecordInput.dinerario_no_incapacidad.retencion → positions 95–107.

  ### 4.3 Gastos deducibles

  - Sum of SS-tax deductions where is_ss_tax(line)==True.
  - Decide attribution rule (make configurable, default simple):
      - Default: attach all gastos_deducibles to the employee’s clave A record (subclave blank).
      - Optional: allow allocating SS-tax deductions proportionally to devengo base by clave/subclave.
  - Modelo 190 mapping (PDF pages 36–37, extracted):
      - Datos adicionales positions 184–196 (184–194 integer, 195–196 decimals).
      - Note: PDF explicitly allows this field exceptionally for L.05 / L.10 / L.27; you support L.05, so allow it there too if you choose to
        allocate.

  ### 4.4 Percepción íntegra IT (sick pay / IL)

  - Sum of PayrollLine.amount where:
      - category == 'devengo'
      - is_sickpay == True
  - Modelo 190 mapping: store as PerceptorRecordInput.incapacidad.dineraria.base → positions 256–268 (sign at 255 blank). Only emit on clave A
    records.

  ### 4.5 Retenciones practicadas IT

  - Same method as 4.2 but with is_sickpay==True.
  - Modelo 190 mapping: PerceptorRecordInput.incapacidad.dineraria.retencion → positions 269–281.

  Deliverable: build_perceptor_inputs(session, cif, start, end, mappings) -> list[PerceptorRecordInput] producing multiple records per person when
  they have multiple claves/subclaves (as required by spec_190.md).

  ———

  ## 5) Build “defaults” for everything else (explicitly)

  Based on documents/spec_190.md + the PDF sections you’re targeting:

  1. Always default to zero/blank:

  - In-kind blocks (108–147, 282–321) unless you explicitly decide to support is_in_kind.
  - Atrasos (ejercicio_devengo 148–151) = 0000
  - Ceuta/Melilla/La Palma (152) = 0
  - IMV (322) = 0 (you’re not doing L.29)
  - Foral split (323–387) = zeros (you’re not doing clave E)
  - Startup shares excess (388) = 0

  2. Datos adicionales (153–254) implementation for your supported cases

  - Initialize 153–254 to '0' everywhere, except 158–166 which is an alphanumeric NIF field and should default to spaces when absent.
  - Fill only what you can source:
      - 153–156 AÑO NACIMIENTO: from Employee.birth_date.year else 0000
      - 157 SITUACIÓN FAMILIAR: you don’t have it → default to 3 (per PDF: “distinta/no deseó manifestarla”)
      - 167 DISCAPACIDAD: default 0
      - 168 CONTRATO O RELACIÓN (clave A only): default 1
      - 170 MOVILIDAD GEOGRÁFICA (clave A only): default 0
      - 184–196 GASTOS DEDUCIBLES: from your computed value (or zero)
      - 254 COMUNICACIÓN PRÉSTAMO VIVIENDA HABITUAL: default 0
      - All children/ascendientes blocks (223–253): default zeros

  ———

  ## 6) Implement the file generator exactly per documents/spec_190.md

  Put the spec logic into code with these deliverables:

  1. Formatting primitives

  - normalize_text, fmt_alpha, fmt_numeric_int, fmt_amount_euros, fmt_sign, fmt_nif

  2. Record builders

  - build_type2_record(decl, perceptor)
  - build_type1_record(decl, perceptors) with totals computed from perceptor inputs (per spec section 5.2)
  - Emit:
      - 500 chars per line
      - \r\n line endings
      - encode final file as ISO-8859-1

  3. Validation
     Implement the spec’s section 8 checks plus your scope checks:

  - Only allow claves A and L (and subclaves in {01,05,24,25,26} for L) unless config explicitly expands it.
  - If a record has IL amounts, enforce clave == 'A'.

  ———

  ## 7) Wire it into 190.py as a single entrypoint

  Suggested structure inside 190.py (still one file, but separated by sections):

  - Config loading (--mapping path.json)
  - DB querying (fetch_*)
  - Aggregation (aggregate_*)
  - Spec generator functions (from spec_190.md)
  - CLI main:
      - python 190.py --cif ... --year 2024 --out modelo190_2024.txt

  ———

  ## 8) Acceptance checklist (what “done” means)

  - Generates a file with:
      - First line type 1, remaining lines type 2
      - Every line length exactly 500
      - ISO-8859-1 encoding, CRLF
  - For a known CIF/year:
      - Perceptor count in header matches emitted type-2 line count
      - Header totals equal sum of emitted perceptor monetary fields (per spec)
  - For clave A records:
      - IT totals appear only in IL fields (255–281), not mixed into 81–107
  - For clave L records:
      - Subclave always present and 2-digit

  If you want, I can also list the exact JSON shape for the mapping config file and the exact SQLAlchemy query skeleton (with cast(..., Date) and de-
  dup strategy) tailored to your DB.