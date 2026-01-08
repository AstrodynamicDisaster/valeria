<INSTRUCTIONS>
## Skills
A skill is a set of local instructions to follow that is stored in a `SKILL.md` file. Below is the list of skills that can be used. Each entry includes a name, description, and file path so you can open the source for full instructions when using a specific skill.
### Available skills
- skill-creator: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Codex's capabilities with specialized knowledge, workflows, or tool integrations. (file: /Users/albert/.codex/skills/.system/skill-creator/SKILL.md)
- skill-installer: Install Codex skills into $CODEX_HOME/skills from a curated list or a GitHub repo path. Use when a user asks to list installable skills, install a curated skill, or install a skill from another repo (including private repos). (file: /Users/albert/.codex/skills/.system/skill-installer/SKILL.md)
### How to use skills
- Discovery: The list above is the skills available in this session (name + description + file path). Skill bodies live on disk at the listed paths.
- Trigger rules: If the user names a skill (with `$SkillName` or plain text) OR the task clearly matches a skill's description shown above, you must use that skill for that turn. Multiple mentions mean use them all. Do not carry skills across turns unless re-mentioned.
- Missing/blocked: If a named skill isn't in the list or the path can't be read, say so briefly and continue with the best fallback.
- How to use a skill (progressive disclosure):
  1) After deciding to use a skill, open its `SKILL.md`. Read only enough to follow the workflow.
  2) If `SKILL.md` points to extra folders such as `references/`, load only the specific files needed for the request; don't bulk-load everything.
  3) If `scripts/` exist, prefer running or patching them instead of retyping large code blocks.
  4) If `assets/` or templates exist, reuse them instead of recreating from scratch.
- Coordination and sequencing:
  - If multiple skills apply, choose the minimal set that covers the request and state the order you'll use them.
  - Announce which skill(s) you're using and why (one short line). If you skip an obvious skill, say why.
- Context hygiene:
  - Keep context small: summarize long sections instead of pasting them; only load extra files when needed.
  - Avoid deep reference-chasing: prefer opening only files directly linked from `SKILL.md` unless you're blocked.
  - When variants exist (frameworks, providers, domains), pick only the relevant reference file(s) and note that choice.
- Safety and fallback: If a skill can't be applied cleanly (missing files, unclear instructions), state the issue, pick the next-best approach, and continue.
</INSTRUCTIONS>

# ValerIA (valeria) — Agent Guide

This repository is a Spanish payroll processing and onboarding automation prototype. It centers on:
- Ingesting “vida laboral” employment events (ALTA/BAJA/VAC) into a local Postgres DB
- Processing payroll documents (PDF payslips / settlements) with LLM-based extraction
- Persisting extracted payroll totals + line items, then generating “missing payslips” reports
- Supporting Spanish tax reporting queries (e.g., Modelo 190 helpers)

## What to ignore (repo navigation)
When doing repo analysis or broad refactors, you can usually skip:
- `parsing/` (customer-specific inputs/configs)
- `tests/` (root)
- `web/` (static frontend assets)
- `core/agent/` (agent implementation; `core/valeria_agent.py` is just a shim)
- `backups/`, `archive/`

## Tech stack
- Language/runtime: Python (code uses `X | Y` unions → Python 3.10+ recommended)
- Web: Flask (`web_app.py`) + `flask-cors`
- DB: PostgreSQL (Docker Compose), accessed via SQLAlchemy ORM (`core/models.py`) + psycopg2
- LLM/Vision extraction:
  - OpenAI (`openai` SDK)
  - Google Gemini (`google-genai`; supports default Google credentials and project/location config for Vertex-style usage)
  - Optional local inference via Ollama (`ollama`), though it is not the primary path in the modules inspected
- PDF/text tooling: PyMuPDF (`pymupdf`), Pillow; PDF generation helpers include WeasyPrint + pdfkit
- Workflow/ops: Docker Compose provides Postgres + n8n + Metabase

## Primary entrypoints
- Local web API + chat prototype: `python web_app.py --debug`
  - Uses in-memory session storage; not production-ready (no persistence/Redis, no auth beyond whatever you add)
  - Expects `OPENAI_API_KEY` if using the agent web UI flow
- Orchestration CLI (ties together prod import + vida laboral + report): `python main.py <folder-under-parsing>`
  - Reads `parsing/<folder>/config.json` and `.msj` files; folder contents are intentionally treated as external inputs
- DB setup/reset:
  - `python scripts/setup_database.py` (creates tables, indexes, views, seeds `nomina_concepts`)
  - `python scripts/reset_database.py` (destructive)

## Core workflows (high level)
1) **Bring up dependencies**
   - `docker compose up -d postgres` (optional: `n8n`, `metabase`)
2) **Create schema**
   - `python scripts/setup_database.py`
3) **Create clients + locations**
   - Either from production DB (`core/production_models.py` + `scripts/reprocess_prod_query.py`) or manually
4) **Ingest vida laboral events → EmployeePeriod**
   - MSJ → CSV: `scripts/extract_vida_ccc.py` (extracts company CCC + employee NAF/SSN)
   - CSV → DB: `scripts/reprocess_vida_laboral.py` (calls `core/vida_laboral.process_row`)
5) **Ingest payroll extractions**
   - `scripts/ingest_payrolls_mapped.py` loads mapped JSON into `payrolls` + `payroll_lines`
6) **Generate missing payslips report**
   - `scripts/generate_missing_payslips_report.py` wraps `core/missing_payslips.py`

## Data model (local DB)
See `core/models.py`.
- `clients` (UUID): one row per company (unique `cif`)
- `client_locations`: one row per CCC (unique `ccc_ss`), FK → `clients.id`
- `employees`: identity (DNI/NIE), `ss_number`, names
- `employee_periods`: ALTA/BAJA/VAC periods, FK → `employees.id` and `client_locations.id`
- `documents`: local-file-backed documents with optional extraction results and confidence
- `payrolls`: per-employee payroll snapshot; stores `periodo` JSON and normalized totals as columns
- `payroll_lines`: normalized line items (category + concept + flags)
- `checklist_items`: missing-doc tracking (used by reporting/reminders)

Note: some queries treat “company_ssn” as CCC (location code). Don’t confuse it with employee NAF/SSN.

## Key modules (where to look first)
- DB + storage helpers: `core/database.py`
  - `create_database_engine()` reads `POSTGRES_*` env vars
  - Local document storage under `./documents/` (can disable with `DISABLE_LOCAL_DOCUMENTS=true`)
- Production (read-only) models + import: `core/production_models.py`
  - Uses `PROD_URL` (treat as sensitive); intended for reads only
- Vida laboral ingestion logic: `core/vida_laboral.py` + `core/vida_laboral_utils.py`
  - Idempotent-ish period merging; prefers SSN match, then DNI/NIE
- Missing payslips detection/reporting: `core/missing_payslips.py`
- Deterministic payslip parsing + optional LLM validation: `core/payslip_parser.py`
- Vision/LLM-based document parsing router: `core/vision_model/auto_parser.py` and `core/vision_model/process_documents.py`
- A3 (Wolters Kluwer) integration: `core/a3/*` (OAuth refresh token, REST calls, mapping utilities)

## Configuration / environment variables
See `.env` (do not commit real secrets).
- Postgres: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, plus optional `POSTGRES_HOST`, `POSTGRES_PORT`
- Production DB (read-only access): `PROD_URL`
- LLM (agent/web app): `LLM_PROVIDER` (documented as `openai|local`), `OPENAI_API_KEY`
- LLM (vision_model): OpenAI uses `OPENAI_API_KEY`; Gemini typically relies on Google Application Default Credentials and the code-level `project`/`location` passed to `AutoParser`/parsers.
- n8n: `N8N_*`, `WEBHOOK_URL`, etc. (used by Docker Compose deployment; repo code doesn’t directly orchestrate workflows)
- A3 provider: `A3_SUBSCRIPTION_KEY`, `A3_CLIENT_ID`, `A3_CLIENT_SECRET`, `A3_REFRESH_TOKEN`

## Development practices for this repo
- Prefer running scripts from repo root so imports resolve (many scripts do `sys.path.insert(...)`).
- Keep production reads and local writes clearly separated:
  - `core/production_models.py` and `scripts/reprocess_prod_query.py` should never write to prod.
- Be careful with identifiers:
  - Employee SSN/NAF lives in `Employee.ss_number`
  - Company location CCC lives in `ClientLocation.ccc_ss`
- When adding new DB functionality, keep it idempotent:
  - Imports should safely re-run without duplicating rows (use unique indexes or merge logic)
- Avoid leaking secrets in logs; scrub env output in scripts.
- If extending the web app, don’t rely on global in-memory `sessions` for anything beyond prototyping.

## Known “paper cuts” (good to fix when iterating)
- `README.md` references files that now live under `scripts/` (e.g., `setup_database.py`).
- `core/missing_payslips.py` currently hardcodes `start_date_cap = date(2025, 1, 1)` during analysis (may not be intended).

## Suggested next documentation (optional)
- A “golden path” dev walkthrough: reset DB → import one client from prod → ingest vida laboral → process PDFs → report.
- A schema diagram and a short glossary (CIF vs CCC vs NAF/SSN vs DNI/NIE).
