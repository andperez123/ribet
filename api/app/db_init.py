import logging
import time

from sqlalchemy import text

from app.database import engine

logger = logging.getLogger("ribet.db")


def wait_for_database(max_attempts: int = 30, delay_seconds: float = 2.0) -> None:
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
