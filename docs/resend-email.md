## Resend email (report-ready + weekly brief)

The worker can send:

- **Report-ready** email (sent when a report finishes processing)
- **Weekly brief** email (scheduled Mondays 08:00 server time)

Implementation lives in:

- `api/app/services/email.py`
- Templates in `api/app/templates/`

### 1) Verify a sending domain in Resend

- Verify `ribetlab.com` (or your chosen domain).
- Create a sender identity like `reports@ribetlab.com`.

### 2) Set Railway variables (api + worker)

Railway → **api** → Variables:

- `RESEND_API_KEY`
- `RESEND_FROM=Ribet <reports@ribetlab.com>`
- `RIBET_APP_URL=https://ribetlab.com` (used to generate report links in emails)

Copy the same `RESEND_API_KEY` and `RESEND_FROM` to **worker**.

Also set `RIBET_APP_URL` on **worker** (recommended so worker-sent emails always link correctly).

### 3) Configure recipients

Emails send to the organization’s recipients:

- If org has recipients set (UI), those are used.
- Otherwise, if `DEFAULT_BRIEF_RECIPIENT` is set on the API/worker, it will be used for bootstrapping/testing.

For early testing, set:

- `DEFAULT_BRIEF_RECIPIENT=you@ribetlab.com`

### 4) Validate

1. Upload a CSV and wait for the worker to finish.\n
2. Confirm the ingest job reaches `done` and a report exists.\n
3. Confirm you receive a **report-ready** email.\n

If you don’t receive an email:

- Confirm `RESEND_API_KEY` is present on **worker** (emails are triggered by the worker after report generation).
- Confirm the org has recipients configured (or set `DEFAULT_BRIEF_RECIPIENT`).
- Check worker logs for `report_ready_email_failed`.

