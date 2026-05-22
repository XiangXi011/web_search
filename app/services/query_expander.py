from __future__ import annotations

import re

from app.utils.text import extract_error_phrases


def _extract_github_url(query: str) -> str | None:
    m = re.search(r"https?://github\.com/([^/\s]+)/([^/\s]+)", query)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return None


def expand(query: str, profile: str) -> list[str]:
    variants = [query]

    if profile == "tech":
        variants = _expand_tech(query)
    elif profile == "research":
        variants = _expand_research(query)
    elif profile == "fresh_cn":
        variants = [query]

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
