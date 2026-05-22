import pytest

from app.utils.text import (
    contains_any,
    cosine_similarity,
    extract_error_phrases,
    jaccard_similarity,
    normalize_text,
    tokenize,
)


class TestTokenize:
    def test_english(self):
        tokens = tokenize("FastAPI Redis connection error")
        assert "fastapi" in tokens
        assert "redis" in tokens
        assert "error" in tokens

    def test_chinese(self):
        tokens = tokenize("连接超时报错")
        assert "连接超时报错" in tokens or len(tokens) > 0

    def test_mixed(self):
        tokens = tokenize("LangGraph checkpointer 报错")
        assert "langgraph" in tokens
        assert "checkpointer" in tokens


class TestJaccardSimilarity:
    def test_identical(self):
        assert jaccard_similarity("hello world", "hello world") == 1.0

    def test_no_overlap(self):
        assert jaccard_similarity("abc", "xyz") == 0.0

    def test_partial(self):
        sim = jaccard_similarity("hello world", "hello there")
        assert 0.0 < sim < 1.0


class TestCosineSimilarity:
    def test_identical(self):
        assert cosine_similarity("test query", "test query") == pytest.approx(1.0, abs=1e-6)

    def test_no_overlap(self):
        assert cosine_similarity("abc", "xyz") == 0.0


class TestNormalizeText:
    def test_lowercase_and_collapse(self):
        result = normalize_text("  Hello   WORLD  ")
        assert result == "hello world"


class TestContainsAny:
    def test_match_found(self):
        assert contains_any("I love python programming", ["python", "java"]) is True

    def test_no_match(self):
        assert contains_any("hello world", ["python", "java"]) is False

    def test_chinese(self):
        assert contains_any("连接超时报错", ["报错", "超时"]) is True


class TestExtractErrorPhrases:
    def test_traceback(self):
        text = "Traceback (most recent call last):\n  File \"test.py\", line 1\nKeyError: 'config'"
        phrases = extract_error_phrases(text)
        assert len(phrases) > 0

    def test_no_error(self):
        phrases = extract_error_phrases("Everything is working fine")
        assert len(phrases) == 0
