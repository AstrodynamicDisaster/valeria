# ValerIA

Prototype for Spanish payroll ingestion and reporting (vida laboral, payslips, Modelo 190).
Run scripts from the repo root.

## Requirements

- Python 3.10+
- PostgreSQL (local or via Docker Compose)

## Quick start (local DB)

```bash
pip install -r requirements.txt
docker compose up -d postgres
python scripts/setup_database.py
```

## Production sync (optional, read-only)

Set `PROD_URL` and sync a company + locations (postal codes are stored locally):

```bash
python - <<'PY'
from core.production_models import create_production_engine, create_production_session, insert_company_locations_into_local_clients

prod_engine = create_production_engine()
prod_session = create_production_session(prod_engine)
insert_company_locations_into_local_clients(prod_session, "<CIF>", skip_existing=False)
prod_session.close()
PY
```

## Vida laboral ingestion

1) Convert the .msj to CSV:

```bash
python scripts/extract_vida_ccc.py path/to/vida_laboral.msj
# writes output.csv in the current directory
```

2) Load the CSV into the local DB:

```bash
python scripts/reprocess_vida_laboral.py output.csv "<Company Name or CIF>"
```

## Payroll ingestion

```bash
python scripts/ingest_payrolls_mapped.py payrolls_mapped.json
```

## Missing payslips report

```bash
python scripts/generate_missing_payslips_report.py --client-id <UUID> --format csv --save
```

## Modelo 190

1) Build the concept mapping:

```bash
python scripts/export_190_concepts.py --bucket-template --out 190_buckets.yml
# edit 190_buckets.yml
python scripts/export_190_concepts.py --mapping-from 190_buckets.yml --mapping-out 190_mapping.json
```

2) Generate the file:

```bash
python 190.py --cif <CIF> --year 2025 --mapping 190_mapping.json --out reports/modelo190_<CIF>_2025.txt
```
