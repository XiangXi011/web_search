from fastapi import APIRouter

from app.config import settings
from app.schemas import HealthResponse, ReadyDependency, ReadyResponse
from app.services.cache import cache_service
from app.services.searxng_client import searxng_client

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="search-gateway",
        version=settings.version,
    )


@router.get("/ready", response_model=ReadyResponse)
async def ready() -> ReadyResponse:
    redis_ok = await cache_service.ping()
    searxng_ok = await searxng_client.health_check()

    if redis_ok and searxng_ok:
        return ReadyResponse(
            status="ready",
            dependencies=ReadyDependency(redis="ok", searxng="ok"),
        )

    return ReadyResponse(
        status="degraded",
        dependencies=ReadyDependency(
            redis="ok" if redis_ok else "failed",
            searxng="ok" if searxng_ok else "failed",
        ),
    )
