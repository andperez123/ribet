# Railway new-user walkthrough

UX test script for Ribet on Railway as an **async operational intelligence workflow**.

**How to judge the MVP:** confirmation, persistence, async processing, and trust—not speed.

## Replace placeholders

| Placeholder | You fill in |
|---|---|
| `https://YOUR-WEB-DOMAIN` | Railway public URL for **web** |
| `https://YOUR-API-DOMAIN` | Railway public URL for **api** |
| `YOUR_ADMIN_SECRET` | Value of web `ADMIN_SECRET` |

## Pre-flight

1. `GET https://YOUR-API-DOMAIN/health` — JSON OK
2. `GET https://YOUR-API-DOMAIN/health/ready` — DB connected (not 503)
3. `GET https://YOUR-WEB-DOMAIN/api/health` — OK
4. `GET https://YOUR-WEB-DOMAIN/api/health/worker` — queue depth + `worker_alive`
5. Worker service running: `python -m app.worker.process_job` with same env as **api** (see [railway-deploy.md](railway-deploy.md))

Use **incognito** for each path.

## Paths

- **A — Demo:** Try demo data → confirm message on dashboard → leave/return → report when ready
- **B — Upload:** `/#upload` → consent → fixture CSV → confirmation banner → dashboard updates
- **C — Email:** Settings recipient + `RESEND_API_KEY` → report-ready email after job completes
- **D — Auth:** `/sign-up`, `/sign-in` (Clerk or fallback)
- **E — Metrics:** `/admin/metrics?key=YOUR_ADMIN_SECRET`

## Comment template

```markdown
## Environment
- Web URL:
- API URL:
- Clerk enabled? yes / no
- Email enabled? yes / no

## Pre-flight
- API health OK? yes / no
- API ready OK? yes / no
- Web health OK? yes / no
- Worker health OK? yes / no
- Worker env confirmed? yes / no

## Path A — Try demo
- Demo confirmation shown? yes / no
- Time to confirmation:
- Time to report ready:
- Did user know they could leave? yes / no
- Dashboard useful? yes / partial / no

## Path B — Manual upload
- Consent gate obvious? yes / no
- Upload confirmation clear? yes / no
- Could user leave and return safely? yes / no

## Path C — Email
- Email sent? yes / no
- Email link worked? yes / no

## Overall
- Would I trust this with real ERP exports? yes / maybe / no
- Did it feel broken or just processing?
- Top 3 fixes:
- Top 3 delights:
```
