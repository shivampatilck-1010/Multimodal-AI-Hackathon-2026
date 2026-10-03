"""Small deterministic text utilities shared by local providers and the evidence gate."""

from __future__ import annotations

import re
import unicodedata

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

STOPWORDS = frozenset(
    """
    a about above after again against all also am an and any are as at be because been
    before being below between both but by can could did do does doing done down during
    each explain explained explaining few for from further get gets give had has have
    having he her here hers herself him himself his how i if in into is it its itself
    just me mean means more most my myself no nor not now of off on once only or other
    our ours ourselves out over own please same she should so some such tell than that
    the their theirs them themselves then there these they this those through to too
    under until up very was we were what when where which while who whom why will with
    would you your yours yourself yourselves simply simple describe define definition
    sometimes happen happens example
    """.split()
)


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def stem(token: str) -> str:
    """Very light suffix stripping so 'converges'/'converge', 'overshooting'/'overshoot' match."""
    for suffix, min_len in (("ing", 6), ("ies", 5), ("es", 5), ("ed", 5), ("s", 4)):
        if len(token) >= min_len and token.endswith(suffix) and not token.endswith("ss"):
            if suffix == "ies":
                return token[:-3] + "y"
            return token[: -len(suffix)]
    return token


def content_terms(text: str) -> list[str]:
    """Lower-cased, stemmed, stop-word-free tokens (order preserved, duplicates kept)."""
    return [stem(t) for t in _TOKEN_RE.findall(normalize(text)) if t not in STOPWORDS and len(t) > 1]


def term_coverage(query: str, evidence_texts: list[str]) -> float:
    """Fraction of distinct query content terms that appear somewhere in the evidence."""
    q_terms = set(content_terms(query))
    if not q_terms:
        return 0.0
    ev_terms: set[str] = set()
    for text in evidence_texts:
        ev_terms.update(content_terms(text))
    return len(q_terms & ev_terms) / len(q_terms)


def strip_control_chars(text: str) -> str:
    return _CONTROL_RE.sub("", text)


def single_line(text: str | None, max_len: int = 200) -> str:
    """Collapse metadata to one bounded line so it cannot break prompt structure."""
    if not text:
        return ""
    cleaned = " ".join(strip_control_chars(text).split())
    return cleaned[:max_len]


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    return [p for p in parts if p]
