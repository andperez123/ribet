/** FastAPI paths — mirrored in docs/openapi.yaml */
export const API = {
  ingest: {
    uploads: "/v1/ingest/uploads",
    jobs: "/v1/ingest/jobs",
    job: (id: string) => `/v1/ingest/jobs/${id}`,
  },
  reports: {
    latest: "/v1/reports/latest",
    byId: (id: string) => `/v1/reports/${id}`,
  },
  findings: "/v1/findings",
  health: {
    score: "/v1/health/score",
    history: "/v1/health/history",
  },
  brief: {
    weekly: "/v1/brief/weekly",
  },
  org: {
    progress: "/v1/org/progress",
    coverage: "/v1/org/coverage",
    gaps: "/v1/org/gaps",
  },
  chat: {
    query: "/v1/chat/query",
  },
} as const;

/** Next.js BFF paths — browser calls these */
export const BFF = {
  health: "/api/health",
  ingest: {
    uploads: "/api/ingest/uploads",
    jobs: "/api/ingest/jobs",
    job: (id: string) => `/api/ingest/jobs/${id}`,
  },
  reports: {
    latest: "/api/reports/latest",
    byId: (id: string) => `/api/reports/${id}`,
  },
  findings: "/api/findings",
  healthScore: "/api/health/score",
  healthHistory: "/api/health/history",
  briefWeekly: "/api/brief/weekly",
  orgProgress: "/api/org/progress",
  orgCoverage: "/api/org/coverage",
  orgFeatures: "/api/org/features",
  chatQuery: "/api/chat/query",
} as const;
