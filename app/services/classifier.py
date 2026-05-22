from __future__ import annotations

import re
from pathlib import Path

import yaml

from app.schemas import QueryProfile
from app.utils.text import contains_any


_RULES_PATH = Path(__file__).parent.parent / "rules" / "tech_keywords.yml"


def _load_keywords() -> list[str]:
    try:
        with open(_RULES_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("tech_keywords", [])
    except Exception:
        return []


_TECH_KEYWORDS = _load_keywords()

_WECHAT_KEYWORDS = [
    "公众号", "微信文章", "爆文", "私域", "种草", "小红书文案",
    "行业号", "公众号文章", "微信推文",
]

_RESEARCH_KEYWORDS = [
    "论文", "paper", "arxiv", "benchmark", "evaluation", "评测",
    "研究", "survey", "dataset", "sota", "leaderboard",
]

_FRESH_KEYWORDS = [
    "最新", "今天", "新闻", "价格", "政策", "发布", "公告",
    "current", "latest", "2026", "今年", "最近",
]


def classify(query: str) -> QueryProfile:
    lowered = query.lower()

    if contains_any(lowered, _TECH_KEYWORDS):
        return QueryProfile.TECH

    if contains_any(lowered, _WECHAT_KEYWORDS):
        return QueryProfile.WECHAT

    if contains_any(lowered, _RESEARCH_KEYWORDS):
        return QueryProfile.RESEARCH

    if contains_any(lowered, _FRESH_KEYWORDS):
        return QueryProfile.FRESH_CN

    return QueryProfile.GENERAL_CN
