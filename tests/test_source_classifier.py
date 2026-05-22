import pytest

from app.services.source_classifier import classify_source, is_content_farm


class TestClassifySource:
    def test_official_doc_docs_subdomain(self):
        assert classify_source("https://docs.python.org/3/library/json.html") == "official_doc"

    def test_official_doc_readthedocs(self):
        assert classify_source("https://mylib.readthedocs.io/en/latest/") == "official_doc"

    def test_official_doc_github_io(self):
        assert classify_source("https://langchain-ai.github.io/langgraph/") == "official_doc"

    def test_github_repo(self):
        assert classify_source("https://github.com/langchain-ai/langgraph") == "github_repo"

    def test_github_issue(self):
        assert classify_source("https://github.com/langchain-ai/langgraph/issues/123") == "github_issue"

    def test_github_pr(self):
        assert classify_source("https://github.com/langchain-ai/langgraph/pull/456") == "github_issue"

    def test_package_registry_pypi(self):
        assert classify_source("https://pypi.org/project/fastapi/") == "package_registry"

    def test_package_registry_npm(self):
        assert classify_source("https://www.npmjs.com/package/express") == "package_registry"

    def test_academic_arxiv(self):
        assert classify_source("https://arxiv.org/abs/2301.00001") == "academic"

    def test_academic_crossref(self):
        assert classify_source("https://crossref.org/doi/10.1234/test") == "academic"

    def test_government_domain(self):
        assert classify_source("https://www.gov.cn/policy/2026") == "government"

    def test_content_farm_csdn(self):
        assert classify_source("https://blog.csdn.net/user/article/12345") == "content_farm"

    def test_content_farm_zhihu(self):
        assert classify_source("https://zhuanlan.zhihu.com/p/12345") == "content_farm"

    def test_seo_spam_indicator(self):
        result = classify_source(
            "https://example.com/page",
            title="免费破解版下载 激活码 序列号",
            snippet="",
        )
        assert result == "seo_spam"

    def test_wechat_article(self):
        assert classify_source("https://mp.weixin.qq.com/s/abcdefg") == "wechat_article"

    def test_community_stackoverflow(self):
        assert classify_source("https://stackoverflow.com/questions/12345") == "community"

    def test_unknown(self):
        assert classify_source("https://random-site.com/post/1") == "unknown"


class TestIsContentFarm:
    def test_csdn_is_content_farm(self):
        assert is_content_farm("https://blog.csdn.net/user/article/123") is True

    def test_github_is_not_content_farm(self):
        assert is_content_farm("https://github.com/user/repo") is False

    def test_subdomain_content_farm(self):
        assert is_content_farm("https://www.jianshu.com/p/abc123") is True
