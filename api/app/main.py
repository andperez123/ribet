import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.db_init import get_database_error, initialize_database, is_database_ready
from app.routers import admin, brief, chat, health, ingest, org, reports, snapshots

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ribet")


@asynccontextmanager
async def lifespan(app: FastAPI):
    port = os.environ.get("PORT", "8000")
    logger.info(
        "api_starting port=%s database_url_configured=%s",
        port,
        bool(os.environ.get("DATABASE_URL")),
    )
    if os.environ.get("RIBET_SKIP_BACKGROUND_DB") == "1":
        initialize_database()
    else:
        asyncio.create_task(asyncio.to_thread(initialize_database))
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
app.include_router(snapshots.router)
app.include_router(chat.router)


@app.get("/health")
def health_check():
    """Liveness probe — returns 200 as soon as the API process is listening."""
    return {"ok": True}


@app.get("/health/ready")
def health_ready():
    """Readiness probe — verifies Postgres connectivity and schema init."""
    if not is_database_ready():
        err = get_database_error()
        if err:
            return JSONResponse(
                status_code=503,
                content={"ok": False, "database": err},
            )
        return JSONResponse(
            status_code=503,
            content={"ok": False, "database": "initializing"},
        )
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"ok": False, "database": str(e)},
        )
    return {"ok": True, "database": "connected"}


@app.get("/health/worker")
def health_worker():
    """Queue depth and worker heartbeat for ops / BFF pre-flight."""
    if not is_database_ready():
        return JSONResponse(
            status_code=503,
            content={"ok": False, "database": get_database_error() or "initializing"},
        )
    from app.database import SessionLocal
    from app.services.worker_status import get_worker_status

    db = SessionLocal()
    try:
        return get_worker_status(db)
    finally:
        db.close()
