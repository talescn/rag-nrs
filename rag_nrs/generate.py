"""Gera a resposta com o Gemini a partir dos trechos recuperados, citando norma e item."""
import os
from dataclasses import dataclass

from .config import GEMINI_MODEL
from .retrieval import Hit, Retriever

SYSTEM_PROMPT = """Você é um assistente de consulta às Normas Regulamentadoras (NRs) de segurança e saúde no \
trabalho do Brasil.
Responda em português, usando somente os trechos fornecidos entre <trechos>.
Cite a fonte de cada afirmação no formato [NR-35, item 35.2.1], usando a norma e o item indicados em cada trecho.
Se os trechos não trouxerem a resposta, diga que não encontrou nas normas consultadas e não complete com \
conhecimento próprio.
Comece pela resposta direta e depois detalhe, se for útil. Não invente números, prazos ou itens."""


@dataclass
class Answer:
    texto: str
    hits: list[Hit]


def format_context(hits: list[Hit]) -> str:
    blocos = []
    for h in hits:
        c = h.chunk
        itens = ", ".join(c.itens) if c.itens else c.secao
        blocos.append(f'<trecho norma="{c.norma}" item="{itens}" pagina="{c.pagina}">\n{c.texto}\n</trecho>')
    return "<trechos>\n" + "\n".join(blocos) + "\n</trechos>"


def build_prompt(pergunta: str, hits: list[Hit]) -> str:
    return f"{format_context(hits)}\n\nPergunta: {pergunta}"


def answer(pergunta: str, retriever: Retriever, k: int = 5, mode: str = "dense",
           model: str = GEMINI_MODEL) -> Answer:
    from google import genai
    from google.genai import types

    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        raise RuntimeError("Defina GEMINI_API_KEY no arquivo .env (veja .env.example).")

    hits = retriever.search(pergunta, k=k, mode=mode)
    client = genai.Client()
    resp = client.models.generate_content(
        model=model,
        contents=build_prompt(pergunta, hits),
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.2),
    )
    return Answer(resp.text or "", hits)
