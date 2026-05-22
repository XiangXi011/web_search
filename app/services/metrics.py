from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timezone

from app.schemas import SearchMetrics

logger = logging.getLogger("search.metrics")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _query_hash(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def _percentile(sorted_data: list[int], p: float) -> int:
    if not sorted_data:
        return 0
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


class MetricsCollector:
    """In-memory counters for aggregated metrics, flushed to logs periodically."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._start_time = time.monotonic()
        self._request_count = 0
        self._cache_hit_count = 0
        self._partial_result_count = 0
        self._empty_result_count = 0
        self._fallback_count = 0
        self._latencies: list[int] = []
        self._engine_success: dict[str, int] = {}
        self._engine_total: dict[str, int] = {}
        self._engine_timeout: dict[str, int] = {}
        self._engine_403: dict[str, int] = {}
        self._engine_429: dict[str, int] = {}

    async def record_search(
        self,
        latency_ms: int,
        cache_hit: bool,
        partial: bool,
        result_count: int,
        fallback_used: bool = False,
    ) -> None:
        async with self._lock:
            self._request_count += 1
            self._latencies.append(latency_ms)
            if cache_hit:
                self._cache_hit_count += 1
            if partial:
                self._partial_result_count += 1
            if result_count == 0:
                self._empty_result_count += 1
            if fallback_used:
                self._fallback_count += 1

    async def record_engine_result(
        self, engine: str, success: bool, error: str | None = None
    ) -> None:
        async with self._lock:
            self._engine_total[engine] = self._engine_total.get(engine, 0) + 1
            if success:
                self._engine_success[engine] = self._engine_success.get(engine, 0) + 1
            if error == "timeout":
                self._engine_timeout[engine] = self._engine_timeout.get(engine, 0) + 1
            elif error == "HTTP_403":
                self._engine_403[engine] = self._engine_403.get(engine, 0) + 1
            elif error == "HTTP_429":
                self._engine_429[engine] = self._engine_429.get(engine, 0) + 1

    def get_snapshot(self) -> dict:
        sorted_latencies = sorted(self._latencies)
        engine_success_rate = {}
        for engine, total in self._engine_total.items():
            success = self._engine_success.get(engine, 0)
            engine_success_rate[engine] = round(success / total, 4) if total > 0 else 0.0

        return {
            "timestamp": _now_iso(),
            "uptime_seconds": int(time.monotonic() - self._start_time),
            "request_count": self._request_count,
            "cache_hit_rate": round(
                self._cache_hit_count / self._request_count, 4
            ) if self._request_count > 0 else 0.0,
            "request_latency_p50": _percentile(sorted_latencies, 50),
            "request_latency_p95": _percentile(sorted_latencies, 95),
            "partial_result_rate": round(
                self._partial_result_count / self._request_count, 4
            ) if self._request_count > 0 else 0.0,
            "empty_result_rate": round(
                self._empty_result_count / self._request_count, 4
            ) if self._request_count > 0 else 0.0,
            "fallback_rate": round(
                self._fallback_count / self._request_count, 4
            ) if self._request_count > 0 else 0.0,
            "engine_success_rate": engine_success_rate,
            "engine_timeout_count": dict(self._engine_timeout),
            "engine_403_count": dict(self._engine_403),
            "engine_429_count": dict(self._engine_429),
        }


# Module-level singleton
metrics_collector = MetricsCollector()

# ---- Legacy per-request log (kept for backward compat) ----


def log_search(
    query: str,
    profile: str,
    latency_ms: int,
    cache_hit: bool,
    partial: bool,
    engines_used: list[str],
    engines_failed: list[str],
    result_count: int,
    top_domains: list[str],
    fallback_used: bool = False,
) -> None:
    metrics = SearchMetrics(
        timestamp=_now_iso(),
        query=query,
        profile=profile,
        query_hash=_query_hash(query),
        latency_ms=latency_ms,
        cache_hit=cache_hit,
        partial=partial,
        engines_used=engines_used,
        engines_failed=engines_failed,
        result_count=result_count,
        top_domains=top_domains,
        fallback_used=fallback_used,
    )
    logger.info("%s", metrics.model_dump_json())


def log_event(event_type: str, details: dict) -> None:
    payload = {
        "timestamp": _now_iso(),
        "event": event_type,
        **details,
    }
    logger.info("%s", json.dumps(payload, ensure_ascii=False))
