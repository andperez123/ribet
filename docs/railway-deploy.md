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

| Service | Path | Purpose |
|---------|------|---------|
| API | `GET /health` | Liveness (Railway healthcheck) |
| API | `GET /health/ready` | Readiness (includes DB check) |
| Web | `GET /api/health` | Liveness |

Configure these in Railway service settings for reliable deploys. Do **not** set a healthcheck on **worker** — it only runs `python -m app.worker.process_job` (no uvicorn).

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
   - **Healthcheck path:** leave empty (worker has no HTTP server)
   - Optional: **Config file path** = `railway.worker.toml` (disables healthcheck via config-as-code)
5. Deploy **web** (Root Directory: `web`, Builder: Dockerfile), set `FASTAPI_URL` to api internal URL
   - **Generate domain:** use the port shown under **Networking** after deploy (often Railway’s injected `PORT`, not a guess). If the app listens on `3000`, the public target port must be `3000` — `3080` causes “Application failed to respond”.
6. Configure R2 credentials on api + worker
7. Set `CORS_ORIGINS` to your web public URL
8. Visit `/admin/metrics?key=...` to confirm KPIs

### Fix: "Failed to build an image" with Railpack at repo root

Railway may show **Builder: Railpack** even when a Dockerfile exists. The repo now includes a **root `Dockerfile`** (builds the API) plus `railway.toml` and `railway.json` forcing Docker builds.

**Do this in the Railway dashboard:**

1. Open the **ribet** service → **Settings** → **Build**
2. Change **Builder** from **Railpack** to **Dockerfile**
3. Set **Dockerfile path** to `Dockerfile` (repo root)
4. **Redeploy**

If Builder is locked to Railpack, add a service variable:

```
RAILWAY_DOCKERFILE_PATH=Dockerfile
```

Then redeploy.

**Alternative (cleaner for monorepo):** set **Root Directory** to `api` and use `api/Dockerfile` instead of the root Dockerfile.

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

## Fix: Healthcheck failure with 0 variables

If deploy fails at **Network › Healthcheck** and the service shows **0 Variables**:

1. **+ New** → **Database** → **PostgreSQL** (in the same project)
2. Open the **ribet** (API) service → **Variables** → **+ New Variable**
3. Add `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`  
   (click **Add Reference** and pick your Postgres service — the name may not be exactly `Postgres`)
4. Add `API_KEY` and `ADMIN_API_KEY` (random secrets)
5. **Redeploy**

Without `DATABASE_URL`, the API cannot start (it defaults to `localhost:5432`, which does not exist on Railway).

## Fix: Web public URL “Application failed to respond”

Railway’s proxy is hitting a different port than Node is listening on (or the service built the wrong app).

**Checklist (in order):**

1. **Root Directory** must be `web` (not repo root). Root root builds the **API** on port 8000; a domain aimed at `3000` will always fail.
2. **Variables** → `PORT` must match the public domain port. If you see `PORT=3080`, either delete it and redeploy, or set the domain target port to `3080` — they must be identical.
3. **Networking** → public domain → target port `3000` (typical for Next.js after setting `PORT=3000` in Variables).
4. **Deploy logs** → look for `ribet-web starting on 0.0.0.0:XXXX` and use that `XXXX` as the domain port.
5. Redeploy **ribet_web** after fixing the above.
