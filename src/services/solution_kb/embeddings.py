"""Embeddings for semantic retrieval.

Primary: OpenAI embeddings (if OPENAI_API_KEY available).
Fallback: deterministic hashing embedding (no external deps) so the system still works
without network/keys (not truly semantic, but keeps vector pipeline functional).
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import List, Optional


class EmbeddingError(RuntimeError):
    pass


@dataclass(frozen=True)
class EmbeddingResult:
    vector: List[float]
    model: str


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


class Embedder:
    def embed(self, text: str) -> EmbeddingResult:  # pragma: no cover
        raise NotImplementedError


class OpenAIEmbedder(Embedder):
    def __init__(self, *, model: str = "text-embedding-3-small"):
        import os
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EmbeddingError("OPENAI_API_KEY not set.")
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def embed(self, text: str) -> EmbeddingResult:
        text = (text or "").strip()
        if not text:
            return EmbeddingResult(vector=[], model=self._model)
        resp = self._client.embeddings.create(model=self._model, input=text)
        vec = list(resp.data[0].embedding)
        return EmbeddingResult(vector=vec, model=self._model)


class HashEmbedder(Embedder):
    """Deterministic hash embedding. Not semantic, but fast/no deps."""

    def __init__(self, *, dim: int = 256):
        self._dim = dim
        self._model = f"hash-{dim}"

    def embed(self, text: str) -> EmbeddingResult:
        text = (text or "").strip()
        if not text:
            return EmbeddingResult(vector=[0.0] * self._dim, model=self._model)
        vec = [0.0] * self._dim
        # Tokenize by simple whitespace + keep Chinese as is
        tokens = []
        cur = []
        for ch in text:
            if ch.isalnum() or ("\u4e00" <= ch <= "\u9fff"):
                cur.append(ch)
            else:
                if cur:
                    tokens.append("".join(cur))
                    cur = []
        if cur:
            tokens.append("".join(cur))
        if not tokens:
            tokens = [text]

        for tok in tokens:
            h = hashlib.sha256(tok.encode("utf-8")).digest()
            idx = int.from_bytes(h[:2], "big") % self._dim
            sign = 1.0 if (h[2] % 2 == 0) else -1.0
            vec[idx] += sign

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return EmbeddingResult(vector=vec, model=self._model)


def default_embedder() -> Embedder:
    try:
        return OpenAIEmbedder()
    except Exception:
        return HashEmbedder()

