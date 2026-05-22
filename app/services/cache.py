from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

import redis.asyncio as redis

from app.config import gateway_config

if TYPE_CHECKING:
    from app.schemas import SearchResponse


def _build_redis_client() -> redis.Redis:
    return redis.from_url(gateway_config.redis.url, decode_responses=True)


def _cache_key(query: str, profile: str, language: str, freshness: str, limit: int) -> str:
    raw = f"{query}|{profile}|{language}|{freshness}|{limit}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"{gateway_config.redis.cache_prefix}{h}"


def _get_ttl(profile: str) -> int:
    mapping = {
        "tech": 21600,       # 6 hours
        "research": 86400,   # 24 hours
        "fresh_cn": 600,     # 10 minutes
    }
    return mapping.get(profile, gateway_config.redis.cache_ttl_seconds)


class CacheService:
    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = _build_redis_client()
        return self._client

    async def get(self, query: str, profile: str, language: str, freshness: str, limit: int) -> SearchResponse | None:
        try:
            key = _cache_key(query, profile, language, freshness, limit)
            data = await self.client.get(key)
            if data:
                from app.schemas import SearchResponse
                return SearchResponse.model_validate_json(data)
        except Exception:
            pass
        return None

    async def set(self, query: str, profile: str, language: str, freshness: str, limit: int, response: SearchResponse) -> None:
        try:
            key = _cache_key(query, profile, language, freshness, limit)
            ttl = _get_ttl(profile)
            await self.client.setex(key, ttl, response.model_dump_json())
        except Exception:
            pass

    async def ping(self) -> bool:
        try:
            return await self.client.ping()
        except Exception:
            return False


cache_service = CacheService()
