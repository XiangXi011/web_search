from __future__ import annotations

import math
import re
from datetime import datetime, timezone

from app.config import gateway_config
from app.schemas import QueryProfile
from app.services.source_classifier import classify_source
from app.utils.text import normalize_text, tokenize
from app.utils.url import get_domain


def _load_domain_boosts() -> dict[str, float]:
    from pathlib import Path

    import yaml

    rules_dir = Path(__file__).parent.parent / "rules"
    try:
        with open(rules_dir / "domain_boost.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        boosts = data.get("boosts", {})
        penalties = data.get("penalties", {})
        result = dict(boosts)
        for k, v in penalties.items():
            result[k] = v
        return result
    except Exception:
        return {}


_DOMAIN_BOOSTS = _load_domain_boosts()


def _domain_authority_score(domain: str, profile: str) -> float:
    boost = 0.0
    for d, v in _DOMAIN_BOOSTS.items():
        if domain.endswith(d) or domain == d:
            boost = v
            break

    # Profile-specific adjustments
    if profile == QueryProfile.TECH:
        if any(d in domain for d in ("csdn.net", "zhihu.com", "jianshu.com")):
            boost -= 0.25
        if any(d in domain for d in ("baidu.com", "360.cn", "so.com")):
            boost -= 0.15
        if any(d in domain for d in (
            "github.com",
            "stackoverflow.com",
            "docs.python.org",
            "developer.mozilla.org",
            "learn.microsoft.com",
            "python.langchain.com",
            "langchain-ai.github.io",
        )):
            boost += 0.2

    if profile == QueryProfile.GENERAL_CN:
        if "bing.com" in domain:
            boost += 0.1
        if any(d in domain for d in ("360.cn", "so.com", "sogou.com")):
            boost += 0.05
        if "baidu.com" in domain:
            boost -= 0.05

    # Normalize to 0-1
    score = 0.5 + boost
    return max(0.0, min(1.0, score))


def _keyword_match_score(query: str, title: str, snippet: str) -> float:
    query_tokens = tokenize(query)
    title_tokens = tokenize(title)
    snippet_tokens = tokenize(snippet)

    if not query_tokens:
        return 0.5

    title_overlap = len(query_tokens & title_tokens) / len(query_tokens)
    snippet_overlap = len(query_tokens & snippet_tokens) / len(query_tokens)

    return min(1.0, title_overlap * 0.7 + snippet_overlap * 0.3)


def _freshness_score(item: dict) -> float:
    published = item.get("publishedDate") or item.get("published_date")
    if not published:
        return 0.5
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_old = (now - dt).days
        if days_old < 0:
            return 0.5
        if days_old < 7:
            return 1.0
        if days_old < 30:
            return 0.8
        if days_old < 90:
            return 0.6
        if days_old < 365:
            return 0.4
        return 0.2
    except Exception:
        return 0.5


def _searxng_score_norm(item: dict) -> float:
    score = item.get("score", 0)
    if isinstance(score, (int, float)):
        # Normalize: assume max ~10 for most engines
        return min(1.0, max(0.0, score / 10.0))
    # Fallback: rank-based
    position = item.get("position", 50)
    return max(0.0, 1.0 - position / 50.0)


def _engine_consensus_score(item: dict, total_engines: int) -> float:
    engines = set(item.get("engines", []))
    if not engines:
        return 0.0
    return min(1.0, len(engines) / max(1, total_engines))


def rank_results(raw_results: list[dict], query: str, profile: str) -> list[dict]:
    cfg = gateway_config.scoring
    weights = cfg.weights
    source_scores = cfg.source_type_scores

    # First pass: classify and compute scores
    scored = []
    for item in raw_results:
        url = item.get("url", "")
        title = item.get("title", "")
        snippet = item.get("content", "") or item.get("snippet", "")
        domain = get_domain(url)
        source_type = classify_source(url, title, snippet)

        s_searxng = _searxng_score_norm(item)
        s_domain = _domain_authority_score(domain, profile)
        s_keyword = _keyword_match_score(query, title, snippet)
        s_source = source_scores.get(source_type, source_scores.get("unknown", 0.4))
        s_consensus = _engine_consensus_score(item, len({r.get("engine", "") for r in raw_results}))
        s_freshness = _freshness_score(item)

        # Profile-specific source type boost
        penalty = 0.0
        if profile == QueryProfile.TECH:
            if source_type == "official_doc":
                s_source += 0.2
            elif source_type == "github_repo":
                s_source += 0.15
            elif source_type == "github_issue":
                s_source += 0.1
            elif "stackoverflow.com" in domain:
                s_source += 0.1
            elif source_type in ("content_farm", "seo_spam"):
                penalty = 0.3

        s_source = max(0.0, min(1.0, s_source))

        final_score = (
            weights.searxng_score * s_searxng
            + weights.domain_authority * s_domain
            + weights.keyword_match * s_keyword
            + weights.source_type * s_source
            + weights.engine_consensus * s_consensus
            + weights.freshness * s_freshness
            - penalty
        )

        item["_final_score"] = final_score
        item["_source_type"] = source_type
        item["_breakdown"] = {
            "searxng_score": round(s_searxng, 4),
            "domain_authority": round(s_domain, 4),
            "keyword_match": round(s_keyword, 4),
            "source_type": round(s_source, 4),
            "engine_consensus": round(s_consensus, 4),
            "freshness": round(s_freshness, 4),
            "penalty": round(penalty, 4),
        }
        scored.append(item)

    scored.sort(key=lambda x: x["_final_score"], reverse=True)
    return scored
