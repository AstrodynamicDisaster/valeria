# Modelo 190 Generator Summary (Current Implementation)

This summary describes the current end‑to‑end Modelo 190 implementation in `190.py`, including how each value is computed, how claves/subclaves are assigned, the file generator details, and the XLSX add‑on.

---

## Scope and Structure

`190.py` now contains all core logic in one file:

- Config loading (concept mapping + SS tax concepts)
- DB extraction (payroll lines for a CIF with correct period overlap)
- Aggregation (per employee + clave/subclave)
- Spec‑compliant record builders for Modelo 190 (type 1 + type 2)
- Validation rules (clave/subclave, incapacidad, signs, etc.)
- CLI entrypoint
- Optional XLSX output (table + declarant block)

This keeps everything self‑contained and executable via a single script.

---

## Concept Normalization and Clave/Subclave Assignment

All concept matching uses the same normalization rules as the AEAT text fields:

- Uppercase
- Accents removed
- Whitespace collapsed

**Classification rule:**

- If `PayrollLine.is_sickpay == True` → **force clave A**.
- Else, map the normalized concept using `concepts_to_clave_subclave`.
- If no match, default to **clave A** (subclave blank).

This ensures IT (incapacidad) stays in clave A and everything else is mapped explicitly or defaults to A.

---

## DB Extraction (Payroll Lines for CIF + Period)

Payrolls are attributed to a CIF through employee periods, same logic as ingestion:

- Join path: `Payroll → Employee → EmployeePeriod → ClientLocation → Client`
- Period overlap check:
  - Payroll period uses `payroll.periodo['desde']` / `['hasta']` (cast to Date)
  - `EmployeePeriod.period_begin_date <= payroll_end`
  - `EmployeePeriod.period_end_date is NULL OR >= payroll_start`

A subquery first selects eligible payroll IDs to **avoid duplication** from multiple overlapping employee periods, then pulls all related payroll lines in a single pass.

---

## Aggregations (5 requested metrics)

Aggregations are computed per employee **and** per `(clave, subclave)` group using `Decimal`.

### 1) Percepción íntegra NO IT
Sum of `devengo` lines where `is_sickpay == False` for the clave/subclave.

### 2) Retenciones practicadas NO IT
For each payroll:

- `taxable_base = sum(devengo.amount)` where `is_taxable_income == True`, `is_sickpay == False`, same clave/subclave
- `retencion = taxable_base * (tipo_irpf / 100)`

All payroll retenciones are summed per clave/subclave.

### 3) Gastos deducibles
Sum of **deducciones** whose normalized concept is in `ss_tax_concepts`.

Allocation (configurable):

- Default: attach all gastos to **clave A** for each employee
- Optional: proportional allocation based on devengo base per clave/subclave

### 4) Percepción íntegra IT
Sum of `devengo` lines where `is_sickpay == True` (forced clave A).

### 5) Retenciones practicadas IT
Same as (2) but using `is_sickpay == True`.

---

## Defaulted Fields (Non‑supported blocks)

All non‑supported sections are explicitly zeroed/blanked:

- In‑kind blocks, atrasos, IMV, foral split, etc.
- Ceuta/Melilla flag, ejercicio devengo
- Children/ascendientes blocks
- BOE 2025 format fields: pos 389 = 0, pos 390–394 = 00000 (always)
- Tail blanks now 395–500 (per BOE 2025)

**Datos adicionales** defaults:

- Año nacimiento from employee, or `0000`
- Situación familiar = `3`
- Discapacidad = `0`
- Contrato/relación = `1` (clave A only)
- Movilidad geográfica = `0` (clave A only)
- Gastos deducibles → filled as computed

---

## Record Generation (Spec_190)

The generator builds:

- **Type 1 (header)**: totals computed from perceptor inputs
- **Type 2 (perceptor)**: 500‑char fixed record, strict formatting

Formatting helpers enforce:

- Right‑aligned numeric, zero‑padded
- Left‑aligned alpha, space‑padded
- ISO‑8859‑1 encoding
- CRLF line endings

Validation enforces:

- Only allowed claves/subclaves
- Incapacidad only on clave A
- No negative amounts without sign
- Foral split consistency
- At least one monetary component present

---

## XLSX Output (optional)

New CLI flag:

```
--xlsx <path>
```

When provided, the script generates a `.xlsx` file containing:

1) **Declarant info block** (before the table)
2) **Table of perceptors** with key monetary fields:
   - NIF, name, province, clave/subclave
   - Percepción no IT + retención no IT
   - Gastos deducibles
   - Percepción IT + retención IT

The Excel output is for inspection/verification and does not replace the official Modelo 190 file.

---

## CLI Usage

```
python 190.py --cif B12345678 --year 2024 --mapping mapping.json --out modelo190_2024.txt
```

With XLSX:

```
python 190.py --cif B12345678 --year 2024 --mapping mapping.json --out modelo190_2024.txt --xlsx modelo190_2024.xlsx
```

---

## Mapping Config (summary)

Key fields:

- `concepts_to_clave_subclave`: list of {clave, subclave, concepts}
- `ss_tax_concepts`: list of deduction concepts considered SS taxes
- `gastos_deducibles_allocation`: `clave_a` (default) or `proportional`
- `allowed_claves` / `allowed_subclaves_by_clave`
- `include_in_kind` (default false)

All concept matching is normalized in a consistent way.

---

If you want the XLSX columns expanded or the summary updated with an execution example tailored to your real CIF/year, say the word.
