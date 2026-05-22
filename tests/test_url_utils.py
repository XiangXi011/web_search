import pytest

from app.utils.url import (
    clean_url,
    extract_github_info,
    get_canonical_url,
    get_domain,
    is_github_issue_or_pr,
    is_github_repo,
)


class TestCleanUrl:
    def test_removes_utm_params(self):
        url = "https://example.com/page?utm_source=google&utm_medium=cpc&id=123"
        cleaned = clean_url(url)
        assert "utm_source" not in cleaned
        assert "utm_medium" not in cleaned
        assert "id=123" in cleaned

    def test_removes_fbclid(self):
        url = "https://example.com/page?fbclid=abc123&key=val"
        cleaned = clean_url(url)
        assert "fbclid" not in cleaned
        assert "key=val" in cleaned

    def test_removes_spm(self):
        url = "https://example.com/page?spm=abc&from=source"
        cleaned = clean_url(url)
        assert "spm" not in cleaned
        assert "from" not in cleaned

    def test_no_params_unchanged(self):
        url = "https://example.com/page"
        assert clean_url(url) == url


class TestGetDomain:
    def test_strips_www(self):
        assert get_domain("https://www.example.com/path") == "example.com"

    def test_lowercase(self):
        assert get_domain("https://Example.COM/path") == "example.com"

    def test_no_www(self):
        assert get_domain("https://github.com/user/repo") == "github.com"


class TestGetCanonicalUrl:
    def test_strips_tracking_and_trailing_slash(self):
        url = "https://www.example.com/page/?utm_source=test&id=1"
        canonical = get_canonical_url(url)
        assert "utm_source" not in canonical
        assert canonical.endswith("/page") or canonical.endswith("/page?")


class TestExtractGithubInfo:
    def test_extracts_owner_repo(self):
        owner, repo = extract_github_info("https://github.com/langchain-ai/langgraph")
        assert owner == "langchain-ai"
        assert repo == "langgraph"

    def test_non_github_returns_none(self):
        owner, repo = extract_github_info("https://example.com/page")
        assert owner is None
        assert repo is None


class TestIsGithubRepo:
    def test_github_repo_url(self):
        assert is_github_repo("https://github.com/langchain-ai/langgraph") is True

    def test_github_issue_url(self):
        assert is_github_repo("https://github.com/langchain-ai/langgraph/issues/123") is False


class TestIsGithubIssueOrPr:
    def test_issue(self):
        assert is_github_issue_or_pr("https://github.com/owner/repo/issues/42") is True

    def test_pr(self):
        assert is_github_issue_or_pr("https://github.com/owner/repo/pull/99") is True

    def test_repo_main_page(self):
        assert is_github_issue_or_pr("https://github.com/owner/repo") is False
