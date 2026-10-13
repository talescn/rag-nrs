"""Baixa os PDFs das NRs para data/raw. Uso: python -m rag_nrs.download"""
import urllib.request

from .config import RAW_DIR
from .sources import SOURCES


def download_all(force: bool = False) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for norma, (_, url) in SOURCES.items():
        target = RAW_DIR / f"{norma}.pdf"
        if target.exists() and not force:
            print(f"{norma}: já existe, pulando")
            continue
        req = urllib.request.Request(url, headers={"User-Agent": "rag-nrs/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        if not data.startswith(b"%PDF"):
            raise RuntimeError(f"{norma}: a URL não devolveu um PDF ({url})")
        target.write_bytes(data)
        print(f"{norma}: {len(data) / 1024:.0f} KB")


if __name__ == "__main__":
    download_all()
