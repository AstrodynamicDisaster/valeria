# Database Schema Migration Summary

## Overview
Successfully migrated the local development database schema to match the production Valeria database schema, and implemented a dual data source system for seamless switching between local test data and production data.

## Changes Completed

### Step 1-3: Schema Alignment ✅

#### 1. Updated `setup_database.py`
**Client Model → Production `companies` table:**
- `fiscal_name` → `name`
- `nif` → `cif`
- `id`: Integer → String (UUID format)
- Added fields: `fiscal_address`, `email`, `phone`, `begin_date`, `managed_by`, `payslips`
- Added legal representative fields: `legal_repr_first_name`, `legal_repr_last_name1`, `legal_repr_last_name2`, `legal_repr_nif`, etc.

**Employee Model → Production `company_employees` table:**
- `full_name` → split into `first_name`, `last_name`, `last_name2`
- `documento` → `identity_card_number`
- `nss` → `ss_number`
- `employment_start_date` → `begin_date`
- `employment_end_date` → `end_date`
- `client_id` → `company_id` (now String type)
- Added fields: `salary`, `role`, `phone`, `mail`, `address`, `identity_doc_type`, `employee_status`

#### 2. Updated `generate_test_data.py`
- Modified to generate data with production schema structure
- Splits names into first_name/last_name/last_name2
- Generates additional required fields (salary, role, contact info)
- Updated all field references throughout

#### 3. Updated `valeria_agent.py`
- Updated all Client/Employee queries to use new field names
- Modified name handling to work with split name fields
- Fixed employee matching logic to search across name components
- Updated all references in reporting and detection methods

### Steps 4-5: Production Integration ✅

#### 4. Created Production Database Adapter (`production_models.py`)
- **ProductionCompany**: Read-only model for production `companies` table
- **ProductionEmployee**: Read-only model for production `company_employees` table
- Utility functions for common queries
- Connection management with error handling

#### 5. Implemented Dual Data Source System

**Configuration:**
- Added `USE_PRODUCTION_DATA` flag to `.env`
  - `false` (default): Uses local seeded test data
  - `true`: Reads from production database (read-only)

**Helper Methods in `ValeriaAgent`:**
- `_get_company(cif, company_id, name)`: Gets company from appropriate source
- `_get_employee(identity_card_number, employee_id, company_id)`: Gets employee from appropriate source
- `_list_employees_for_company(company_id)`: Lists all employees for a company

**Key Features:**
- Automatic conversion: Production models → Local models (consistent interface)
- Transparent to rest of codebase (no changes needed in payroll processing)
- **Payroll data always writes to local database** (regardless of data source)
- Graceful fallback if production connection fails

## How It Works

### Development Mode (`USE_PRODUCTION_DATA=false`)
```python
# .env
USE_PRODUCTION_DATA=false

# Agent reads companies/employees from local database
# Can use generated test data for development
company = agent._get_company(cif="B12345678")  # → Local DB
employee = agent._get_employee(identity_card_number="12345678A")  # → Local DB

# Payrolls write to local database
payroll = Payroll(...)  # → Local DB
```

### Production Mode (`USE_PRODUCTION_DATA=true`)
```python
# .env
USE_PRODUCTION_DATA=true

# Agent reads companies/employees from production (read-only)
company = agent._get_company(cif="B67491308")  # → Production DB
employee = agent._get_employee(identity_card_number="36154300W")  # → Production DB

# Payrolls still write to local database (HYBRID APPROACH)
payroll = Payroll(employee_id=employee.id, ...)  # → Local DB
```

## Database Structure

### Local Database Tables
- `clients` - Company information (matches production `companies`)
- `employees` - Employee information (matches production `company_employees`)
- `payrolls` - **Extracted payroll data (local only)**
- `payroll_lines` - **Individual payroll concept lines (local only)**
- `documents` - Document tracking
- `nomina_concepts` - Spanish payroll concepts dictionary
- `checklist_items` - Missing document tracking

### Production Database (Read-Only)
- `companies` - Real company data
- `company_employees` - Real employee data

## Testing

Run the test script to verify configuration switching:
```bash
python test_dual_source.py
```

**Test Results:**
- ✅ Local mode: Correctly reads from local database
- ✅ Production mode: Successfully connects to production (read-only)
- ✅ Helper methods return consistent Employee/Client objects
- ✅ Automatic conversion from production to local models works
- ✅ All 40 employees from KEBEL LOGISTICS loaded correctly

## Next Steps

### For Development:
1. Generate test data: `python generate_test_data.py`
2. Process payslips with local data
3. Test missing payslip detection
4. Validate reports

### For Production:
1. Set `USE_PRODUCTION_DATA=true` in `.env`
2. Process real payslips
3. System will:
   - Read real employee/company data from production
   - Validate employees exist
   - Write extracted payroll data to local database
   - Generate reports with production employee IDs

## Benefits

✅ **Seamless Development**: Test with synthetic data without touching production
✅ **Production Ready**: Simple flag switch to use real data
✅ **Data Isolation**: Payroll extractions stored separately from production
✅ **Read-Only Safety**: Can't accidentally modify production data
✅ **Consistent Interface**: Same code works in both modes
✅ **Easy Testing**: Switch modes anytime for validation

## Files Modified/Created

### Modified:
- `setup_database.py` - Updated schema models
- `generate_test_data.py` - Updated data generation
- `valeria_agent.py` - Added dual source support
- `.env` - Added USE_PRODUCTION_DATA flag

### Created:
- `production_models.py` - Production database models
- `test_dual_source.py` - Test script for verification
- `MIGRATION_SUMMARY.md` - This document

## Important Notes

⚠️ **Production Database Access**: Read-only connection via `PROD_URL`
⚠️ **Payroll Data**: Always stored in local database, never in production
⚠️ **Employee Validation**: In production mode, employees must exist in production DB
⚠️ **UUID vs Integer IDs**: Company IDs are UUIDs (strings), Employee IDs are integers

## Configuration Reference

```bash
# .env file
USE_PRODUCTION_DATA=false   # Use local test data (development)
USE_PRODUCTION_DATA=true    # Use production data (when live)
PROD_URL="postgresql://..."  # Production database connection (read-only)
```

---

**Status**: ✅ Completed and Tested
**Date**: 2025-10-09
**Ready for**: Development and Production use
