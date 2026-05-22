from __future__ import annotations

import pytest

from app.services.cache import _cache_key, _get_ttl


class TestCacheKey:
    def test_key_deterministic(self):
        """Same inputs produce the same key."""
        key1 = _cache_key("test query", "tech", "all", "auto", 10)
        key2 = _cache_key("test query", "tech", "all", "auto", 10)
        assert key1 == key2

    def test_key_differs_by_query(self):
        key1 = _cache_key("query A", "tech", "all", "auto", 10)
        key2 = _cache_key("query B", "tech", "all", "auto", 10)
        assert key1 != key2

    def test_key_differs_by_profile(self):
        key1 = _cache_key("query", "tech", "all", "auto", 10)
        key2 = _cache_key("query", "research", "all", "auto", 10)
        assert key1 != key2

    def test_key_uses_prefix(self):
        key = _cache_key("q", "tech", "all", "auto", 10)
        assert key.startswith("search_cache:")


class TestCacheTTL:
    def test_tech_ttl(self):
        ttl = _get_ttl("tech")
        assert ttl == 6 * 3600

    def test_research_ttl(self):
        ttl = _get_ttl("research")
        assert ttl == 24 * 3600

    def test_fresh_cn_ttl(self):
        ttl = _get_ttl("fresh_cn")
        assert ttl == 10 * 60

    def test_default_ttl(self):
        ttl = _get_ttl("general_cn")
        assert ttl == 3600
