# Database Schema Refactoring: Client → Client + ClientLocation

## Date
2025-12-21

## Overview
Refactored the database schema to properly separate companies from their locations, and fixed critical bug where NAF (employee social security) was confused with CCC (company location code).

## Initial Problem
The database had Client records with:
- Non-unique CIF (company tax ID)
- Unique NAF/SSN/CCC field
- This created multiple Client records for the same company (one per location)

## Solution Part 1: Schema Refactoring

### New Structure
- **Client table**: One record per company (unique CIF)
  - Removed `ccc_ss` field
  - Made `cif` unique
- **ClientLocation table**: Multiple records per company (unique CCC)
  - `company_id` → references Client
  - `ccc_ss` → unique CCC identifier
- **EmployeePeriod table**: Links to locations instead of clients
  - Changed `company_id` → `location_id`
  - Now references ClientLocation instead of Client

### Files Modified (Part 1)
1. **core/models.py**
   - Created ClientLocation model
   - Modified Client.cif to unique=True
   - Removed Client.ccc_ss
   - Changed EmployeePeriod.company_id → location_id
   - Fixed utility function get_employee_company()

2. **core/database.py**
   - Updated 3 query functions to use ClientLocation:
     - list_employee_ssns_for_company_period()
     - get_payroll_line_aggregates()
     - get_employee_devengo_total()

3. **core/agent/vida_laboral.py**
   - Updated handle_alta(), handle_baja(), handle_vacacion()
   - Each now gets/creates ClientLocation before creating EmployeePeriod

4. **core/production_models.py**
   - Rewrote insert_company_locations_into_local_clients()
   - Creates ONE Client + multiple ClientLocations

5. **scripts/setup_database.py**
   - Updated indexes: company_id → location_id
   - Added ClientLocation indexes
   - Updated database views to join through client_locations

6. **scripts/reset_database.py**
   - Added client_locations to tables_to_drop
   - Fixed table name: vacation_periods → employee_periods

## Critical Bug Discovery: NAF vs CCC Confusion

### The Problem
Initial refactoring incorrectly assumed NAF = CCC. Actually:
- **CCC (Código Cuenta Cotización)**: Company location identifier
  - Appears ONCE in MSJ file header: "Codigo Cuenta Cotizacion  07 132297640"
  - Should be used for ClientLocation.ccc_ss
- **NAF (Número de Afiliación)**: Employee social security number
  - Appears per employee: "03 1137501265"
  - Should be used for Employee.ss_number

### MSJ File Format Example
```
       Codigo Cuenta Cotizacion  07 132297640    Regimen  0111
       Denominacion  DANIK IMPORT& SUPLY SL

     NAF            IPF             Apellidos y Nombre
-------------  ------------- ----------------------------------------------
 03 1137501265  1 078295290R RAMIS GARCIA DEISIS KARINA
          ALTA 01-08-2025 01-08-2025                       08/S 200 0,526
```

## Solution Part 2: Fix NAF vs CCC

### Files Modified (Part 2)
1. **scripts/extract_vida_ccc.py**
   - Added CCC extraction from file header using regex
   - Format CCC as joined string (e.g., "07132297640" not "07 132297640")
   - Added 'ccc' field to CSV output (first column)
   - All employee records now include the CCC from file header

2. **core/agent/vida_laboral.py**
   - Fixed all 3 handlers:
     - Changed `location_ccc = row.get('naf')` → `row.get('ccc')`
     - Kept `ss_number = row.get('naf')` (correct usage)
   - Removed misleading comments

3. **core/database.py**
   - Cleaned up comments (removed "also known as NAF")
   - Comments now correctly state company_ssn is the CCC

## Key Decisions

### User Preferences
- **Data strategy**: Reset database (fresh start), no migration
- **Location fields**: Minimal (just company_id, ccc_ss)
- **Views/indexes**: Minimal updates only
- **Code clarity**: Keep existing names, add comments

### Technical Details
- CCC format: Joined string without spaces (e.g., "07132297640")
- All employees from same MSJ file link to same ClientLocation (same CCC)
- Employee NAF stored in Employee.ss_number
- Company location CCC stored in ClientLocation.ccc_ss

## Data Flow
1. MSJ file → extract_vida_ccc.py extracts CCC from header + NAF per employee
2. CSV created with both 'ccc' and 'naf' fields
3. reprocess_vida_laboral.py reads CSV
4. vida_laboral.py handlers:
   - Use 'ccc' field to find/create ClientLocation
   - Use 'naf' field for Employee.ss_number
   - Create EmployeePeriod linking employee to location

## Testing Checklist
After changes:
1. Reset database
2. Import company locations from production
3. Process vida laboral CSV
4. Verify:
   - Client records have unique CIF
   - ClientLocation records have correct CCC (not employee NAF)
   - EmployeePeriod records link to locations
   - All employees from same file share same ClientLocation

## Files Changed Summary
- core/models.py
- core/database.py
- core/agent/vida_laboral.py
- core/production_models.py
- scripts/setup_database.py
- scripts/reset_database.py
- scripts/extract_vida_ccc.py

## Benefits
- Clean separation of company vs location data
- CIF uniqueness enforced at database level
- Employees explicitly linked to locations (CCCs)
- Matches production database structure
- Easier to query employees by CCC (what vida laboral uses)
- Correct data: CCC for locations, NAF for employees
