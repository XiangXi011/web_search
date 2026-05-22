import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import health, search
from app.services.searxng_client import searxng_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await searxng_client.close()


app = FastAPI(
    title="Search Gateway",
    description="LLM Web Search Gateway with quality control and failure isolation",
    version=settings.version,
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(search.router)


@app.get("/")
async def root():
    return {"service": "search-gateway", "version": settings.version}
