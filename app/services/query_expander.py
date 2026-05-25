from __future__ import annotations

import re

from app.utils.text import extract_error_phrases


def _extract_github_url(query: str) -> str | None:
    m = re.search(r"https?://github\.com/([^/\s]+)/([^/\s]+)", query)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return None


_CN_STOPWORDS = frozenset({
    "的", "了", "吗", "呢", "吧", "啊", "呀", "哦", "哈",
    "是", "在", "有", "不", "也", "和", "与", "或", "及",
    "什么", "怎么", "如何", "哪个", "哪些", "为什么", "哪",
    "可以", "能", "会", "要", "想", "需要",
    "我", "你", "他", "她", "它", "们", "这", "那",
})

_CN_SITE_VARIANTS = [
    "site:gov.cn",
    "site:zhihu.com",
    "site:juejin.cn",
]


def expand(query: str, profile: str) -> list[str]:
    variants = [query]

    if profile == "tech":
        variants = _expand_tech(query)
    elif profile == "research":
        variants = _expand_research(query)
    elif profile in ("general_cn", "fresh_cn", "wechat"):
        variants = _expand_cn(query, profile)

    return variants[:4]


def _expand_tech(query: str) -> list[str]:
    variants = [query]

    # Error / traceback expansion
    if re.search(r"(traceback|exception|error:|failed|cannot import|module not found)", query, re.I):
        phrases = extract_error_phrases(query)
        for phrase in phrases:
            variants.append(f'"{phrase}"')
            variants.append(f'site:github.com "{phrase}"')
            variants.append(f'site:stackoverflow.com "{phrase}"')
        return list(dict.fromkeys(variants))[:4]

    # GitHub URL expansion
    gh = _extract_github_url(query)
    if gh:
        repo_name = gh.split("/")[1]
        owner = gh.split("/")[0]
        variants = [
            f"{repo_name} {owner} GitHub",
            f"site:github.com/{gh} README",
            f"site:github.com/{gh} issues",
            f"site:docs.{repo_name}.dev {repo_name}",
        ]
        return variants

    # General tech: add English variant and site queries
    english = query
    # Simple heuristic: if Chinese, also try English keywords
    if re.search(r"[一-鿿]", query):
        english = re.sub(r"[一-鿿]+", "", query).strip()
        if english:
            variants.append(english)

    # Add site queries for major tech sites
    if re.search(r"(langchain|langgraph)", query, re.I):
        variants.append(f"site:langchain-ai.github.io {query}")
        variants.append(f"site:python.langchain.com {query}")

    if re.search(r"(fastapi|redis|docker|kubernetes)", query, re.I):
        variants.append(f"site:docs.{re.search(r'(fastapi|redis|docker|kubernetes)', query, re.I).group(1)}.io {query}")

    return list(dict.fromkeys(variants))[:4]


def _expand_research(query: str) -> list[str]:
    variants = [query]
    if "arxiv" not in query.lower():
        variants.append(f"arxiv {query}")
    if "paper" not in query.lower():
        variants.append(f"{query} paper")
    return list(dict.fromkeys(variants))[:4]


def _expand_cn(query: str, profile: str) -> list[str]:
    variants = [query]

    # Strip stopwords for a cleaner variant
    cleaned = _strip_cn_stopwords(query)
    if cleaned and cleaned != query:
        variants.append(cleaned)

    # English keyword extraction (keep Latin words)
    english = re.sub(r"[一-鿿\s]+", " ", query).strip()
    if english and len(english) > 2:
        variants.append(english)

    # Site-specific variants for wechat
    if profile == "wechat":
        variants.append(f"site:mp.weixin.qq.com {query}")

    return list(dict.fromkeys(variants))[:4]


def _strip_cn_stopwords(query: str) -> str:
    # Remove trailing stopwords/question particles
    text = query
    for _ in range(3):  # strip up to 3 trailing particles
        stripped = False
        for sw in ("的", "了", "吗", "呢", "吧", "啊", "呀", "哦"):
            if text.endswith(sw) and len(text) > 2:
                text = text[:-len(sw)]
                stripped = True
                break
        if not stripped:
            break
    # Remove leading question words
    for prefix in ("怎么", "如何", "什么是", "什么是", "请问", "求教"):
        if text.startswith(prefix) and len(text) > len(prefix) + 1:
            text = text[len(prefix):]
            break
    return text.strip()
