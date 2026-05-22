from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException

from app.config import gateway_config, settings
from app.schemas import (
    ConfidenceBreakdown,
    EngineFailReason,
    EngineSkipReason,
    EnginesStatusResponse,
    EngineStatus,
    SearchMeta,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from app.services.cache import cache_service
from app.services.classifier import classify
from app.services.cooldown import cooldown_manager
from app.services.dedup import deduplicate_results
from app.services.engine_router import (
    get_engines,
    get_profile_language,
    get_profile_time_range,
    get_profile_timeout,
)
from app.services.metrics import log_search, metrics_collector
from app.services.query_expander import expand
from app.services.ranker import rank_results
from app.services.searxng_client import searxng_client
from app.services.source_classifier import classify_source
from app.services.fallback import fallback_orchestrator
from app.utils.url import get_domain

router = APIRouter(prefix="/v1")


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    start = time.perf_counter()
    query = req.query.strip()
    limit = min(req.limit, gateway_config.search.max_limit)

    # Determine profile
    profile = req.profile
    if profile == "auto":
        profile = classify(query).value

    # Language
    language = req.language
    if language == "auto":
        language = get_profile_language(profile)

    # Freshness
    freshness = req.freshness
    time_range = None
    if freshness == "auto":
        time_range = get_profile_time_range(profile)
    elif freshness != "auto":
        time_range = freshness

    # Cache check
    if req.use_cache:
        cached = await cache_service.get(query, profile, language, freshness, limit)
        if cached:
            cached.meta.cache_hit = True
            return cached

    # Query expansion
    query_variants = expand(query, profile)

    # Engine routing
    engines = get_engines(profile)
    per_engine_timeout = get_profile_timeout(profile)

    # Build skip/fail tracking
    engines_skipped: list[EngineSkipReason] = []
    engines_failed: list[EngineFailReason] = []

    for engine in engines:
        if await cooldown_manager.is_cooling_down(engine):
            engines_skipped.append(EngineSkipReason(engine=engine, reason="cooldown"))

    # Record engines excluded by profile selection
    all_engines_pool: set[str] = set()
    for profile_cfg in gateway_config.profiles.values():
        all_engines_pool.update(profile_cfg.engines)
    for engine in sorted(all_engines_pool):
        if engine not in engines:
            engines_skipped.append(EngineSkipReason(engine=engine, reason="profile_excluded"))

    # Search
    engine_results = await searxng_client.search_all(
        query_variants=query_variants,
        engines=engines,
        language=language if language != "all" else None,
        time_range=time_range,
        per_engine_timeout=per_engine_timeout,
    )

    # Collect raw results
    all_raw: list[dict[str, Any]] = []
    used_engines: set[str] = set()
    for er in engine_results:
        engine = er.get("engine", "")
        if er.get("error"):
            engines_failed.append(EngineFailReason(engine=engine, reason=er["error"]))
            await metrics_collector.record_engine_result(engine, False, er["error"])
            continue
        used_engines.add(engine)
        await metrics_collector.record_engine_result(engine, True)
        for r in er.get("results", []):
            enriched = dict(r)
            enriched["engine"] = engine
            enriched.setdefault("engines", [engine])
            all_raw.append(enriched)

    # Deduplicate
    deduped = deduplicate_results(all_raw)

    # Rank
    ranked = rank_results(deduped, query, profile)

    # Build response items
    results: list[SearchResultItem] = []
    for idx, item in enumerate(ranked[:limit], start=1):
        url = item.get("url", "")
        title = item.get("title", "")
        snippet = item.get("content", "") or item.get("snippet", "")
        domain = get_domain(url)
        source_type = item.get("_source_type", "unknown")
        breakdown = item.get("_breakdown", {})
        engines_list = list(item.get("engines", []))

        why = ""
        if source_type == "official_doc":
            why = "官方文档域名"
        elif source_type == "github_repo":
            why = "GitHub 项目仓库"
        elif source_type == "github_issue":
            why = "GitHub Issue / PR"
        elif source_type == "academic":
            why = "学术论文来源"
        elif "stackoverflow" in domain:
            why = "StackOverflow 技术问答"
        elif source_type == "community":
            why = "技术社区讨论"
        else:
            why = f"{domain} 来源"

        results.append(
            SearchResultItem(
                rank=idx,
                title=title,
                url=url,
                snippet=snippet,
                domain=domain,
                source_type=source_type,
                confidence=round(item.get("_final_score", 0.0), 4),
                confidence_breakdown=ConfidenceBreakdown(
                    searxng_score=breakdown.get("searxng_score", 0.0),
                    domain_authority=breakdown.get("domain_authority", 0.0),
                    keyword_match=breakdown.get("keyword_match", 0.0),
                    engine_consensus=breakdown.get("engine_consensus", 0.0),
                    freshness=breakdown.get("freshness", 0.0),
                    source_type=breakdown.get("source_type", 0.0),
                    penalty=breakdown.get("penalty", 0.0),
                ),
                engines=engines_list,
                why_selected=why,
            )
        )

    # Fallback if enabled and too few results
    fallback_used = False
    if (
        gateway_config.search.enable_commercial_fallback
        and len(results) < gateway_config.search.min_results_before_fallback
    ):
        fb_results, fb_provider = await fallback_orchestrator.search(query, limit)
        if fb_results:
            fallback_used = True
            used_engines.add(f"fallback:{fb_provider}")
            for fb in fb_results:
                fb_domain = get_domain(fb.get("url", ""))
                fb_source = classify_source(fb.get("url", ""), fb.get("title", ""), fb.get("snippet", ""))
                results.append(
                    SearchResultItem(
                        rank=len(results) + 1,
                        title=fb.get("title", ""),
                        url=fb.get("url", ""),
                        snippet=fb.get("snippet", ""),
                        domain=fb_domain,
                        source_type=fb_source,
                        confidence=0.5,
                        confidence_breakdown=ConfidenceBreakdown(),
                        engines=[f"fallback:{fb_provider}"],
                        why_selected=f"商业 fallback ({fb_provider})",
                    )
                )

    latency_ms = int((time.perf_counter() - start) * 1000)
    partial = len(engines_failed) > 0 and len(results) > 0

    warnings: list[str] = [
        "Search snippets are not full-page evidence.",
    ]
    if partial:
        warnings.append("Partial results returned because one or more engines timed out or failed.")
    if len(results) == 0:
        warnings.append("No results found for the given query.")

    response = SearchResponse(
        query=query,
        profile=profile,
        query_variants=query_variants,
        results=results,
        meta=SearchMeta(
            total_results=len(results),
            latency_ms=latency_ms,
            cache_hit=False,
            partial=partial,
            engines_used=sorted(used_engines),
            engines_skipped=engines_skipped,
            engines_failed=engines_failed,
        ),
        warnings=warnings,
    )

    # Cache
    if req.use_cache:
        await cache_service.set(query, profile, language, freshness, limit, response)

    # Metrics
    log_search(
        query=query,
        profile=profile,
        latency_ms=latency_ms,
        cache_hit=False,
        partial=partial,
        engines_used=sorted(used_engines),
        engines_failed=[f.engine for f in engines_failed],
        result_count=len(results),
        top_domains=[r.domain for r in results[:5]],
        fallback_used=fallback_used,
    )
    await metrics_collector.record_search(
        latency_ms=latency_ms,
        cache_hit=False,
        partial=partial,
        result_count=len(results),
        fallback_used=fallback_used,
    )

    return response


@router.get("/engines/status", response_model=EnginesStatusResponse)
async def engines_status() -> EnginesStatusResponse:
    all_cooldowns = await cooldown_manager.list_all()
    all_engines = set()
    for profile_cfg in gateway_config.profiles.values():
        all_engines.update(profile_cfg.engines)

    statuses: list[EngineStatus] = []
    for engine in sorted(all_engines):
        info = next((c for c in all_cooldowns if c.get("engine") == engine), None)
        if info:
            statuses.append(
                EngineStatus(
                    name=engine,
                    status="cooldown",
                    cooldown_until=info.get("cooldown_until"),
                    last_error=info.get("last_error"),
                )
            )
        else:
            statuses.append(
                EngineStatus(
                    name=engine,
                    status="healthy",
                    cooldown_until=None,
                )
            )

    return EnginesStatusResponse(engines=statuses, metrics=metrics_collector.get_snapshot())
