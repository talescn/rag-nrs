"""Interface web. Uso: streamlit run app.py"""
import streamlit as st

from rag_nrs.config import GEMINI_MODEL
from rag_nrs.retrieval import MODES, Retriever
from rag_nrs.sources import SOURCES

st.set_page_config(page_title="Consulta às NRs", page_icon="🦺")


@st.cache_resource
def get_retriever() -> Retriever:
    return Retriever.load()


st.title("Consulta às Normas Regulamentadoras")
st.caption("RAG sobre NR-01, 05, 06, 11, 17, 23 e 35. As respostas citam norma e item; confira sempre o texto oficial.")

with st.sidebar:
    mode = st.selectbox("Busca", MODES, index=MODES.index("dense"),
                        help="dense teve o melhor resultado na avaliação (evaluation/results.md)")
    k = st.slider("Trechos enviados ao modelo", 1, 10, 5)
    usar_llm = st.toggle(f"Gerar resposta com {GEMINI_MODEL}", value=True)

pergunta = st.text_input("Pergunta", placeholder="Ex.: a empresa pode cobrar do funcionário pelo EPI?")
if pergunta:
    retriever = get_retriever()
    if usar_llm:
        from rag_nrs.generate import answer
        try:
            with st.spinner("Consultando as normas..."):
                resposta = answer(pergunta, retriever, k=k, mode=mode)
            st.markdown(resposta.texto)
            hits = resposta.hits
        except RuntimeError as e:
            st.error(str(e))
            hits = retriever.search(pergunta, k=k, mode=mode)
    else:
        hits = retriever.search(pergunta, k=k, mode=mode)

    st.subheader("Fontes")
    for h in hits:
        c = h.chunk
        url = f"{SOURCES[c.norma][1]}#page={c.pagina}"
        itens = ", ".join(c.itens) if c.itens else c.secao
        with st.expander(f"{c.norma}, itens {itens} · p. {c.pagina}"):
            st.write(c.texto)
            st.markdown(f"[Abrir o PDF oficial na página {c.pagina}]({url})")
