from __future__ import annotations

import logging
import time
from pathlib import Path

from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app.seed import seed_demo_orgs

logger = logging.getLogger("ribet.db")

_db_ready = False
_db_error: str | None = None


def is_database_ready() -> bool:
    return _db_ready


def get_database_error() -> str | None:
    return _db_error


def wait_for_database(max_attempts: int = 60, delay_seconds: float = 2.0) -> None:
    """Wait for Postgres to accept connections (Railway plugin cold start)."""
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("database_connected attempt=%s", attempt)
            return
        except Exception as exc:
            last_error = exc
            logger.warning(
                "database_not_ready attempt=%s/%s error=%s",
                attempt,
                max_attempts,
                exc,
            )
            if attempt < max_attempts:
                time.sleep(delay_seconds)
    raise RuntimeError(
        "Could not connect to Postgres. Set DATABASE_URL on this Railway service "
        "(reference it from the Postgres plugin, e.g. ${{Postgres.DATABASE_URL}})."
    ) from last_error


def _run_migrations() -> None:
    try:
        from alembic import command
        from alembic.config import Config

        ini = Path(__file__).resolve().parent.parent / "alembic.ini"
        cfg = Config(str(ini))
        command.upgrade(cfg, "head")
        logger.info("alembic_upgrade_complete")
    except Exception as exc:
        logger.warning("alembic_upgrade_failed fallback=create_all error=%s", exc)
        Base.metadata.create_all(bind=engine)


def initialize_database() -> None:
    """Run in a background thread so /health responds while Postgres warms up."""
    global _db_ready, _db_error
    try:
        wait_for_database()
        _run_migrations()
        # Idempotent — required for Railway web DEV_ORG_ID until Clerk provisions orgs.
        seed_demo_orgs()
        _db_ready = True
        logger.info("database_initialized")
    except Exception as exc:
        _db_error = str(exc)
        logger.error("database_init_failed error=%s", exc)
