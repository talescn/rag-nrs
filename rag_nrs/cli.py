"""Pergunta pela linha de comando. Uso: python -m rag_nrs.cli "A empresa pode cobrar pelo EPI?" [--no-llm]"""
import argparse
import sys

from .retrieval import MODES, Retriever


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Consulta às Normas Regulamentadoras com RAG")
    p.add_argument("pergunta")
    p.add_argument("-k", type=int, default=5, help="quantos trechos recuperar")
    p.add_argument("--mode", choices=MODES, default="dense")
    p.add_argument("--no-llm", action="store_true", help="só mostra os trechos, sem chamar o Gemini")
    args = p.parse_args()

    retriever = Retriever.load()
    if args.no_llm:
        hits = retriever.search(args.pergunta, k=args.k, mode=args.mode)
    else:
        from .generate import answer
        try:
            resposta = answer(args.pergunta, retriever, k=args.k, mode=args.mode)
        except RuntimeError as e:
            sys.exit(f"Erro: {e}\nPara ver só os trechos recuperados, use --no-llm.")
        print(resposta.texto, "\n")
        hits = resposta.hits

    print("Fontes:")
    for n, h in enumerate(hits, start=1):
        c = h.chunk
        itens = ", ".join(c.itens) if c.itens else c.secao
        print(f"  {n}. {c.norma}, itens {itens} (p. {c.pagina}) [{h.score:.3f}]: {c.texto[:110]}...")


if __name__ == "__main__":
    main()
