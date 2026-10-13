from rag_nrs.chunking import _quebrar, chunk_items, parse_items

PAGINA_1 = """Este texto não substitui o publicado no DOU
NR 35 - TRABALHO EM ALTURA
SUMÁRIO
35.1 Objetivo
35.2 Campo de Aplicação
Glossário

35.1 Objetivo
35.1.1 Esta Norma estabelece os requisitos e as medidas de prevenção para o trabalho em altura,
envolvendo o planejamento, a organização e a execução.
35.2 Campo de Aplicação
35.2.1 Aplica-se a toda atividade com diferença de nível acima de 2,0m do nível inferior.
35.3 Responsabilidades
35.3.1 Cabe à organização:
a) garantir a implementação das medidas de prevenção;
b) assegurar a realização da Análise de Risco.
"""

PAGINA_2 = """Este texto não substitui o publicado no DOU

Anexo I desta NR.

GLOSSÁRIO
Permissão de Trabalho - PT: Documento escrito contendo conjunto de medidas de controle.
Análise de Risco: Avaliação dos riscos potenciais.

ANEXO I da NR-35
1.1 Para fins desta Norma considera-se acesso por cordas a técnica de progressão.
"""


def _itens():
    return parse_items([PAGINA_1, PAGINA_2], "NR-35")


def test_pula_sumario_e_comeca_no_primeiro_item():
    itens = _itens()
    assert itens[0].numero == "35.1.1"
    assert itens[0].secao == "35.1 Objetivo"


def test_alineas_ficam_no_mesmo_item_e_quebras_de_linha_viram_espaco():
    item = next(i for i in _itens() if i.numero == "35.3.1")
    assert "a) garantir" in item.texto and "b) assegurar" in item.texto
    assert "altura, envolvendo" in next(i for i in _itens() if i.numero == "35.1.1").texto


def test_frase_que_vira_a_pagina_comecando_com_anexo_nao_abre_anexo():
    # no topo da página 2, depois do cabeçalho e de uma linha em branco, "Anexo I desta NR." continua o item 35.3.1
    item = next(i for i in _itens() if i.numero == "35.3.1")
    assert "Anexo I desta NR" in item.texto


def test_glossario_separa_definicoes_e_anexo_recomeca_numeracao():
    numeros = [i.numero for i in _itens()]
    assert "Glossário: Permissão de Trabalho - PT" in numeros
    assert "Glossário: Análise de Risco" in numeros
    assert "Anexo I 1.1" in numeros


def test_itens_curtos_da_mesma_secao_sao_unidos_e_ids_sao_unicos():
    chunks = chunk_items(_itens(), "NR-35", "Trabalho em Altura")
    assert all(c.itens for c in chunks)
    assert len({c.id for c in chunks}) == len(chunks)
    # seções diferentes nunca se misturam no mesmo trecho
    assert all(len({i.split(".")[1] for i in c.itens if i.startswith("35.")}) <= 1 for c in chunks)


def test_texto_longo_e_quebrado_com_sobreposicao_comecando_em_palavra():
    texto = " ".join(f"Frase numero {n} sobre seguranca." for n in range(200))
    partes = _quebrar(texto, maximo=300, sobreposicao=60)
    assert len(partes) > 1
    assert all(len(p) <= 300 for p in partes)
    assert all(p.split()[0] in texto.split() for p in partes)  # nenhum pedaço começa no meio de palavra
    assert partes[1][:20] in partes[0]  # há sobreposição
