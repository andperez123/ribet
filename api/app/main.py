from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import brief, health, ingest, org, reports
from app.seed import seed_demo_orgs


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(org.router)
app.include_router(health.router)
app.include_router(reports.router)
app.include_router(brief.router)


@app.get("/health")
def health_check():
    return {"ok": True}
