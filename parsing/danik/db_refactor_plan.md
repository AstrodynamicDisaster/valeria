     │ Database Schema Refactoring: Client → Client + ClientLocation                                                     │
     │                                                                                                                   │
     │ Changes Overview                                                                                                  │
     │                                                                                                                   │
     │ - Client table: Make CIF unique, remove ccc_ss field                                                              │
     │ - New ClientLocation table: Links companies to CCCs (minimal fields)                                              │
     │ - EmployeePeriod: Change from company_id (Client) → location_id (ClientLocation)                                  │
     │ - Database: Fresh reset (no migration)                                                                            │
     │                                                                                                                   │
     │ Files to Modify                                                                                                   │
     │                                                                                                                   │
     │ 1. core/models.py                                                                                                 │
     │ - Add unique=True to Client.cif                                                                                   │
     │ - Remove Client.ccc_ss field                                                                                      │
     │ - Create new ClientLocation model (id, company_id, ccc_ss, timestamps)                                            │
     │ - Update relationships: Client ↔ ClientLocation ↔ EmployeePeriod                                                  │
     │ - Change EmployeePeriod.company_id → EmployeePeriod.location_id                                                   │
     │                                                                                                                   │
     │ 2. core/database.py (3 functions)                                                                                 │
     │ - list_employee_ssns_for_company_period(): Query ClientLocation by ccc_ss, use location_id                        │
     │ - get_payroll_line_aggregates(): Same changes                                                                     │
     │ - get_employee_devengo_total(): Same changes                                                                      │
     │                                                                                                                   │
     │ 3. core/agent/vida_laboral.py (3 functions)                                                                       │
     │ - handle_alta(): Get/create ClientLocation by NAF (CCC), use location_id, add comment                             │
     │ - handle_baja(): Same changes + add comment                                                                       │
     │ - handle_vacacion(): Same changes + add comment                                                                   │
     │                                                                                                                   │
     │ 4. core/production_models.py                                                                                      │
     │ - insert_company_locations_into_local_clients(): Rewrite to create one Client (by CIF) + multiple ClientLocations │
     │ (by CCC)                                                                                                          │
     │                                                                                                                   │
     │ 5. scripts/setup_database.py                                                                                      │
     │ - Update EmployeePeriod indexes: company_id → location_id                                                         │
     │ - Add basic ClientLocation indexes (company_id, ccc_ss)                                                           │
     │ - Update views only where queries break (minimal changes)                                                         │
     │                                                                                                                   │
     │ 6. scripts/reset_database.py                                                                                      │
     │ - Add 'client_locations' to tables_to_drop list                                                                   │
     │                                                                                                                   │
     │ Files NOT Modified                                                                                                │
     │                                                                                                                   │
     │ - a3/tools.py: Works with CIF lookups (still valid)                                                               │
     │ - scripts/extract_vida_ccc.py: Data extraction unchanged                                                          │
     │ - scripts/reprocess_vida_laboral.py: Uses client.id (still valid)                                                 │
     │                                                                                                                   │
     │ Testing After Changes                                                                                             │
     │                                                                                                                   │
     │ 1. Reset database                                                                                                 │
     │ 2. Import company locations from production                                                                       │
     │ 3. Process vida laboral CSV                                                                                       │
     │ 4. Verify employee periods link to correct CCCs                                                                   │
     ╰───────────────────────────────────────────────────────────────────────────