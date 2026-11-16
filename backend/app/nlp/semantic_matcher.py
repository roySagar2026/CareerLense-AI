"""Semantic similarity behind a small interface.

The default `TfidfSemanticMatcher` is pure Python (no model download, tiny memory) so the
backend fits serverless limits. It measures wording overlap, which is a *proxy* for
relatedness: a high score never proves the candidate has a skill. A sentence-embedding
implementation can be added behind the same interface (see docs/architecture.md).
"""

from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z][a-z0-9+#.]{1,}")
_STOP = frozenset(
    [
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "will",
        "you",
        "our",
        "are",
        "have",
        "has",
        "your",
        "their",
        "they",
        "who",
        "what",
        "when",
        "into",
        "able",
        "such",
        "other",
        "more",
        "than",
        "also",
        "any",
        "all",
        "can",
        "may",
        "must",
        "should",
        "work",
        "working",
        "team",
        "role",
        "experience",
        "strong",
        "ability",
        "skills",
        "using",
        "use",
        "used",
        "including",
        "related",
        "plus",
        "years",
        "year",
    ]
)


def _stem(token: str) -> str:
    for suffix in ("ations", "ation", "ments", "ment", "ings", "ing", "ies", "ers", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def tokenize(text: str) -> list[str]:
    return [_stem(t) for t in _TOKEN_RE.findall(text.lower()) if t not in _STOP]


class SemanticMatcher(ABC):
    @abstractmethod
    def best_match(self, query: str, candidates: list[str]) -> tuple[int, float]:
        """Return (index of best candidate, similarity 0..1); (-1, 0.0) when no candidates."""


class TfidfSemanticMatcher(SemanticMatcher):
    def best_match(self, query: str, candidates: list[str]) -> tuple[int, float]:
        if not candidates:
            return -1, 0.0
        docs = [tokenize(c) for c in candidates]
        query_tokens = tokenize(query)
        if not query_tokens:
            return -1, 0.0
        n_docs = len(docs) + 1
        df: Counter[str] = Counter()
        for tokens in [query_tokens, *docs]:
            df.update(set(tokens))
        idf = {t: math.log((1 + n_docs) / (1 + c)) + 1.0 for t, c in df.items()}

        def vector(tokens: list[str]) -> dict[str, float]:
            counts = Counter(tokens)
            return {t: (1 + math.log(c)) * idf[t] for t, c in counts.items()}

        def norm(vec: dict[str, float]) -> float:
            return math.sqrt(sum(v * v for v in vec.values())) or 1.0

        qv = vector(query_tokens)
        qn = norm(qv)
        best_index, best_score = -1, 0.0
        for index, tokens in enumerate(docs):
            if not tokens:
                continue
            dv = vector(tokens)
            dot = sum(qv[t] * dv[t] for t in qv.keys() & dv.keys())
            score = dot / (qn * norm(dv))
            if score > best_score:
                best_index, best_score = index, score
        return best_index, round(best_score, 4)


def get_semantic_matcher() -> SemanticMatcher:
    return TfidfSemanticMatcher()
