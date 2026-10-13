"""Busca de trechos: BM25 (palavras), densa (embeddings) e híbrida (Reciprocal Rank Fusion das duas)."""
import re
import unicodedata
from dataclasses import dataclass

import numpy as np
from rank_bm25 import BM25Okapi

from .chunking import Chunk
from .config import EMBEDDINGS_PATH

MODES = ("bm25", "dense", "hybrid")

_STOPWORDS = set("""
a ao aos as com como da das de do dos e ela ele em entre essa esse esta este eu foi ha isso ja la mais mas me
mesmo na nas nao no nos o os ou para pela pelas pelo pelos por qual quais quando que quem se sem ser seu sua
so sobre tambem tem um uma umas uns deve devem pode podem
""".split())


def tokenize(texto: str) -> list[str]:
    """Minúsculas, sem acento, sem stopwords. Mantém números de item (35.2.1) e medidas (2,0) inteiros."""
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return [w for w in re.findall(r"[a-z0-9]+(?:[.,][0-9]+)*", t) if w not in _STOPWORDS]


def rrf(rankings: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion: soma 1/(k + posição) de cada lista. Não depende da escala das notas."""
    notas: dict[int, float] = {}
    for ranking in rankings:
        for pos, idx in enumerate(ranking):
            notas[idx] = notas.get(idx, 0.0) + 1.0 / (k + pos + 1)
    return sorted(notas.items(), key=lambda x: -x[1])


@dataclass
class Hit:
    chunk: Chunk
    score: float


class Retriever:
    def __init__(self, chunks: list[Chunk], embeddings: np.ndarray | None = None, model=None):
        self.chunks = chunks
        self.embeddings = embeddings
        self.model = model
        self.bm25 = BM25Okapi([tokenize(c.contexto()) for c in chunks])

    @classmethod
    def load(cls) -> "Retriever":
        from .index import load_model
        from .ingest import load_chunks
        return cls(load_chunks(), np.load(EMBEDDINGS_PATH), load_model())

    def _bm25(self, pergunta: str, n: int) -> list[tuple[int, float]]:
        notas = self.bm25.get_scores(tokenize(pergunta))
        ordem = np.argsort(-notas)[:n]
        return [(int(i), float(notas[i])) for i in ordem]

    def _dense(self, pergunta: str, n: int) -> list[tuple[int, float]]:
        from .index import embed_query
        notas = self.embeddings @ embed_query(self.model, pergunta)  # vetores normalizados: produto = cosseno
        ordem = np.argsort(-notas)[:n]
        return [(int(i), float(notas[i])) for i in ordem]

    def search(self, pergunta: str, k: int = 5, mode: str = "hybrid", candidatos: int = 50) -> list[Hit]:
        if mode == "bm25":
            ranked = self._bm25(pergunta, k)
        elif mode == "dense":
            ranked = self._dense(pergunta, k)
        elif mode == "hybrid":
            listas = [[i for i, _ in self._bm25(pergunta, candidatos)],
                      [i for i, _ in self._dense(pergunta, candidatos)]]
            ranked = rrf(listas)[:k]
        else:
            raise ValueError(f"modo desconhecido: {mode} (use {', '.join(MODES)})")
        return [Hit(self.chunks[i], s) for i, s in ranked]
