import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("API_KEY", "dev-secret")
os.environ.setdefault("ADMIN_API_KEY", "dev-admin-secret")
os.environ.setdefault("STORAGE_BACKEND", "local")
os.environ.setdefault("LOCAL_STORAGE_PATH", "/tmp/ribet-test-uploads")
os.environ.setdefault("RIBET_ENV", "test")
os.environ.setdefault("RIBET_SKIP_BACKGROUND_DB", "1")

USE_SQLITE = os.environ.get("TEST_USE_SQLITE") == "1"

if USE_SQLITE:
    os.environ["DATABASE_URL"] = "sqlite://"

from app.database import Base, get_db  # noqa: E402
import app.database as database  # noqa: E402
from app.main import app  # noqa: E402

if USE_SQLITE:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    from app.config import settings

    engine = create_engine(settings.database_url, pool_pre_ping=True)

TestSession = sessionmaker(bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    database.engine = engine
    database.SessionLocal = TestSession
    import app.db_init as db_init_mod
    import app.main as main_mod

    db_init_mod.engine = engine
    main_mod.engine = engine
    Base.metadata.create_all(bind=engine)
    from app.db_init import initialize_database

    initialize_database()
    import app.db_init as db_init_mod

    db_init_mod._db_ready = True
    db_init_mod._db_error = None
    yield
    if USE_SQLITE:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
