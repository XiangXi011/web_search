import pytest

from app.services.dedup import deduplicate_results


def test_dedup_by_canonical():
    raw = [
        {"url": "https://example.com/page?utm_source=x", "title": "Page 1", "content": "Snippet 1", "engine": "bing"},
        {"url": "https://example.com/page?utm_medium=y", "title": "Page 1 dup", "content": "Snippet dup", "engine": "google"},
    ]
    result = deduplicate_results(raw)
    assert len(result) == 1


def test_dedup_domain_limit():
    raw = [
        {"url": "https://example.com/a", "title": f"A{i}", "content": f"S{i}", "engine": "bing"}
        for i in range(5)
    ]
    result = deduplicate_results(raw)
    assert len(result) <= 2


def test_dedup_github_limit():
    raw = [
        {"url": f"https://github.com/owner/repo{i}", "title": f"Repo{i}", "content": f"S{i}", "engine": "github"}
        for i in range(6)
    ]
    result = deduplicate_results(raw)
    assert len(result) <= 4
