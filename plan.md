# Province inference plan (Modelo 190)

## Goal
Infer `provincia` for payroll-derived perceptors **only** from production DB postal codes (company + location), then fall back to `default_provincia` (`"00"`). No CCC-based or address-text parsing.

## Updated approach (constraints honored)
- **Source of truth**: production DB postal codes only.
- **Preferred query approach** (step 2): enrich the payroll line query with location context (ClientLocation + Client) so we can derive provincia per employee/payroll from local data that was imported from production.
- **Full implementation of step 3**: persist production postal codes into local `clients` and `client_locations`, so 190 generation can read locally without runtime prod queries.

---

## Plan (detailed)

### 1) Data model: persist production postal codes locally (full step 3)
Add postal code fields so we can store production data locally.

- **Update `core/models.py`**
  - `Client`: add `postal_code: Column(Text)`.
  - `ClientLocation`: add `postal_code: Column(Text)`.

- **Update DB setup / migration**
  - `scripts/setup_database.py`: include the new columns automatically for fresh DBs.
  - Add a migration script (new) or a documented SQL snippet to alter existing tables:
    - `ALTER TABLE clients ADD COLUMN postal_code TEXT;`
    - `ALTER TABLE client_locations ADD COLUMN postal_code TEXT;`

Files to touch:
- `core/models.py`
- `scripts/setup_database.py`
- (new) `scripts/migrate_add_postal_code.py` or a documented SQL snippet in README.

### 2) Production sync: copy postal codes into local tables
Use production data only.

- **Update `core/production_models.insert_company_locations_into_local_clients()`**
  - From `ProductionCompany.company_postal_code` → local `Client.postal_code`.
  - From `ProductionLocation.postal_code` → local `ClientLocation.postal_code`.
  - Ensure the fields are set on both new and existing records (when `skip_existing=False` or when updating).

Files to touch:
- `core/production_models.py`

### 3) Preferred query enrichment (step 2)
Enrich payroll line query with location + company postal codes.

- **Update `fetch_payroll_lines_for_cif_period()` in `190.py`**
  - Select `ClientLocation.postal_code` and `Client.postal_code` alongside existing fields.
  - Keep the current `eligible_payrolls` subquery to avoid duplicates; extend it to include location join if needed.

Files to touch:
- `190.py`

### 4) Province resolution logic (production-only)
Compute `provincia` from postal codes stored locally (which were sourced from production).

- **Add helper in `190.py`**
  - `_postal_to_provincia(postal_code: str) -> Optional[str]`
    - Take first 2 digits from a 5-digit postal code.
    - Validate digits; return `None` if invalid.

- **In `build_perceptor_inputs()`**
  - For each row/perceptor:
    1) Use `ClientLocation.postal_code` → provincia.
    2) Else use `Client.postal_code` → provincia.
    3) Else use `config.default_provincia` (`"00"`).
  - No CCC parsing, no address parsing.

Files to touch:
- `190.py`

### 5) Manual clave G behavior (unchanged, but consistent)
Manual entries continue to honor the `provincia` in the bucket file; if omitted, they fall back to `default_provincia` (`"00"`). No auto-inference.

Files to touch:
- None (already implemented)

---

## Output behavior after change
- Payroll-derived perceptors will carry province codes inferred from **production postal codes** only.
- Manual clave G entries remain explicitly controlled by the bucket file.
- If production postal codes are missing, province defaults to `"00"`.

---

## Verification steps (post-implementation)
1) Refresh local client + locations from production:
   - `python - <<'PY' ... insert_company_locations_into_local_clients(...) ... PY`
2) Spot-check local data:
   - Query `clients.postal_code` and `client_locations.postal_code` for a known CIF.
3) Run 190 generation and verify province codes:
   - `python 190.py --cif <CIF> --year 2025 --mapping <mapping.json> --out reports/modelo190_<CIF>_2025.txt`

