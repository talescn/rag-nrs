"""Gera os trechos e calcula seus embeddings. Uso: python -m rag_nrs.index"""
import numpy as np
from sentence_transformers import SentenceTransformer

from .config import EMBEDDING_MODEL, EMBEDDINGS_PATH
from .ingest import build_chunks, save_chunks

# Os modelos E5 foram treinados com estes prefixos; sem eles a qualidade da busca cai.
_E5 = "e5" in EMBEDDING_MODEL.lower()
PASSAGE_PREFIX = "passage: " if _E5 else ""
QUERY_PREFIX = "query: " if _E5 else ""


def load_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


def embed_passages(model: SentenceTransformer, textos: list[str]) -> np.ndarray:
    vetores = model.encode([PASSAGE_PREFIX + t for t in textos], batch_size=32,
                           normalize_embeddings=True, show_progress_bar=True)
    return vetores.astype(np.float32)


def embed_query(model: SentenceTransformer, pergunta: str) -> np.ndarray:
    return model.encode(QUERY_PREFIX + pergunta, normalize_embeddings=True).astype(np.float32)


def build_index() -> None:
    chunks = build_chunks()
    save_chunks(chunks)
    vetores = embed_passages(load_model(), [c.contexto() for c in chunks])
    np.save(EMBEDDINGS_PATH, vetores)
    print(f"embeddings {vetores.shape} salvos em {EMBEDDINGS_PATH}")


if __name__ == "__main__":
    build_index()
