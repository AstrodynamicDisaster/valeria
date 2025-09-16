# ValerIA Automation — Minimal Runbook

This runbook helps you spin up the **n8n + PostgreSQL + MinIO + Metabase** stack and perform first-time configuration.

## 1) Prerequisites
- Docker & Docker Compose installed
- `.env` file created from `.env.sample`
- Ports available: 5432 (Postgres), 5678 (n8n), 9000/9001 (MinIO), 3000 (Metabase)

## 2) Start the Stack
```bash
docker compose --env-file .env up -d
docker compose ps
```

## 3) Verify Services
- **n8n**: http://localhost:5678  (login: N8N_BASIC_AUTH_USER/PASSWORD)
- **MinIO Console**: http://localhost:9001  (login: MINIO_ROOT_USER/PASSWORD)
- **Metabase**: http://localhost:3000  (initial setup wizard)
- **PostgreSQL**: localhost:5432 (use POSTGRES_* env vars)

## 4) Configure MinIO Bucket
1. Open MinIO Console → Create bucket named `${S3_BUCKET}` (default `valeria-docs`).
2. Create an access key/secret (or reuse root) and ensure they match `.env`.
3. (Optional) Create a folder structure:
   - `inbox/` (incoming uploads)
   - `processed/`
   - `errors/`
   - `exports/`

## 5) Initialize Database
Use your preferred SQL client:
```bash
docker exec -it valeria-postgres psql -U $POSTGRES_USER -d $POSTGRES_DB
```
Run your schema migrations (from the spec). For quick tests, you can paste the minimal DDL excerpt in the spec.

## 6) n8n First-Time Setup
1. Open n8n → Create owner account (if prompted) or use basic auth.
2. Create credentials:
   - **Postgres** (host `postgres`, db `${POSTGRES_DB}`)
   - **IMAP/SMTP** (for ingestion + drip emails)
   - **HTTP** for SS tool (base URL + token)
   - **S3** (MinIO endpoint + keys)
   - **OpenAI** (or local LLM endpoint)
3. Import or build workflows:
   - Onboarding trigger (Webhook/Manual)
   - Employee roster fetch (HTTP)
   - Checklist generator (Function + DB)
   - Ingestion watcher (IMAP/Webhook/S3)
   - OCR + AI parse (call OCR, then LLM)
   - Aggregations (DB nodes) + Exporters
   - Drip reminders (Schedule/Wait + Email)

## 7) Metabase
1. Complete first-run wizard; connect to the same Postgres (`valeria` DB).
2. Create starter dashboards:
   - Ingestion throughput (files/day)
   - Completion rate (% checklist done)
   - Extraction accuracy (manual QA flags)
   - Exceptions (documents with errors)

## 8) Security Notes
- Change all default passwords in `.env`.
- Restrict ports or place behind a reverse proxy (nginx/Traefik).
- Enable HTTPS (TLS termination on proxy); set `N8N_PROTOCOL=https` and update `WEBHOOK_URL`.
- Consider running OpenAI in **data control mode** or use a local LLM if GDPR requires full data residency.
- Encrypt backups; rotate keys.

## 9) Operations
- **Update images**: `docker compose pull && docker compose up -d`
- **Logs**: `docker compose logs -f n8n` (or any service)
- **Backup**:
  - Postgres: `pg_dump` on schedule
  - MinIO: lifecycle rules + external backups
- **Restore**: Restore DB dump → Re-sync MinIO bucket

## 10) Troubleshooting
- n8n cannot reach Postgres: check network + env vars.
- 403 on n8n: confirm basic auth creds.
- OCR fails: try alternate OCR backend or increase resources.
- LLM failures: check provider keys/rate limits; fall back to local.

---

**Done.** You can now build workflows and import the spec’s Mermaid diagrams into your docs.
