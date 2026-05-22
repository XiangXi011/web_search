from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.config import gateway_config
from app.services.cooldown import cooldown_manager


class SearXNGClient:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(gateway_config.searxng.global_deadline_seconds + 2),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    async def search_one(
        self,
        query: str,
        engine: str,
        language: str | None = None,
        time_range: str | None = None,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any] | None:
        if await cooldown_manager.is_cooling_down(engine):
            return None

        params: dict[str, Any] = {
            "q": query,
            "format": "json",
            "engines": engine,
        }
        if language and language != "all":
            params["language"] = language
        if time_range:
            params["time_range"] = time_range

        url = f"{gateway_config.searxng.base_url}{gateway_config.searxng.search_path}"
        to = timeout_seconds or gateway_config.searxng.default_timeout_seconds

        try:
            resp = await self.client.get(url, params=params, timeout=to)
            if resp.status_code == 200:
                await cooldown_manager.reset_timeout_count(engine)
                data = resp.json()
                results = data.get("results", [])
                return {"engine": engine, "results": results}
            else:
                await cooldown_manager.handle_error(engine, resp.status_code, resp.text)
                return {"engine": engine, "error": f"HTTP_{resp.status_code}", "results": []}
        except httpx.TimeoutException:
            await cooldown_manager.record_timeout(engine)
            return {"engine": engine, "error": "timeout", "results": []}
        except httpx.ConnectError:
            await cooldown_manager.handle_error(engine, None, None)
            return {"engine": engine, "error": "connection_failed", "results": []}
        except Exception as e:
            return {"engine": engine, "error": str(e), "results": []}

    async def search_all(
        self,
        query_variants: list[str],
        engines: list[str],
        language: str | None = None,
        time_range: str | None = None,
        per_engine_timeout: float | None = None,
    ) -> list[dict[str, Any]]:
        tasks = []
        for query in query_variants:
            for engine in engines:
                if await cooldown_manager.is_cooling_down(engine):
                    continue
                tasks.append(
                    self.search_one(query, engine, language, time_range, per_engine_timeout)
                )

        if not tasks:
            return []

        deadline = gateway_config.searxng.global_deadline_seconds
        results = await self._gather_with_deadline(tasks, deadline)
        return results

    async def _gather_with_deadline(
        self, coros: list[Any], deadline: float
    ) -> list[dict[str, Any]]:
        tasks = [asyncio.create_task(c) for c in coros]

        done, not_done = await asyncio.wait(tasks, timeout=deadline, return_when=asyncio.ALL_COMPLETED)
        for task in not_done:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        out = []
        for task in done:
            try:
                result = task.result()
                if result is not None:
                    out.append(result)
            except Exception as e:
                out.append({"engine": "unknown", "error": str(e), "results": []})
        return out

    async def health_check(self) -> bool:
        try:
            url = f"{gateway_config.searxng.base_url}{gateway_config.searxng.search_path}"
            resp = await self.client.get(url, params={"q": "test", "format": "json"}, timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self.client.aclose()


searxng_client = SearXNGClient()
