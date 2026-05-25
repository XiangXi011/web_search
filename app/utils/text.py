from __future__ import annotations

import math
import re

import jieba

_CJK_RE = re.compile(r"[一-鿿]+")
_LATIN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set[str]:
    lowered = text.lower()
    tokens: set[str] = set()

    # Split into CJK and non-CJK segments
    pos = 0
    for m in re.finditer(r"[一-鿿]+", lowered):
        # Latin tokens before this CJK segment
        for w in _LATIN_RE.findall(lowered[pos:m.start()]):
            tokens.add(w)
        # CJK: jieba search-mode segmentation (granular) + original substring
        cjk = m.group()
        tokens.add(cjk)
        for w in jieba.cut_for_search(cjk):
            if len(w) > 1:
                tokens.add(w)
        pos = m.end()
    # Trailing Latin tokens
    for w in _LATIN_RE.findall(lowered[pos:]):
        tokens.add(w)

    return tokens


def jaccard_similarity(a: str, b: str) -> float:
    set_a = tokenize(a)
    set_b = tokenize(b)
    if not set_a and not set_b:
        return 1.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    if union == 0:
        return 0.0
    return inter / union


def cosine_similarity(a: str, b: str) -> float:
    set_a = tokenize(a)
    set_b = tokenize(b)
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    return inter / (math.sqrt(len(set_a)) * math.sqrt(len(set_b)))


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w一-鿿]", " ", text)
    return text.strip()


def contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    for kw in keywords:
        if kw.lower() in lowered:
            return True
    return False


def extract_error_phrases(text: str) -> list[str]:
    lines = text.splitlines()
    phrases = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.search(r"(Error|Exception|Traceback|failed|cannot import|module not found)", line, re.I):
            cleaned = re.sub(r'^\s*File\s+".*?",\s*line\s*\d+\s*,\s*', "", line)
            cleaned = re.sub(r"^\s*Traceback\s*\(.*\):\s*", "", cleaned)
            if len(cleaned) > 10 and len(cleaned) < 200:
                phrases.append(cleaned)
    if not phrases:
        for line in lines:
            if "Error:" in line or "Exception" in line:
                phrases.append(line.strip())
    return phrases[:3]
