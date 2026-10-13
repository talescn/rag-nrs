"""Extrai o texto dos PDFs e gera data/index/chunks.jsonl. Uso: python -m rag_nrs.ingest"""
import json
from dataclasses import asdict

import pymupdf

from .chunking import Chunk, chunk_items, parse_items
from .config import CHUNK_OVERLAP_CHARS, CHUNKS_PATH, INDEX_DIR, MAX_CHUNK_CHARS, RAW_DIR
from .sources import SOURCES


def extract_pages(norma: str) -> list[str]:
    with pymupdf.open(RAW_DIR / f"{norma}.pdf") as doc:
        return [page.get_text() for page in doc]


def build_chunks() -> list[Chunk]:
    todos: list[Chunk] = []
    for norma, (titulo, _) in SOURCES.items():
        itens = parse_items(extract_pages(norma), norma)
        chunks = chunk_items(itens, norma, titulo, MAX_CHUNK_CHARS, CHUNK_OVERLAP_CHARS)
        print(f"{norma}: {len(itens)} itens -> {len(chunks)} trechos")
        todos.extend(chunks)
    return todos


def save_chunks(chunks: list[Chunk]) -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
    print(f"{len(chunks)} trechos salvos em {CHUNKS_PATH}")


def load_chunks() -> list[Chunk]:
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        return [Chunk(**json.loads(linha)) for linha in f]


if __name__ == "__main__":
    save_chunks(build_chunks())
