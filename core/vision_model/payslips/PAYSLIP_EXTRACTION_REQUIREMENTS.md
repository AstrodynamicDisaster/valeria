# Payslip Extraction Requirements

This document outlines what data needs to be extracted from Spanish payslips (nóminas) and how it's stored in the database.

## Overview

The extraction process converts payslip PDFs into structured JSON that is then stored in two main database tables:
- **`payrolls`**: Stores period information, totals, and warnings
- **`payroll_lines`**: Stores individual line items (devengos, deducciones, aportaciones empresa)

## Data Flow

1. **Extraction**: PDF → JSON (via vision model + heuristics)
2. **Matching**: Use `empresa` and `trabajador` to match Client and Employee records
3. **Storage**: Store `periodo`, `totales`, and line items in database

---

## Required Fields by Category

### 1. Empresa (Company) - Used for Matching Only
**Purpose**: Match payslip to correct Client record in database  
**NOT stored directly** - only used for validation/matching

- **`razon_social`** (string|null): Company legal name
  - Used to match `clients.name` in database
  - Example: "ACME CORPORATION S.L."
  
- **`cif`** (string|null): Company tax ID (CIF)
  - Used to match `clients.cif` in database (most reliable)
  - Format: Letter + 8 digits + optional letter (e.g., "B12345678")

### 2. Trabajador (Employee) - Used for Matching Only
**Purpose**: Match payslip to correct Employee record  
**NOT stored directly** - only used for validation/matching

- **`nombre`** (string|null): Employee full name
  - **Format**: UPPERCASE, no commas (e.g., "AHMED TUFAYEL" not "AHMED, TUFAYEL")
  - Used to match employee records
  
- **`dni`** (string|null): Employee ID (DNI/NIE)
  - Format: 8 digits + letter OR X/Y/Z + 7 digits + letter
  - Example: "12345678A" or "X1234567L"
  - Used to match employee records
  
- **`ss_number`** (string|null): Social Security affiliation number
  - **Format**: 12 digits, no spaces (e.g., "071074115236")
  - Source: Found under "Nº AFILIACION S.S." section
  - Used to match employee records

### 3. Periodo (Period) - Stored in `payrolls.periodo` (JSON)
**Purpose**: Identify the payroll period

- **`desde`** (string|null): Start date
  - Format: "YYYY-MM-DD" or "DD-MM-YYYY" (as found in document)
  - Example: "2024-01-01" or "01-01-2024"
  
- **`hasta`** (string|null): End date
  - Format: "YYYY-MM-DD" or "DD-MM-YYYY" (as found in document)
  - Example: "2024-01-31" or "31-01-2024"
  
- **`dias`** (number): Number of days in period
  - Range: Typically 28-31 days
  - **Special rule**: If document shows 31 but OCR extracts 30, leave as 30 (don't correct)

### 4. Devengo Items (Earnings) - Stored in `payroll_lines`
**Purpose**: All earnings/income items  
**Category**: `"devengo"`  
**Table**: `payroll_lines` with `category = 'devengo'`

Each item requires:
- **`concepto`** (string): Concept name
  - Normalize multiple spaces to single space
  - Example: "SALARIO BASE", "PAGA EXTRA", "TBJO. DOMINGOS"
  
- **`importe`** (number): Amount in euros
  - Must be numeric (not string)
  - Format: Decimal with 2 decimal places
  - Example: 1500.00, 250.50

**Special Rules**:
- If concept contains "EMBARGO", it must be moved to `deduccion_items` (not devengo)
- All amounts should be positive numbers

### 5. Deduccion Items (Deductions) - Stored in `payroll_lines`
**Purpose**: All deductions from salary  
**Category**: `"deduccion"`  
**Table**: `payroll_lines` with `category = 'deduccion'`

Each item requires:
- **`concepto`** (string): Concept name
  - Examples: "RETENCION IRPF", "DTO. SEGURIDAD SOCIAL", "EMBARGO"
  
- **`importe`** (number): Amount deducted
  - Must be numeric (not string)
  - Format: Decimal with 2 decimal places
  - Example: 150.00, 25.50

**Special Rules**:
- "RETENCION IRPF" or "RETENCION I.R.P.F" = income tax withholding
- "DTO. SEGURIDAD SOCIAL" = social security deduction
- "EMBARGO" concepts should be here (not in devengos)

### 6. Aportacion Empresa Items (Employer Contributions) - Stored in `payroll_lines`
**Purpose**: Employer social security contributions  
**Category**: `"aportacion_empresa"`  
**Table**: `payroll_lines` with `category = 'aportacion_empresa'`

Each item requires:
- **`concepto`** (string): Contribution concept name
  - Standard concepts:
    - "CONTINGENCIAS COMUNES" (typically 23.6-24.27%)
    - "AT Y EP" (Accidents & Professional Diseases, typically 1.5-7.15%)
    - "DESEMPLEO" (Unemployment, typically 5.50% or 6.70%)
    - "FORMACIÓN PROFESIONAL" (Training, typically 0.60%)
    - "FONDO GARANTÍA SALARIAL" / "FOGASA" (typically 0.20%)
  
- **`base`** (number): Base amount for calculation
  - Typically the "Base Total de Cotización" (BTC)
  - Must be >= 300 (minimum base)
  - Format: Decimal with 2 decimal places
  
- **`tipo`** (number): Percentage rate
  - **Format**: Always 2 decimal places (e.g., 3.70, 5.50, 24.27)
  - Must match expected ranges for each concept
  
- **`importe`** (number): Calculated amount
  - Formula: `importe = round(base * tipo / 100, 2)`
  - If printed importe exists and matches calculated (within ±0.02), use printed value
  - Format: Decimal with 2 decimal places

**Special Rules**:
- If "HORAS EXTRA" (overtime) is present, base should include overtime amount (future enhancement)
- All three fields (base, tipo, importe) are required for aportacion items

### 7. Totales (Totals) - Stored in `payrolls` table
**Purpose**: Summary totals for the payslip  
**Stored as separate columns** in `payrolls` table

- **`devengo_total`** (number): Sum of all devengo items
  - Stored in: `payrolls.devengo_total`
  - Should match sum of `devengo_items[].importe`
  
- **`deduccion_total`** (number): Sum of all deduccion items
  - Stored in: `payrolls.deduccion_total`
  - Should match sum of `deduccion_items[].importe`
  
- **`aportacion_empresa_total`** (number): Sum of all aportacion empresa items
  - Stored in: `payrolls.aportacion_empresa_total`
  - Should match sum of `aportacion_empresa_items[].importe`
  - **If not found in document**: Calculate by summing all aportacion items
  
- **`liquido_a_percibir`** (number): Net amount to receive
  - Stored in: `payrolls.liquido_a_percibir`
  - Formula: `devengo_total - deduccion_total`
  - This is the final amount the employee receives

### 8. Warnings - Stored in `payrolls.warnings` (Text)
**Purpose**: Track any corrections or issues during extraction  
**Stored as**: JSON string or newline-separated text in `payrolls.warnings`

Add warnings when:
- Format corrections are made (name, SS number, etc.)
- Totals are calculated (not found in document)
- Concepts are moved between categories (e.g., EMBARGO)
- Any other modifications or assumptions

**Standardized warning messages** (in Spanish):
- `"Se ha estandarizado el formato del nombre del trabajador."`
- `"Se ha estandarizado el formato del Número de Afiliación a la S.S."`
- `"El valor 'aportacion_empresa_total' no se encontró y ha sido calculado sumando sus componentes."`
- `"El concepto '[NOMBRE_CONCEPTO]' ha sido movido de devengos a deducciones por ser un embargo."`

---

## Database Schema Mapping

### Payrolls Table
```sql
payrolls:
  - type (Enum): 'payslip' | 'settlement' | 'hybrid' (hybrid = payslip with settlement items)
  - periodo (JSON): {desde, hasta, dias}
  - devengo_total (Numeric 10,2)
  - deduccion_total (Numeric 10,2)
  - aportacion_empresa_total (Numeric 10,2)
  - liquido_a_percibir (Numeric 10,2)
  - warnings (Text)
```

### PayrollLines Table
```sql
payroll_lines:
  - category (String): 'devengo' | 'deduccion' | 'aportacion_empresa'
  - concepto (Text)
  - importe (Numeric 10,2) - REQUIRED for all
  - base (Numeric 10,2) - REQUIRED for aportacion_empresa only
  - tipo (Numeric 6,2) - REQUIRED for aportacion_empresa only
```

---

## Common Extraction Issues

1. **Name Format**: Names often have commas or inconsistent casing
   - Fix: Uppercase, remove commas
   
2. **SS Number**: Often has spaces (e.g., "07 1074115236")
   - Fix: Remove all spaces → "071074115236"
   
3. **Tipo (Percentage)**: Inconsistent decimal places (3.7 vs 3.70)
   - Fix: Always format to 2 decimal places
   
4. **EMBARGO in wrong category**: Sometimes appears in devengos
   - Fix: Move to deducciones
   
5. **Missing totals**: Some payslips don't show explicit totals
   - Fix: Calculate from line items
   
6. **Date formats**: Various formats (DD-MM-YYYY, YYYY-MM-DD, etc.)
   - Fix: Keep as found in document (don't normalize)

---

## Validation Rules

1. All numeric amounts must be positive (except possibly some edge cases)
2. `importe` for aportacion items should match `base * tipo / 100` (within ±0.02)
3. Totals should match sum of line items (within rounding tolerance)
4. `dias` should be between 28-31 (typically)
5. `tipo` values should be within expected ranges for each concept
6. `base` for aportacion items should be >= 300
