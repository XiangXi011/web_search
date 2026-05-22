import pytest

from app.services.ranker import rank_results


def test_rank_official_doc_higher():
    raw = [
        {"url": "https://docs.python.org/3/tutorial", "title": "Python Tutorial", "content": "Official tutorial", "score": 5, "engine": "bing", "engines": ["bing"]},
        {"url": "https://csdn.net/article/123", "title": "Python Tutorial", "content": "CSDN repost", "score": 6, "engine": "baidu", "engines": ["baidu"]},
    ]
    ranked = rank_results(raw, "Python tutorial", "tech")
    assert ranked[0]["url"] == "https://docs.python.org/3/tutorial"


def test_rank_keyword_match():
    raw = [
        {"url": "https://fastapi.tiangolo.com/tutorial", "title": "FastAPI Tutorial", "content": "Learn FastAPI", "score": 5, "engine": "bing", "engines": ["bing"]},
        {"url": "https://example.com/other", "title": "Other thing", "content": "Random content", "score": 5, "engine": "bing", "engines": ["bing"]},
    ]
    ranked = rank_results(raw, "FastAPI tutorial", "tech")
    assert ranked[0]["url"] == "https://fastapi.tiangolo.com/tutorial"


def test_rank_github_repo_boost():
    raw = [
        {"url": "https://github.com/tiangolo/fastapi", "title": "FastAPI", "content": "Repo", "score": 5, "engine": "github", "engines": ["github"]},
        {"url": "https://example.com/fastapi", "title": "FastAPI", "content": "Blog", "score": 5, "engine": "bing", "engines": ["bing"]},
    ]
    ranked = rank_results(raw, "FastAPI", "tech")
    assert ranked[0]["url"] == "https://github.com/tiangolo/fastapi"
