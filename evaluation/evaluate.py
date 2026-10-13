"""Mede a qualidade da busca com perguntas rotuladas. Uso: python -m evaluation.evaluate

Para cada pergunta, o trecho certo é qualquer trecho da norma esperada que contenha um dos itens esperados.
Métricas: Recall@k (o trecho certo aparece entre os k primeiros) e MRR@10 (média de 1/posição do primeiro acerto).
"""
import json
import sys
from pathlib import Path

from rag_nrs.retrieval import MODES, Retriever

HERE = Path(__file__).parent
KS = (1, 3, 5, 10)


def load_questions() -> list[dict]:
    with open(HERE / "questions.jsonl", encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]


def is_relevant(chunk, q: dict) -> bool:
    return chunk.norma == q["norma"] and any(i in chunk.itens for i in q["itens"])


def check_labels(retriever: Retriever, questions: list[dict]) -> None:
    """Garante que todo item esperado existe no índice; senão a métrica mediria um rótulo errado."""
    faltando = [q["pergunta"] for q in questions if not any(is_relevant(c, q) for c in retriever.chunks)]
    if faltando:
        sys.exit("Itens esperados que não existem no índice:\n- " + "\n- ".join(faltando))


def first_hit_rank(retriever: Retriever, q: dict, mode: str) -> int | None:
    hits = retriever.search(q["pergunta"], k=max(KS), mode=mode)
    return next((pos for pos, h in enumerate(hits, start=1) if is_relevant(h.chunk, q)), None)


def evaluate(retriever: Retriever, questions: list[dict]) -> tuple[dict, dict]:
    metricas, ranks = {}, {}
    for mode in MODES:
        r = [first_hit_rank(retriever, q, mode) for q in questions]
        ranks[mode] = r
        n = len(questions)
        metricas[mode] = {f"Recall@{k}": sum(1 for x in r if x and x <= k) / n for k in KS}
        metricas[mode]["MRR@10"] = sum(1 / x for x in r if x) / n
    return metricas, ranks


def to_markdown(metricas: dict, ranks: dict, questions: list[dict]) -> str:
    nomes = {"bm25": "BM25 (palavras-chave)", "dense": "Densa (embeddings)", "hybrid": "Híbrida (RRF)"}
    colunas = list(next(iter(metricas.values())).keys())
    linhas = [f"# Avaliação da busca ({len(questions)} perguntas)", "",
              "| Busca | " + " | ".join(colunas) + " |", "|---|" + "---:|" * len(colunas)]
    for mode, m in metricas.items():
        linhas.append(f"| {nomes[mode]} | " + " | ".join(f"{v:.2f}" for v in m.values()) + " |")
    linhas += ["", "## Posição do primeiro trecho certo (- = fora do top 10)", "",
               "| Pergunta | Norma | BM25 | Densa | Híbrida |", "|---|---|---:|---:|---:|"]
    for i, q in enumerate(questions):
        pos = [str(ranks[m][i]) if ranks[m][i] else "-" for m in MODES]
        linhas.append(f"| {q['pergunta']} | {q['norma']} | " + " | ".join(pos) + " |")
    return "\n".join(linhas) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    questions = load_questions()
    retriever = Retriever.load()
    check_labels(retriever, questions)
    metricas, ranks = evaluate(retriever, questions)
    md = to_markdown(metricas, ranks, questions)
    (HERE / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
