# Ribet

Operational intelligence infrastructure for manufacturers.

## Quick start

### 1. Start backend

```bash
docker compose up --build
```

Services:
- API: http://localhost:8000
- Postgres: localhost:5433 (host; 5432 if already in use on your machine)
- MinIO: http://localhost:9000 (console :9001)

Demo org ID: `11111111-1111-1111-1111-111111111111`

### 2. Start frontend

```bash
cd web
cp .env.local.example .env.local
npm install
npm run dev
```

Upload fixture CSVs from [`fixtures/`](fixtures/) on http://localhost:3000

### 3. View report

```bash
curl -s http://localhost:8000/v1/reports/latest \
  -H "X-API-Key: dev-secret" \
  -H "X-Org-Id: 11111111-1111-1111-1111-111111111111" | jq
```

## Architecture

```
web (Next.js BFF) → api (FastAPI) → Postgres
                         ↓ worker → ETL → Rules → Operational Health Report
                         ↓ MinIO/R2 (raw files)
```

## API endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /v1/ingest/uploads` | Upload CSV/XLSX/PDF |
| `GET /v1/ingest/jobs/{id}` | Job status |
| `GET /v1/reports/latest` | Operational Health Report |
| `GET /v1/findings` | Raw findings |
| `GET /v1/health/score` | Health score |
| `GET /v1/health/history` | Trend history |
| `GET /v1/brief/weekly` | Weekly executive brief |

See [`docs/openapi.yaml`](docs/openapi.yaml).

## Fixtures

Sample exports with intentional problems in [`fixtures/`](fixtures/):
- `ar_aging_jobboss.csv` — AR >90 spike
- `gl_detail_jobboss.csv` — inventory adjustments, unmapped GL
- `inventory_jobboss.csv` — orphan items
- `ap_aging_jobboss.csv` — vendor concentration, negative AP

## Tests

```bash
cd api
pip install -r requirements.txt
DATABASE_URL=sqlite:///./test.db pytest tests/ -v
```

## Project structure

```
Ribet/
├── api/           FastAPI + worker
├── web/           Next.js landing + BFF
├── fixtures/      Demo CSV exports
└── docs/          OpenAPI contract
```
