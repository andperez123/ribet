# Railway deployment guide

Deploy Ribet as a multi-service Railway project with product traction metrics at `/admin/metrics`.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Railway Project                       │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐ │
│  │   web   │→ │   api   │→ │ Postgres │  │  worker  │ │
│  │ Next.js │  │ FastAPI │  │  plugin  │← │  (poll)  │ │
│  └─────────┘  └────┬────┘  └──────────┘  └────┬─────┘ │
└────────────────────┼────────────────────────────┼───────┘
                     │                            │
                     └──────────┬─────────────────┘
                                ▼
                     Cloudflare R2 (S3-compatible)
```

## Services

| Service | Root directory | Build | Start command |
|---------|----------------|-------|---------------|
| **api** | `api/` | `api/Dockerfile` | (default) uvicorn on `$PORT` |
| **worker** | `api/` | `api/Dockerfile` | `python -m app.worker.process_job` |
| **web** | `web/` | `web/Dockerfile` | (default) `node server.js` on `$PORT` |

Add the **Postgres** plugin and link `DATABASE_URL` to **api** and **worker**.

## Environment variables

### API + Worker

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | From Railway Postgres plugin |
| `API_KEY` | Yes | Shared secret for org-scoped API calls |
| `ADMIN_API_KEY` | Yes | Secret for `/v1/admin/metrics` |
| `S3_ENDPOINT` | Yes | R2 or S3 endpoint URL |
| `S3_ACCESS_KEY` | Yes | Object storage access key |
| `S3_SECRET_KEY` | Yes | Object storage secret |
| `S3_BUCKET` | Yes | e.g. `ribet-uploads` |
| `STORAGE_BACKEND` | No | `s3` (default) or `local` for dev |
| `CORS_ORIGINS` | Yes | Comma-separated web URLs, e.g. `https://app.ribet.com` |

### Web

| Variable | Required | Description |
|----------|----------|-------------|
| `FASTAPI_URL` | Yes | Internal Railway URL for the **api** service |
| `FASTAPI_API_KEY` | Yes | Same value as API `API_KEY` |
| `DEV_ORG_ID` | Yes | Default org for BFF (until full auth) |
| `NEXT_PUBLIC_UPLOAD_MODE` | Yes | Set to `api` in production |
| `ADMIN_SECRET` | Yes | Gate for `/admin/metrics` page (cookie auth) |
| `ADMIN_API_KEY` | Yes | Same value as API `ADMIN_API_KEY` |

Generate strong random values for all secrets:

```bash
openssl rand -hex 32
```

## Cloudflare R2 setup

1. Create an R2 bucket named `ribet-uploads`
2. Create an API token with Object Read & Write
3. Set on **api** and **worker**:
   - `S3_ENDPOINT=https://<account_id>.r2.cloudflarestorage.com`
   - `S3_ACCESS_KEY=<access_key_id>`
   - `S3_SECRET_KEY=<secret_access_key>`
   - `S3_BUCKET=ribet-uploads`

No code changes required — storage uses boto3 S3-compatible API.

## Health checks

| Service | Path |
|---------|------|
| API | `GET /health` (includes DB check) |
| Web | `GET /api/health` |

Configure these in Railway service settings for reliable deploys.

## Traction metrics dashboard

After deploy, open:

```
https://<your-web-domain>/admin/metrics?key=<ADMIN_SECRET>
```

The query param sets a 7-day cookie; subsequent visits do not need the key.

### VC metrics reference

| Metric | VC narrative |
|--------|--------------|
| **Reports generated** | Value delivered — core product output |
| **Files uploaded** | Top-of-funnel usage |
| **Active orgs (30d)** | Real engagement, not vanity signups |
| **Activation rate** | % orgs that reached first report (PMF signal) |
| **Median time-to-first-report** | Onboarding speed |
| **Upload success rate** | Product reliability |
| **Report yield rate** | % uploads that produce actionable reports |
| **Repeat upload rate** | Retention / stickiness |
| **Findings delivered** | Quantified insight value |
| **Weekly charts** | Growth trajectory for investor updates |
| **Per-org table + CSV** | Multi-tenant proof, exportable for decks |

### API access (optional)

```bash
curl -s https://<api-domain>/v1/admin/metrics \
  -H "X-Admin-Key: $ADMIN_API_KEY" | jq
```

## Deploy order

1. Create Railway project + Postgres plugin
2. **Important:** For each service, set **Settings → Root Directory** (`api` or `web`). Deploying from repo root will fail — Railpack cannot detect a single app at the root.
3. Deploy **api** (Root Directory: `api`, Builder: Dockerfile), verify `GET /health`
4. Deploy **worker** (Root Directory: `api`, start command: `python -m app.worker.process_job`)
5. Deploy **web** (Root Directory: `web`, Builder: Dockerfile), set `FASTAPI_URL` to api internal URL
6. Configure R2 credentials on api + worker
7. Set `CORS_ORIGINS` to your web public URL
8. Visit `/admin/metrics?key=...` to confirm KPIs

### Fix: "Failed to build an image" with Railpack at repo root

If Railway shows **Builder: Railpack** and the service name is just `ribet` with no root directory:

1. Open the service → **Settings**
2. Set **Root Directory** to `api` (for the API service)
3. Under **Build**, set **Builder** to **Dockerfile** (or redeploy — `api/railway.toml` forces this)
4. Redeploy

Repeat for a second service (worker, same root `api`) and a third (web, root `web`).

## Local parity

Use the same admin keys locally:

```bash
# api/.env
ADMIN_API_KEY=dev-admin-secret

# web/.env.local
ADMIN_SECRET=dev-admin-secret
ADMIN_API_KEY=dev-admin-secret
```

Then open http://localhost:3000/admin/metrics?key=dev-admin-secret
