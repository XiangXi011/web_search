"""
Integration tests — require running SearXNG + Redis.

Run with: pytest tests/ -v -m integration
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

pytestmark = pytest.mark.integration


def _search(query: str, profile: str = "auto") -> dict:
    resp = client.post("/v1/search", json={"query": query, "profile": profile})
    assert resp.status_code == 200
    return resp.json()


# ---- Tech queries ----

class TestTechQueries:
    @pytest.mark.parametrize("query", [
        "LangGraph checkpointer error",
        "vLLM qwen3 tool call parser 报错",
        "FastAPI redis connection pool timeout",
        "Docker Windows WSL2 install failed",
        "github.com/firecrawl/firecrawl",
        "pip install langchain 报错 依赖冲突",
    ])
    def test_tech_query_returns_results(self, query):
        data = _search(query)
        assert data["profile"] == "tech"
        assert len(data["results"]) > 0 or data["meta"]["partial"] is True
        assert len(data["meta"]["engines_used"]) > 0

    def test_tech_query_no_content_farm_in_top3(self):
        data = _search("LangGraph checkpointer error")
        top3_domains = [r["domain"] for r in data["results"][:3]]
        content_farms = {"csdn.net", "zhihu.com", "jianshu.com"}
        assert not any(d in content_farms for d in top3_domains)


# ---- General CN queries ----

class TestGeneralCNQueries:
    @pytest.mark.parametrize("query", [
        "广州 AI 公司 2026",
        "儿童牙膏 国家标准",
        "飞书知识库 RAG",
        "上海天气",
        "小米汽车最新消息",
        "Python 入门教程",
    ])
    def test_general_cn_returns_results(self, query):
        data = _search(query)
        assert data["profile"] == "general_cn"
        assert len(data["results"]) > 0 or data["meta"]["partial"] is True
        assert len(data["meta"]["engines_used"]) > 0


# ---- Fresh CN queries ----

class TestFreshCNQueries:
    @pytest.mark.parametrize("query", [
        "OpenAI 最新模型 2026",
        "中国 AI 政策 2026",
        "特斯拉 今天 新闻",
        "美联储 利率 最新",
        "英伟达 发布 2026",
        "微信 最新版本",
    ])
    def test_fresh_cn_returns_results(self, query):
        data = _search(query)
        assert data["profile"] == "fresh_cn"
        assert len(data["results"]) > 0 or data["meta"]["partial"] is True


# ---- Research queries ----

class TestResearchQueries:
    @pytest.mark.parametrize("query", [
        "LLM agent benchmark arxiv",
        "RAG evaluation metrics paper",
        "transformer attention survey",
        "reinforcement learning from human feedback",
        "多模态大模型 评测 2026",
        "graph neural network drug discovery",
    ])
    def test_research_returns_results(self, query):
        data = _search(query)
        assert data["profile"] == "research"
        assert len(data["results"]) > 0 or data["meta"]["partial"] is True


# ---- WeChat queries ----

class TestWeChatQueries:
    @pytest.mark.parametrize("query", [
        "AI 转型 公众号文章",
        "消费品行业种草案例",
        "私域流量 运营方法",
        "小红书文案 技巧",
        "微信推文 写作模板",
        "行业号 对标分析",
    ])
    def test_wechat_returns_results(self, query):
        data = _search(query)
        assert data["profile"] == "wechat"
        assert len(data["results"]) > 0 or data["meta"]["partial"] is True


# ---- Response structure verification ----

class TestResponseStructure:
    def test_search_response_has_all_fields(self):
        data = _search("FastAPI tutorial", profile="tech")
        # Top-level
        assert "query" in data
        assert "profile" in data
        assert "query_variants" in data
        assert "results" in data
        assert "meta" in data
        assert "warnings" in data
        # Meta
        meta = data["meta"]
        assert "total_results" in meta
        assert "latency_ms" in meta
        assert "cache_hit" in meta
        assert "partial" in meta
        assert "engines_used" in meta
        assert "engines_skipped" in meta
        assert "engines_failed" in meta
        # Result item
        if data["results"]:
            r = data["results"][0]
            assert "rank" in r
            assert "title" in r
            assert "url" in r
            assert "snippet" in r
            assert "domain" in r
            assert "source_type" in r
            assert "confidence" in r
            assert "confidence_breakdown" in r
            assert "engines" in r
            assert "why_selected" in r
            # Confidence breakdown
            bd = r["confidence_breakdown"]
            assert "searxng_score" in bd
            assert "domain_authority" in bd
            assert "keyword_match" in bd
            assert "engine_consensus" in bd
            assert "freshness" in bd
            assert "source_type" in bd
            assert "penalty" in bd

    def test_partial_flag_when_engines_fail(self):
        """Even if some engines fail, we should get partial results."""
        data = _search("LangGraph error", profile="tech")
        # If any engine failed, partial should be True (if we have results)
        if data["meta"]["engines_failed"] and data["results"]:
            assert data["meta"]["partial"] is True
