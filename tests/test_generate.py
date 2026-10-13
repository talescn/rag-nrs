from rag_nrs.chunking import Chunk
from rag_nrs.generate import SYSTEM_PROMPT, build_prompt
from rag_nrs.retrieval import Hit


def test_prompt_traz_norma_item_e_pagina_de_cada_trecho():
    hits = [Hit(Chunk("NR-35", "Trabalho em Altura", "35.2 Campo", ["35.2.1"], 1, "acima de 2,0m"), 0.9),
            Hit(Chunk("NR-06", "EPI", "6.5", ["6.5.1", "6.5.1.1"], 3, "gratuitamente"), 0.8)]
    prompt = build_prompt("A partir de que altura?", hits)
    assert '<trecho norma="NR-35" item="35.2.1" pagina="1">' in prompt
    assert 'item="6.5.1, 6.5.1.1"' in prompt
    assert prompt.rstrip().endswith("Pergunta: A partir de que altura?")


def test_instrucoes_pedem_citacao_e_proibem_inventar():
    assert "[NR-35, item 35.2.1]" in SYSTEM_PROMPT
    assert "não encontrou" in SYSTEM_PROMPT
