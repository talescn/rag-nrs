"""Caminhos e parâmetros do projeto. Tudo que muda entre execuções vem de variáveis de ambiente (.env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

RAW_DIR = ROOT / "data" / "raw"
INDEX_DIR = ROOT / "data" / "index"
CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"
EMBEDDINGS_PATH = INDEX_DIR / "embeddings.npy"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Tamanho máximo de um trecho, em caracteres. Itens maiores são quebrados em pedaços com sobreposição.
MAX_CHUNK_CHARS = 1500
CHUNK_OVERLAP_CHARS = 200
