from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse, urlunparse


_STRIP_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "spm",
    "from",
    "source",
}


def clean_url(url: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    filtered = {k: v for k, v in qs.items() if k.lower() not in _STRIP_PARAMS}
    query = "&".join(
        f"{k}={v[0]}" if len(v) == 1 else "&".join(f"{k}={iv}" for iv in v)
        for k, v in filtered.items()
    )
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, query, "")
    )


def get_domain(url: str) -> str:
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def get_canonical_url(url: str) -> str:
    cleaned = clean_url(url)
    parsed = urlparse(cleaned)
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    if not path:
        path = "/"
    return f"{parsed.scheme}://{netloc}{path}"


def extract_github_info(url: str) -> tuple[str | None, str | None]:
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)(?:/|$)", url)
    if m:
        return m.group(1), m.group(2)
    return None, None


def is_github_issue_or_pr(url: str) -> bool:
    return bool(re.search(r"github\.com/[^/]+/[^/]+/(issues|pull)/\d+", url))


def is_github_repo(url: str) -> bool:
    owner, repo = extract_github_info(url)
    return owner is not None and repo is not None and not is_github_issue_or_pr(url)
