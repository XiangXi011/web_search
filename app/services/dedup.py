from __future__ import annotations

from app.config import gateway_config
from urllib.parse import urlparse

from app.utils.text import cosine_similarity
from app.utils.url import clean_url, get_canonical_url, get_domain


def deduplicate_results(raw_results: list[dict]) -> list[dict]:
    cfg = gateway_config.dedup
    seen_canonicals: set[str] = set()
    seen_domain_paths: set[str] = set()
    domain_counts: dict[str, int] = {}
    final: list[dict] = []

    for item in raw_results:
        url = item.get("url", "")
        if not url:
            continue

        canonical = get_canonical_url(url)
        domain = get_domain(url)
        parsed_path = urlparse(clean_url(url)).path.rstrip("/")
        parsed_domain_path = f"{domain}{parsed_path}"

        # Canonical exact match
        if canonical in seen_canonicals:
            # Merge engines
            _merge_into_existing(final, item, canonical)
            continue

        # Domain + path match
        if parsed_domain_path in seen_domain_paths:
            _merge_into_existing(final, item, canonical)
            continue

        # Title similarity
        title = item.get("title", "")
        if title and _has_similar_title(final, title, cfg.title_similarity_threshold):
            continue

        # Snippet similarity
        snippet = item.get("content", "") or item.get("snippet", "")
        if snippet and _has_similar_snippet(final, snippet, cfg.snippet_similarity_threshold):
            continue

        # Domain limit
        limit = cfg.domain_limits.get(domain, cfg.default_max_per_domain)
        if domain_counts.get(domain, 0) >= limit:
            continue

        seen_canonicals.add(canonical)
        seen_domain_paths.add(parsed_domain_path)
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        final.append(item)

    return final


def _merge_into_existing(final: list[dict], item: dict, canonical: str) -> None:
    engine = item.get("engine", "")
    for existing in final:
        if get_canonical_url(existing.get("url", "")) == canonical:
            existing_engines = set(existing.get("engines", []))
            existing_engines.add(engine)
            existing["engines"] = list(existing_engines)
            return


def _has_similar_title(final: list[dict], title: str, threshold: float) -> bool:
    for existing in final:
        existing_title = existing.get("title", "")
        if existing_title and cosine_similarity(title, existing_title) >= threshold:
            return True
    return False


def _has_similar_snippet(final: list[dict], snippet: str, threshold: float) -> bool:
    for existing in final:
        existing_snippet = existing.get("content", "") or existing.get("snippet", "")
        if existing_snippet and cosine_similarity(snippet, existing_snippet) >= threshold:
            return True
    return False
