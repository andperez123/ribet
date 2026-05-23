# Ribet API Contract

Source of truth: [`openapi.yaml`](./openapi.yaml)

## Primary artifact

**Operational Health Report** — `GET /v1/reports/latest`

Sections: executive summary, financial/operational findings, risk areas, suggested actions, trend snapshot, health score.

## Browser → BFF → FastAPI

1. Browser selects a business sector (financials, manufacturing, orders, sales) and `POST /api/ingest/uploads` with multipart `files` + `sector`
2. BFF proxies to `POST {FASTAPI_URL}/v1/ingest/uploads` with `X-Org-Id` + `X-API-Key`
3. Browser polls `GET /api/ingest/jobs/:id`
4. Worker runs ETL → rules → report (orders/sales unknown files complete without a report)
5. Worker recomputes `org_progress` (sector coverage + unlocked logistics capabilities)
6. Client fetches `GET /v1/reports/latest` and `GET /v1/org/progress` for dashboard

## Job lifecycle

```
pending → processing → done | error
```

## Headers

```
X-API-Key: dev-secret
X-Org-Id: 11111111-1111-1111-1111-111111111111
```

## Dev database migration

If `ingest_jobs` already exists without `sector`, run once against Postgres:

```sql
ALTER TABLE ingest_jobs ADD COLUMN IF NOT EXISTS sector VARCHAR(32);
```

`org_progress` is created on API/worker startup via `create_all` when missing.

## Sectors and unlocks

| Sector | Typical exports |
|--------|-----------------|
| `financials` | AR/AP aging, GL detail |
| `manufacturing` | Inventory on hand |
| `orders` | PO / procurement exports |
| `sales` | Sales orders, revenue |

`GET /v1/org/progress` returns per-sector coverage and logistics capabilities (`cash_flow_logistics`, `inventory_logistics`, etc.) unlocked when enough sector data is uploaded.

## Normalized tables

customers, vendors, gl_transactions, invoices, inventory_items (+ operational_findings, health_snapshots, operational_memory, operational_reports, org_progress)

## Benchmark tables (schema only, not populated)

benchmark_cohorts, benchmark_metrics, org_benchmark_eligibility
