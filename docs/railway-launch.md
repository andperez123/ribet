# Railway launch checklist

Use this guide to deploy Ribet on Railway with sign-in, worker pipeline, and optional AI narration. Email (Resend) is **optional** and not required for launch.

**Related:** [`railway-deploy.md`](railway-deploy.md) (architecture), [`railway-env-setup.md`](railway-env-setup.md) (variable reference), [`clerk-auth.md`](clerk-auth.md) (auth details).

---

## What you need before starting

| Item | Notes |
|------|--------|
| Railway account | [railway.app](https://railway.app) |
| GitHub repo | This monorepo connected to a Railway project |
| Cloudflare R2 (or S3) | Bucket for uploaded ERP files |
| Clerk app (recommended for prod) | Google + email sign-in |
| OpenAI key (optional) | Only if `RIBET_NARRATION=on` |

Generate three secrets locally:

```bash
openssl rand -hex 32   # API_KEY
openssl rand -hex 32   # ADMIN_API_KEY
openssl rand -hex 32   # ADMIN_SECRET (web metrics page)
```

---

## 1. Create the Railway project

1. **New Project** → **Deploy from GitHub** → select the Rivet/Ribet repo.
2. **+ New** → **Database** → **PostgreSQL**.
3. Add **three services** from the same repo (do not deploy only from repo root without setting root directories):

| Service | Root directory | Dockerfile / start |
|---------|----------------|----------------------|
| **api** | `api` | `api/Dockerfile` (default uvicorn on `$PORT`) |
| **worker** | `api` | Same image; **Start command:** `python -m app.worker.process_job` |
| **web** | `web` | `web/Dockerfile` (Next.js on `$PORT`) |

4. **Worker:** leave **healthcheck path empty** (no HTTP server).

---

## 2. Cloudflare R2

1. Create bucket `ribet-uploads`.
2. Create API token (Object Read & Write).
3. Note: account ID, access key, secret, endpoint  
   `https://<account_id>.r2.cloudflarestorage.com`

Set on **api** and **worker** (identical values):

```
S3_ENDPOINT=https://<account_id>.r2.cloudflarestorage.com
S3_ACCESS_KEY=<access_key_id>
S3_SECRET_KEY=<secret_access_key>
S3_BUCKET=ribet-uploads
STORAGE_BACKEND=s3
```

---

## 3. Environment variables

### api

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
API_KEY=<openssl-1>
ADMIN_API_KEY=<openssl-2>
S3_ENDPOINT=...
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_BUCKET=ribet-uploads
STORAGE_BACKEND=s3
RIBET_ENV=production
CORS_ORIGINS=https://<your-web-public-url>
RIBET_APP_URL=https://<your-web-public-url>
```

Optional (AI narration in reports):

```
OPENAI_API_KEY=sk-...
RIBET_NARRATION=on
RIBET_NARRATION_TIMEOUT_SECONDS=90
OPENAI_MODEL=gpt-4o-mini
```

### worker (must match api for DB, API_KEY, S3)

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
API_KEY=<same-as-api>
S3_ENDPOINT=<same-as-api>
S3_ACCESS_KEY=<same-as-api>
S3_SECRET_KEY=<same-as-api>
S3_BUCKET=<same-as-api>
STORAGE_BACKEND=s3
RIBET_ENV=production
```

Copy `OPENAI_*` and `RIBET_NARRATION*` to worker if narration is enabled.

### web

```
NEXT_PUBLIC_UPLOAD_MODE=api
RIBET_ENV=production
FASTAPI_API_KEY=<same-as-api-API_KEY>
ADMIN_API_KEY=<same-as-api-ADMIN_API_KEY>
ADMIN_SECRET=<openssl-3>
FASTAPI_URL=http://${{api.RAILWAY_PRIVATE_DOMAIN}}:${{api.PORT}}
```

Replace `api` in `${{api.*}}` with your FastAPI service name in Railway.

**Clerk (recommended for production sign-in):**

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
CLERK_WEBHOOK_SECRET=whsec_...
```

**Without Clerk:** dashboard routes stay open and all users share `DEV_ORG_ID` (not suitable for real multi-tenant use). You can omit Clerk keys only for internal demos.

**Do not set** `DEV_ORG_ID` in production when Clerk is enabled — each signed-in org is provisioned automatically.

### Public domains

1. **api** → Networking → Generate domain → note URL (e.g. `https://ribet-api-production.up.railway.app`).
2. **web** → Networking → Generate domain.
3. Set **web** domain target port to match deploy logs (`ribet-web starting on 0.0.0.0:XXXX`). Often `PORT=3000` on web.
4. Update **api** `CORS_ORIGINS` to the **exact** web URL (no trailing slash).
5. Redeploy **api** after CORS changes.

### Healthchecks (Railway service settings)

| Service | Path |
|---------|------|
| api | `/health` |
| web | `/api/health` |
| worker | *(none)* |

---

## 4. Clerk setup (sign-in)

1. [Clerk Dashboard](https://dashboard.clerk.com) → new application.
2. Enable **Email** and **Google**.
3. **Allowed origins / redirects:** your web Railway URL and custom domain (e.g. `https://ribetlab.com`).
4. **Webhook** → endpoint `https://<web-domain>/api/webhooks/clerk` → event `organization.created` → copy signing secret → `CLERK_WEBHOOK_SECRET` on **web**.
5. Copy publishable + secret keys to web variables above.
6. Redeploy **web**.

**Verify sign-in:**

- Incognito → `https://<web-domain>/dashboard` → redirect to sign-in.
- Sign in → upload or view reports scoped to your org (not shared demo org).

**Demo without account:** landing **Try demo** still works (ephemeral org cookie; no Clerk required).

---

## 5. Deploy order

1. Postgres plugin linked.
2. Deploy **api** → wait healthy → `curl https://<api>/health` → `{"ok":true}`.
3. Deploy **worker** → check logs for `worker_started`.
4. Deploy **web** → `curl https://<web>/api/health` → `{"ok":true}`.
5. Run verification script (below).

---

## 6. Verify deployment

```bash
export WEB_URL="https://<your-web-domain>"
export API_URL="https://<your-api-domain>"
./scripts/verify-railway-deploy.sh
```

Expected:

- API `/health` and `/health/ready` OK
- Web `/api/health` OK
- Web `/api/health/worker` → `"worker_alive": true` (wait ~1 min after worker start)

### Manual smoke test

1. Incognito → `WEB_URL` → **Try demo data** → dashboard shows processing, then report.
2. Sign in (if Clerk enabled) → upload a CSV from [`fixtures/`](../fixtures/) with consent checked.
3. Founder metrics: `WEB_URL/admin/metrics?key=<ADMIN_SECRET>`.

### Pipeline telemetry (optional)

After a successful job, query `product_events` in Postgres for stage events:

`job_claimed`, `transform_completed`, `rules_completed`, `narration_completed` or `narration_failed`, `report_persist_completed`, `report_generated`.

---

## 7. Custom domain (optional)

1. **web** → Networking → Add custom domain → follow DNS instructions.
2. Wait until certificate is **Active** (fixes TLS mismatch in verify script).
3. Add domain to Clerk allowed origins.
4. Update `CORS_ORIGINS` and `RIBET_APP_URL` on **api** to the custom web URL.
5. Redeploy api + web.

---

## 8. Troubleshooting

| Symptom | Fix |
|---------|-----|
| Upload stuck on processing | Worker missing `DATABASE_URL` or `S3_*` (must match api) |
| CORS error in browser | `CORS_ORIGINS` on api must match web URL exactly |
| BFF 502 on upload | Wrong `FASTAPI_URL` or `FASTAPI_API_KEY` mismatch |
| `worker_alive: false` | Worker crash — check worker deploy logs |
| Web “Application failed to respond” | Web root dir must be `web`; PORT/domain port must match logs |
| 401 on upload when signed in | Clerk org not provisioned — check webhook + `CLERK_WEBHOOK_SECRET` |
| Empty finding narratives | Set `RIBET_NARRATION=on` + `OPENAI_API_KEY` on api and worker |
| Build fails at repo root | Set service **Root Directory** to `api` or `web` |

---

## 9. Post-launch (not required day one)

- Enable narration in production when ready (`RIBET_NARRATION=on`).
- Add Railway alerts on `worker_alive`, backlog growth (query `ingest_jobs` pending count).
- Resend email — skip until you need report-ready notifications.

---

## Quick copy-paste summary

**Services:** Postgres + api (`api/`) + worker (`api/`, `python -m app.worker.process_job`) + web (`web/`).

**Critical links:** web `FASTAPI_URL` → private api URL; web `FASTAPI_API_KEY` = api `API_KEY`; worker S3/DB = api.

**Auth:** Clerk on web + webhook; `RIBET_ENV=production` on api, worker, web.

**Verify:** `./scripts/verify-railway-deploy.sh` then demo + sign-in upload.
