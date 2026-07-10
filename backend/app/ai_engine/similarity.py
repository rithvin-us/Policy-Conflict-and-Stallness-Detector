"""Semantic similarity with graceful degradation.

Default path is pure-Python lexical similarity (token Jaccard + character
sequence ratio) so it runs offline and deterministically. If
``sentence-transformers`` is installed *and* enabled via
``POLICYGUARDIAN_USE_EMBEDDINGS=1``, an embedding-cosine signal is blended in to
improve near-duplicate / near-conflict recall — but it can only *raise* a
similarity score, never suppress a rule-based conflict, preserving precision.
"""
from __future__ import annotations

import difflib
import os
import re
from functools import lru_cache

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "at", "by",
    "with", "is", "are", "be", "been", "must", "shall", "should", "may", "not",
    "all", "any", "this", "that", "their", "its", "as", "from", "will",
}


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOP and len(t) > 2}


def jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def sequence_ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def lexical_similarity(a: str, b: str) -> float:
    """Blend token overlap and character-sequence similarity (0..1)."""
    return round(0.65 * jaccard(a, b) + 0.35 * sequence_ratio(a, b), 4)


# --- Optional embedding upgrade -------------------------------------------

def _embeddings_enabled() -> bool:
    return os.getenv("POLICYGUARDIAN_USE_EMBEDDINGS", "0") == "1"


@lru_cache(maxsize=1)
def _load_model():  # pragma: no cover - exercised only when deps installed
    from sentence_transformers import SentenceTransformer  # type: ignore

    return SentenceTransformer(
        os.getenv("POLICYGUARDIAN_EMBED_MODEL", "all-MiniLM-L6-v2")
    )


def _embedding_similarity(a: str, b: str) -> float:  # pragma: no cover
    model = _load_model()
    va, vb = model.encode([a, b])
    dot = float(sum(x * y for x, y in zip(va, vb)))
    na = float(sum(x * x for x in va)) ** 0.5
    nb = float(sum(y * y for y in vb)) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return max(0.0, dot / (na * nb))


def semantic_similarity(a: str, b: str) -> float:
    """Public similarity signal used by conflict/redundancy detection."""
    base = lexical_similarity(a, b)
    if _embeddings_enabled():
        try:  # pragma: no cover - depends on optional install
            emb = _embedding_similarity(a, b)
            return round(max(base, 0.5 * base + 0.5 * emb), 4)
        except Exception:
            return base
    return base


def backend_name() -> str:
    return "embeddings+lexical" if _embeddings_enabled() else "lexical"
