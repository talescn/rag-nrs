import pytest

from rag_nrs.chunking import Chunk
from rag_nrs.retrieval import Retriever, rrf, tokenize


def test_tokenize_remove_acentos_e_stopwords_e_mantem_numeros_de_item():
    assert tokenize("Proteção da cabeça no item 35.2.1, acima de 2,0m") == \
        ["protecao", "cabeca", "item", "35.2.1", "acima", "2,0", "m"]


def test_rrf_premia_quem_aparece_bem_nas_duas_listas():
    fundido = rrf([[1, 2, 3], [3, 1, 4]])
    ordem = [i for i, _ in fundido]
    assert ordem[0] == 1          # 1º e 2º lugar
    assert ordem[1] == 3          # 3º e 1º lugar
    assert set(ordem) == {1, 2, 3, 4}


def test_rrf_usa_formula_1_sobre_k_mais_posicao():
    (idx, nota), = rrf([[7]], k=60)
    assert idx == 7 and nota == pytest.approx(1 / 61)


def test_bm25_encontra_trecho_por_palavra_e_rejeita_modo_invalido():
    chunks = [Chunk("NR-06", "EPI", "6.5", ["6.5.1"], 1, "fornecer EPI gratuitamente ao empregado"),
              Chunk("NR-35", "Altura", "35.2", ["35.2.1"], 1, "diferença de nível acima de 2,0m"),
              Chunk("NR-17", "Ergonomia", "17.8", ["17.8.1"], 1, "iluminação apropriada à atividade")]
    r = Retriever(chunks)
    assert r.search("EPI gratuitamente", k=1, mode="bm25")[0].chunk.itens == ["6.5.1"]
    with pytest.raises(ValueError):
        r.search("x", mode="inexistente")
