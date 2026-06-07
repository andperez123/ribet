## Clerk auth (Google + email sign-in)

This repo supports optional authentication via Clerk for `/dashboard` routes.

When Clerk is enabled, the Next.js middleware protects `/dashboard(.*)` and redirects users to sign-in (see `web/middleware.ts`).

Each signed-in user gets a **personal workspace** (mapped to a local org via `user_<clerkUserId>`). If the user selects a Clerk organization, that org is used instead. Reports, uploads, and dashboard data are scoped to the active workspace — users only see and manage their own data unless they share a team org.

### 1) Create a Clerk application

- Create a new app in Clerk.
- Enable **Email** sign-in (code or email link).
- Enable **Google** as a social provider.

### 2) Configure URLs for production

In Clerk, add these as allowed origins/redirects:

- `https://ribetlab.com`
- `https://ribetweb-production.up.railway.app` (Railway fallback domain, optional)

If you use `www`, add:

- `https://www.ribetlab.com`

### 3) Configure the webhook (org provisioning)

This app uses Clerk organizations. When an organization is created, the web app provisions a matching local org in the API via:

- `POST /api/webhooks/clerk` → `POST /v1/org/from-clerk`

In Clerk, create a webhook:

- **Endpoint URL**: `https://ribetlab.com/api/webhooks/clerk`
- **Events**: `organization.created`

Copy the webhook secret value.

### 4) Set Railway variables (web service)

Railway → **web** → **Variables**:

- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`
- `CLERK_WEBHOOK_SECRET` (from the webhook you created)

Redeploy the web service.

### 5) Sanity check

- Visit `https://ribetlab.com/dashboard`
- Confirm you are redirected to sign-in
- Sign in with:
  - a business email (email sign-in), or
  - Google (Gmail or Google Workspace)

If you want **no auth while debugging uploads**, remove the three Clerk variables above from Railway web and redeploy.

