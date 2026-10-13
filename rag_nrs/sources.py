"""PDFs oficiais das Normas Regulamentadoras usadas no corpus (gov.br, Ministério do Trabalho e Emprego)."""

_BASE = (
    "https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/"
    "conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente"
)
_VIGENTES = f"{_BASE}/normas-regulamentadora/normas-regulamentadoras-vigentes"
_ARQUIVOS = f"{_BASE}/arquivos/normas-regulamentadoras"

# norma -> (título, URL do PDF). Versões mais recentes publicadas em out/2026.
SOURCES: dict[str, tuple[str, str]] = {
    "NR-01": ("Disposições Gerais e Gerenciamento de Riscos Ocupacionais",
              f"{_VIGENTES}/nr-01-atualizada-2025-i-3.pdf"),
    "NR-05": ("Comissão Interna de Prevenção de Acidentes e de Assédio (CIPA)",
              f"{_VIGENTES}/NR05atualizada2023.pdf"),
    "NR-06": ("Equipamento de Proteção Individual (EPI)",
              f"{_VIGENTES}/nr-06-atualizada-2025-ii.pdf"),
    "NR-11": ("Transporte, Movimentação, Armazenagem e Manuseio de Materiais",
              f"{_VIGENTES}/nr-11-atualizada-2016.pdf"),
    "NR-17": ("Ergonomia",
              f"{_VIGENTES}/nr-17-atualizada-2023.pdf"),
    "NR-23": ("Proteção Contra Incêndios",
              f"{_ARQUIVOS}/nr-23-atualizada-2022.pdf"),
    "NR-35": ("Trabalho em Altura",
              f"{_VIGENTES}/nr-35-atualizada-2025-1.pdf"),
}
