# Railway environment setup (walkthrough-ready)

Use this checklist in the **Railway dashboard** so demo, upload, and dashboard work end-to-end.

Replace service names if yours differ (`api`, `worker`, `web`, `Postgres`).

---

## Step 0 — Generate secrets (run once locally)

```bash
openssl rand -hex 32   # use for API_KEY
openssl rand -hex 32   # use for ADMIN_API_KEY
openssl rand -hex 32   # use for ADMIN_SECRET (web only)
```

Save all three values in a password manager. You will reuse them below.

---

## Step 1 — Postgres on **api** and **worker**

Open **api** → **Variables** → **+ New Variable** → **Add Reference**:

| Variable | Value |
|----------|--------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |

Repeat on **worker** (same reference).

> If your database service is not named `Postgres`, pick the correct service from the reference dropdown.

---

## Step 2 — Shared secrets on **api** and **worker**

Set these on **api** first, then copy the **same values** to **worker**.

| Variable | Example / notes |
|----------|-----------------|
| `API_KEY` | output of `openssl rand -hex 32` |
| `ADMIN_API_KEY` | second `openssl` output |
| `S3_ENDPOINT` | `https://<account_id>.r2.cloudflarestorage.com` |
| `S3_ACCESS_KEY` | R2 access key id |
| `S3_SECRET_KEY` | R2 secret |
| `S3_BUCKET` | `ribet-uploads` |
| `STORAGE_BACKEND` | `s3` |
| `RIBET_ENV` | `production` on **api**, **worker**, and **web** (enables strict sign-in on BFF) |

On **api** only (for now):

| Variable | Value |
|----------|--------|
| `CORS_ORIGINS` | Your public web URL, e.g. `https://ribet-web-production.up.railway.app` |
| `RIBET_APP_URL` | Same public web URL (email links) |

Optional (AI narration — recommended for staging/prod when testing analysis):

| Variable | Where |
|----------|--------|
| `OPENAI_API_KEY` | **api** + **worker** |
| `RIBET_NARRATION` | `on` on **api** + **worker** |
| `RIBET_NARRATION_TIMEOUT_SECONDS` | **api** + **worker** (default 90) |

Optional (email — not required for launch):

| Variable | Where |
|----------|--------|
| `RESEND_API_KEY` | **api** + **worker** |
| `RESEND_FROM` | **api** + **worker**, e.g. `Ribet <reports@yourdomain.com>` |

**Worker must match api** for: `DATABASE_URL`, `API_KEY`, all `S3_*`, `STORAGE_BACKEND`. Missing S3 on worker is the #1 cause of jobs stuck in `processing`.

---

## Step 3 — Worker start command

**worker** → **Settings** → **Deploy**:

- **Root Directory:** `api`
- **Start command:** `python -m app.worker.process_job`
- **Healthcheck path:** leave **empty** (or use config path `api/railway.worker.toml`)

Redeploy worker after env changes.

---

## Step 4 — Web → API networking

**web** → **Variables**:

| Variable | Value |
|----------|--------|
| `NEXT_PUBLIC_UPLOAD_MODE` | `api` |
| `FASTAPI_API_KEY` | **same** as api `API_KEY` |
| `FASTAPI_URL` | See below |
| `RIBET_ENV` | `production` |
| `ADMIN_SECRET` | third `openssl` value (metrics page cookie) |
| `ADMIN_API_KEY` | **same** as api `ADMIN_API_KEY` |

**Clerk (production sign-in — recommended):**

| Variable | Value |
|----------|--------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | From Clerk dashboard |
| `CLERK_SECRET_KEY` | From Clerk dashboard |
| `CLERK_WEBHOOK_SECRET` | Webhook signing secret (`organization.created` → `/api/webhooks/clerk`) |

See [`clerk-auth.md`](clerk-auth.md). Omit `DEV_ORG_ID` when Clerk is enabled.

**Demo-only (no Clerk):**

| Variable | Value |
|----------|--------|
| `DEV_ORG_ID` | `11111111-1111-1111-1111-111111111111` |

### `FASTAPI_URL` (critical)

Use Railway **private** networking — **not** the public api URL browsers use.

In **web** → **Variables**, add:

```
FASTAPI_URL=http://${{api.RAILWAY_PRIVATE_DOMAIN}}:${{api.PORT}}
```

- `${{api.*}}` — replace `api` with your FastAPI service name in Railway.
- Click **Add Reference** if the UI offers it instead of typing manually.

If private DNS fails (BFF 502/503), temporary fallback for debugging only:

```
FASTAPI_URL=https://<your-public-api-domain>
```

Prefer private URL in production.

### `CORS_ORIGINS` on **api**

Must include the **exact** public web origin (scheme + host, no trailing slash):

```
https://your-web-service.up.railway.app
```

Redeploy **api** after changing `CORS_ORIGINS`.

---

## Step 5 — Web service settings

**web** → **Settings**:

- **Root Directory:** `web`
- **Public domain:** generated under Networking
- **PORT:** match what Next listens on (often `3000`; domain target port must match deploy logs)

Redeploy **web** after env changes.

---

## Step 6 — Verify (copy your URLs)

```bash
export WEB_URL="https://YOUR-WEB-DOMAIN"
export API_URL="https://YOUR-API-DOMAIN"
./scripts/verify-railway-deploy.sh
```

Expected:

- API `/health` → `ok`
- API `/health/ready` → database connected
- Web `/api/health` → `ok`
- Web `/api/health/worker` → `worker_alive: true` (after worker has been running ~1 min)

### If verification fails with “TLS cert mismatch”
If `./scripts/verify-railway-deploy.sh` reports a TLS cert mismatch for `WEB_URL`, your custom domain is pointing at Railway but **Railway has not provisioned HTTPS for that domain** yet.

Fix in Railway:

1. Open **web** → **Networking / Domains**
2. Add `YOUR-WEB-DOMAIN` (and optionally `www.YOUR-WEB-DOMAIN`)
3. Follow Railway’s DNS instructions (CNAME/ALIAS/A record, depending on your DNS provider)
4. Wait for the domain to show as **Active** (certificate issued), then retry verification

Tip: While debugging, you can temporarily set `WEB_URL` to Railway’s generated `*.up.railway.app` domain for the **web** service, since that domain always has a valid certificate.

---

## Step 7 — Run the product walkthrough

1. Incognito → `WEB_URL`
2. **Try demo data** → dashboard should show processing banner, then report
3. Fresh incognito → `WEB_URL/#upload` → upload a fixture CSV with consent checked
4. Optional: `/admin/metrics?key=YOUR_ADMIN_SECRET`

Full script: [`railway-new-user-walkthrough.md`](railway-new-user-walkthrough.md)

---

## Quick triage

| Symptom | Fix |
|---------|-----|
| Upload/demo stuck on processing | Worker missing `DATABASE_URL` or `S3_*` |
| Browser CORS error | `CORS_ORIGINS` on api missing web URL |
| BFF 500 on upload | Wrong `FASTAPI_URL` or `FASTAPI_API_KEY` mismatch |
| `worker_alive: false` | Worker crash-looping — check worker deploy logs |
| Web “Application failed to respond” | Root dir not `web`, or PORT/domain mismatch |

---

## Copy-paste variable groups (dashboard)

### api

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
API_KEY=<your-api-key>
ADMIN_API_KEY=<your-admin-api-key>
S3_ENDPOINT=https://<account>.r2.cloudflarestorage.com
S3_ACCESS_KEY=<r2-access-key>
S3_SECRET_KEY=<r2-secret>
S3_BUCKET=ribet-uploads
STORAGE_BACKEND=s3
CORS_ORIGINS=https://<your-web-domain>
RIBET_APP_URL=https://<your-web-domain>
```

### worker (same as api for shared vars)

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
API_KEY=<same-as-api>
S3_ENDPOINT=<same-as-api>
S3_ACCESS_KEY=<same-as-api>
S3_SECRET_KEY=<same-as-api>
S3_BUCKET=<same-as-api>
STORAGE_BACKEND=s3
```

### web

```
NEXT_PUBLIC_UPLOAD_MODE=api
RIBET_ENV=production
FASTAPI_URL=http://${{api.RAILWAY_PRIVATE_DOMAIN}}:${{api.PORT}}
FASTAPI_API_KEY=<same-as-api-API_KEY>
ADMIN_SECRET=<your-admin-secret>
ADMIN_API_KEY=<same-as-api-ADMIN_API_KEY>
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=<clerk-pk>
CLERK_SECRET_KEY=<clerk-sk>
CLERK_WEBHOOK_SECRET=<clerk-whsec>
```

**Full launch walkthrough:** [`railway-launch.md`](railway-launch.md)
