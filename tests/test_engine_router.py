import pytest

from app.services.engine_router import (
    get_engines,
    get_profile_language,
    get_profile_time_range,
    get_profile_timeout,
)


class TestGetEngines:
    def test_tech_engines(self):
        engines = get_engines("tech")
        assert "github" in engines
        assert "stackoverflow" in engines
        assert "bing" in engines
        # Tech profile must NOT include baidu/360/sogou
        assert "baidu" not in engines
        assert "360search" not in engines
        assert "sogou" not in engines

    def test_general_cn_engines(self):
        engines = get_engines("general_cn")
        assert "bing" in engines
        assert "baidu" in engines
        assert "360search" in engines
        assert "sogou" in engines

    def test_wechat_engines(self):
        engines = get_engines("wechat")
        assert "sogou wechat" in engines
        assert "bing" in engines

    def test_research_engines(self):
        engines = get_engines("research")
        assert "arxiv" in engines
        assert "bing" in engines

    def test_fresh_cn_engines(self):
        engines = get_engines("fresh_cn")
        assert "bing" in engines
        assert "baidu" in engines

    def test_unknown_profile_falls_back_to_general_cn(self):
        engines = get_engines("nonexistent")
        assert engines == get_engines("general_cn")


class TestGetProfileTimeout:
    def test_tech_timeout(self):
        assert get_profile_timeout("tech") == 3.5

    def test_wechat_timeout(self):
        assert get_profile_timeout("wechat") == 4.0


class TestGetProfileLanguage:
    def test_tech_language_all(self):
        assert get_profile_language("tech") == "all"

    def test_general_cn_language(self):
        assert get_profile_language("general_cn") == "zh-CN"


class TestGetProfileTimeRange:
    def test_fresh_cn_has_time_range(self):
        assert get_profile_time_range("fresh_cn") == "month"

    def test_tech_no_time_range(self):
        assert get_profile_time_range("tech") is None
