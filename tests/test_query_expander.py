import pytest

from app.services.query_expander import expand


def test_expand_tech_general():
    variants = expand("LangGraph checkpointer 报错", "tech")
    assert len(variants) >= 1
    assert "LangGraph checkpointer 报错" in variants


def test_expand_github_url():
    variants = expand("https://github.com/firecrawl/firecrawl", "tech")
    assert any("site:github.com/firecrawl/firecrawl" in v for v in variants)


def test_expand_error_traceback():
    variants = expand("Traceback: module not found numpy", "tech")
    # Should produce quoted variants for error searches
    assert any('"' in v for v in variants)
    # Should include site-specific variants
    assert any("site:github.com" in v or "site:stackoverflow.com" in v for v in variants)


def test_expand_research():
    variants = expand("RAG evaluation metrics", "research")
    assert any("arxiv" in v for v in variants)


def test_expand_fresh_cn():
    variants = expand("OpenAI 最新模型", "fresh_cn")
    assert variants == ["OpenAI 最新模型"]
