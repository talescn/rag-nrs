"""Divide o texto de uma NR em trechos que seguem a numeração da própria norma (ex.: 35.4.2.1).

Cada item numerado vira um trecho, junto com suas alíneas (a, b, c...). Itens muito curtos são unidos ao
seguinte, e itens longos são quebrados com sobreposição. Assim cada trecho pode ser citado pelo número do item.
"""
import re
from dataclasses import dataclass, field

PAGE_HEADER = "Este texto não substitui o publicado no DOU"
MIN_CHUNK_CHARS = 250


@dataclass
class Chunk:
    norma: str
    titulo: str
    secao: str
    itens: list[str]
    pagina: int
    texto: str
    id: str = ""

    @property
    def item(self) -> str:
        return self.itens[0] if self.itens else self.secao

    def contexto(self) -> str:
        """Texto usado na busca: o trecho precedido de norma e seção, para o trecho não ficar sem contexto."""
        return f"{self.norma} {self.titulo} | {self.secao}\n{self.texto}"


@dataclass
class _Item:
    numero: str | None
    secao: str
    pagina: int
    linhas: list[str] = field(default_factory=list)

    @property
    def texto(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.linhas)).strip()


# título de anexo: "ANEXO I", "Anexo I da NR-01", "ANEXO III da NR-35 - ESCADAS" (mas não "Anexo I desta NR.")
_ANEXO = re.compile(r"^(?:ANEXO|Anexo)\s+([IVXL]+)\s*(?:$|[-–]|da\b|DA\b)")
_GLOSSARIO = re.compile(r"^(?:GLOSSÁRIO|Glossário)\s*$")
# dentro de anexos a numeração recomeça (1.1, 2.3.1...) ou usa letra (A.1 - Capacete, na lista de EPI da NR-06)
_ITEM_ANEXO = re.compile(r"^(\d+(?:\.\d+)+|[A-Z]\.\d+)\.?\s+(?:-\s+)?(.+)")
# definição de glossário: "Termo: texto da definição"
_DEFINICAO = re.compile(r"^([A-ZÀ-Ú][^:]{1,60}):\s")


def _patterns(numero_nr: int):
    n = str(numero_nr)
    # item: "35.4.2.1 Texto" (pelo menos dois níveis abaixo do número da norma)
    item = re.compile(rf"^({n}(?:\.\d+){{2,}})\.?\s+(.+)")
    # seção: "35.4 Autorização, Capacitação e Aptidão" (um nível, título curto sem ponto final)
    secao = re.compile(rf"^({n}\.\d+)\.?\s+([A-ZÀ-Ú][^.]{{2,90}})$")
    return item, secao


def parse_items(paginas: list[str], norma: str) -> list[_Item]:
    """Percorre as páginas e agrupa as linhas por item numerado."""
    numero_nr = int(norma.split("-")[1])
    re_item, re_secao = _patterns(numero_nr)
    primeiro_item = re.compile(rf"^{numero_nr}\.1\.1\.?\s")

    itens: list[_Item] = []
    secao = ""
    rotulo_anexo: str | None = None  # "Anexo I", "Glossário" ou None no corpo da norma
    no_corpo = False  # pula histórico de portarias e sumário até o primeiro item real
    secao_pendente = ""
    atual: _Item | None = None
    anterior_vazia = True  # títulos de anexo e glossário vêm depois de uma linha em branco

    for num_pagina, texto in enumerate(paginas, start=1):
        for bruta in texto.splitlines():
            linha = bruta.replace(" ", " ").strip()
            if not linha or linha.startswith(PAGE_HEADER):
                anterior_vazia = True
                continue
            depois_de_vazia, anterior_vazia = anterior_vazia, False

            if not no_corpo:
                if m := re_secao.match(linha):
                    secao_pendente = f"{m.group(1)} {m.group(2).strip()}"
                if not primeiro_item.match(linha):
                    continue
                no_corpo, secao = True, secao_pendente

            m_anexo = _ANEXO.match(linha) if depois_de_vazia else None
            if m_anexo or (depois_de_vazia and _GLOSSARIO.match(linha)):
                rotulo_anexo = f"Anexo {m_anexo.group(1)}" if m_anexo else "Glossário"
                secao = linha
                atual = None
                continue

            if rotulo_anexo is None and (m := re_secao.match(linha)):
                secao = f"{m.group(1)} {m.group(2).strip()}"
                atual = None
                continue

            m_item = (_ITEM_ANEXO if rotulo_anexo else re_item).match(linha)
            if m_item:
                numero = m_item.group(1)
                if rotulo_anexo:
                    numero = f"{rotulo_anexo} {numero}"
                atual = _Item(numero, secao, num_pagina, [linha])
                itens.append(atual)
                continue

            # no glossário, cada definição começa uma linha depois que a anterior terminou em ponto
            m_def = _DEFINICAO.match(linha) if rotulo_anexo else None
            if m_def and (atual is None or atual.texto.endswith(".")):
                atual = _Item(f"{rotulo_anexo}: {m_def.group(1).strip()}", secao, num_pagina, [linha])
                itens.append(atual)
                continue

            if atual is None:
                atual = _Item(None, secao, num_pagina, [])
                itens.append(atual)
            atual.linhas.append(linha)

    return [i for i in itens if i.texto]


def _quebrar(texto: str, maximo: int, sobreposicao: int) -> list[str]:
    """Quebra um texto longo em pedaços de até `maximo` caracteres, cortando em fim de frase quando dá."""
    if len(texto) <= maximo:
        return [texto]
    pedacos, inicio = [], 0
    while inicio < len(texto):
        fim = min(inicio + maximo, len(texto))
        if fim < len(texto):
            corte = max(texto.rfind(". ", inicio, fim), texto.rfind("; ", inicio, fim))
            if corte > inicio + maximo // 2:
                fim = corte + 1
        pedacos.append(texto[inicio:fim].strip())
        if fim >= len(texto):
            break
        # a sobreposição começa sempre no início de uma palavra
        inicio = max(fim - sobreposicao, inicio + 1)
        espaco = texto.find(" ", inicio, fim)
        if espaco != -1:
            inicio = espaco + 1
    return pedacos


def chunk_items(itens: list[_Item], norma: str, titulo: str,
                max_chars: int = 1500, overlap: int = 200) -> list[Chunk]:
    """Junta itens curtos ao seguinte (mesma seção) e quebra os longos."""
    chunks: list[Chunk] = []
    grupo: list[_Item] = []

    def fechar():
        if not grupo:
            return
        texto = " ".join(i.texto for i in grupo)
        numeros = [i.numero for i in grupo if i.numero]
        for parte in _quebrar(texto, max_chars, overlap):
            chunks.append(Chunk(norma, titulo, grupo[0].secao, numeros, grupo[0].pagina, parte))
        grupo.clear()

    for item in itens:
        if grupo and item.secao != grupo[0].secao:
            fechar()
        grupo.append(item)
        if sum(len(i.texto) for i in grupo) >= MIN_CHUNK_CHARS:
            fechar()
    fechar()

    for n, c in enumerate(chunks):
        c.id = f"{norma}#{n:04d}"
    return chunks
