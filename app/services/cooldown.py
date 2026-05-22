from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import redis.asyncio as redis

from app.config import gateway_config

if TYPE_CHECKING:
    pass


def _build_redis_client() -> redis.Redis:
    return redis.from_url(gateway_config.redis.url, decode_responses=True)


def _cooldown_key(engine: str) -> str:
    return f"{gateway_config.redis.cooldown_prefix}{engine}"


class CooldownManager:
    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = _build_redis_client()
        return self._client

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    async def is_cooling_down(self, engine: str) -> bool:
        try:
            key = _cooldown_key(engine)
            data = await self.client.get(key)
            if not data:
                return False
            info = json.loads(data)
            until = datetime.fromisoformat(info["cooldown_until"])
            return until > self._now()
        except Exception:
            return False

    async def get_cooldown_info(self, engine: str) -> dict | None:
        try:
            key = _cooldown_key(engine)
            data = await self.client.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass
        return None

    async def trigger_cooldown(self, engine: str, reason: str, duration_seconds: int) -> None:
        try:
            until = (self._now() + timedelta(seconds=duration_seconds)).isoformat()
            payload = {
                "reason": reason,
                "cooldown_until": until,
                "last_error": reason,
            }
            await self.client.setex(_cooldown_key(engine), duration_seconds, json.dumps(payload))
        except Exception:
            pass

    async def handle_error(self, engine: str, status_code: int | None, response_text: str | None) -> None:
        cfg = gateway_config.cooldown
        text = (response_text or "").lower()

        if status_code == 403:
            await self.trigger_cooldown(engine, "HTTP_403", cfg.http_403_seconds)
        elif status_code == 429:
            await self.trigger_cooldown(engine, "HTTP_429", cfg.http_429_seconds)
        elif status_code is None:
            await self.trigger_cooldown(engine, "connection_failed", cfg.connection_fail_seconds)
        elif "captcha" in text or "验证" in text or "verification" in text:
            await self.trigger_cooldown(engine, "captcha", cfg.captcha_seconds)

    async def record_timeout(self, engine: str) -> None:
        key = f"timeout_count:{engine}"
        try:
            pipe = self.client.pipeline()
            pipe.incr(key)
            pipe.expire(key, 300)
            results = await pipe.execute()
            count = results[0]
            cfg = gateway_config.cooldown
            if count >= cfg.timeout_fail_threshold:
                await self.trigger_cooldown(engine, "consecutive_timeout", cfg.timeout_cooldown_seconds)
        except Exception:
            pass

    async def reset_timeout_count(self, engine: str) -> None:
        try:
            await self.client.delete(f"timeout_count:{engine}")
        except Exception:
            pass

    async def list_all(self) -> list[dict]:
        try:
            pattern = f"{gateway_config.redis.cooldown_prefix}*"
            keys = []
            async for k in self.client.scan_iter(match=pattern):
                keys.append(k)
            if not keys:
                return []
            values = await self.client.mget(keys)
            result = []
            for k, v in zip(keys, values):
                if v:
                    info = json.loads(v)
                    name = k.decode() if isinstance(k, bytes) else k
                    prefix = gateway_config.redis.cooldown_prefix
                    engine = name[len(prefix):] if name.startswith(prefix) else name
                    result.append({"engine": engine, **info})
            return result
        except Exception:
            return []


cooldown_manager = CooldownManager()
