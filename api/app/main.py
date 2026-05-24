from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app.db_init import wait_for_database
from app.routers import admin, brief, health, ingest, org, reports
from app.seed import seed_demo_orgs


@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_database()
    Base.metadata.create_all(bind=engine)
    seed_demo_orgs()
    yield


app = FastAPI(
    title="Ribet API",
    description="Operational intelligence infrastructure for manufacturers",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(ingest.router)
app.include_router(org.router)
app.include_router(health.router)
app.include_router(reports.router)
app.include_router(brief.router)


@app.get("/health")
def health_check():
    """Liveness probe — returns 200 when the API process is up."""
    return {"ok": True}


@app.get("/health/ready")
def health_ready():
    """Readiness probe — verifies Postgres connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"ok": False, "database": str(e)},
        )
    return {"ok": True, "database": "connected"}
