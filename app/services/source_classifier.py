from __future__ import annotations

import re
from pathlib import Path

import yaml

from app.schemas import QueryProfile
from app.utils.url import get_domain, is_github_issue_or_pr, is_github_repo

_RULES_DIR = Path(__file__).parent.parent / "rules"


def _load_yaml(name: str) -> dict:
    try:
        with open(_RULES_DIR / name, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


_OFFICIAL_PATTERNS: list[str] = []
_PACKAGE_REGISTRIES: list[str] = []
_ACADEMIC_DOMAINS: list[str] = []
_GOVERNMENT_DOMAINS: list[str] = []
_CONTENT_FARMS: set[str] = set()
_SEO_SPAM_INDICATORS: list[str] = []


def _load_rules() -> None:
    global _OFFICIAL_PATTERNS, _PACKAGE_REGISTRIES, _ACADEMIC_DOMAINS
    global _GOVERNMENT_DOMAINS, _CONTENT_FARMS, _SEO_SPAM_INDICATORS

    official = _load_yaml("official_domains.yml")
    _OFFICIAL_PATTERNS = official.get("official_doc_patterns", [])
    _PACKAGE_REGISTRIES = official.get("package_registries", [])
    _ACADEMIC_DOMAINS = official.get("academic_domains", [])
    _GOVERNMENT_DOMAINS = official.get("government_domains", [])

    cf = _load_yaml("content_farm.yml")
    _CONTENT_FARMS = set(cf.get("content_farms", []))
    _SEO_SPAM_INDICATORS = cf.get("seo_spam_indicators", [])


_load_rules()


def classify_source(url: str, title: str = "", snippet: str = "") -> str:
    domain = get_domain(url)
    text = f"{title} {snippet}".lower()

    # SEO spam
    for indicator in _SEO_SPAM_INDICATORS:
        if indicator in text:
            return "seo_spam"

    # Content farm
    if any(domain.endswith(d) or domain == d for d in _CONTENT_FARMS):
        return "content_farm"

    # GitHub
    if is_github_repo(url):
        return "github_repo"
    if is_github_issue_or_pr(url):
        return "github_issue"

    # Package registry (check full URL since patterns may include paths)
    for pattern in _PACKAGE_REGISTRIES:
        if re.search(pattern, url):
            return "package_registry"

    # Academic
    for pattern in _ACADEMIC_DOMAINS:
        if re.search(pattern, domain):
            return "academic"

    # Government (check domain with optional leading dot for bare TLDs)
    for pattern in _GOVERNMENT_DOMAINS:
        if re.search(pattern, domain) or re.search(pattern, f".{domain}"):
            return "government"

    # Official doc
    for pattern in _OFFICIAL_PATTERNS:
        if re.search(pattern, domain):
            return "official_doc"

    # WeChat
    if "weixin.qq.com" in domain or "mp.weixin.qq.com" in url:
        return "wechat_article"

    # Vendor blog / community heuristics
    if re.search(r"blog\.", domain) or "medium.com" in domain:
        return "vendor_blog"

    if re.search(r"(stackoverflow|reddit|quora|v2ex|juejin|segmentfault)", domain):
        return "community"

    if re.search(r"(news|techcrunch|theverge|36kr|pingwest|solidot)", domain):
        return "media"

    return "unknown"


def is_content_farm(url: str) -> bool:
    domain = get_domain(url)
    return any(domain.endswith(d) or domain == d for d in _CONTENT_FARMS)
