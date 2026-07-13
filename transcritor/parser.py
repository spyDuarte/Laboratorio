"""Extração de itens (rótulo, valor, unidade) a partir do texto do laudo.

O parser trabalha linha a linha. Para cada linha ele localiza o *último*
número que não esteja colado a uma letra — o que evita confundir dígitos
que fazem parte do nome do analito (B12, A1c, 25-OH) com o valor medido.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .texto import VALOR_RE


@dataclass
class ItemBruto:
    nome_original: str
    valor_texto: str
    limite: Optional[str]  # "<" ou ">" quando presente
    unidade_original: str
    linha: str


# Unidade logo após o valor: sequência de caracteres típicos de unidade.
_UNIDADE_RE = re.compile(r"^[\sº]*([A-Za-zµμ%/][A-Za-zµμ0-9%/^³²·.\-\s]*)")

# Trechos que indicam início do intervalo de referência na mesma linha.
_REF_MARKERS = re.compile(
    r"(valor(es)?\s+de\s+referencia|referencia|vr|v\.?r\.?|intervalo)",
    re.IGNORECASE,
)


def _limpar_unidade(bruto: str) -> str:
    """Isola a unidade do que vem depois dela (intervalo de referência,
    observações etc.)."""
    if not bruto:
        return ""
    # Corta em parêntese, colchete ou marcadores de referência.
    corte = re.split(r"[\(\[]", bruto, maxsplit=1)[0]
    corte = _REF_MARKERS.split(corte)[0]
    # Remove separadores residuais e pontuação de fim de frase.
    corte = corte.strip(" \t.;,:-–—")
    # Uma unidade não costuma ter mais que ~10 caracteres; descarta frases.
    tokens = corte.split()
    if not tokens:
        return ""
    unidade = tokens[0]
    # Casos com barra separada por espaço: "10^3 / uL".
    if len(tokens) >= 2 and (unidade.endswith("/") or tokens[1].startswith("/")):
        unidade = "".join(tokens[:3]) if len(tokens) >= 3 and tokens[1] == "/" \
            else unidade + tokens[1]
    return unidade.strip()


def _intervalos_delimitados(linha: str) -> list[tuple[int, int]]:
    """Faixas [inicio, fim] cobertas por pares balanceados de () e []."""
    pilha: list[int] = []
    faixas: list[tuple[int, int]] = []
    for i, ch in enumerate(linha):
        if ch in "([":
            pilha.append(i)
        elif ch in ")]" and pilha:
            faixas.append((pilha.pop(), i))
    return faixas


def _dentro_de_delimitador(idx: int, faixas: list[tuple[int, int]]) -> bool:
    return any(ini < idx < fim for ini, fim in faixas)


def parse_linha(linha: str) -> Optional[ItemBruto]:
    """Extrai um ItemBruto de uma linha, ou None se não houver valor."""
    matches = list(VALOR_RE.finditer(linha))
    if not matches:
        return None

    # Números dentro de parênteses/colchetes normalmente são intervalos de
    # referência (ex.: "Glicose 92 mg/dL (70-99)") — descartados na escolha
    # do valor medido.
    faixas = _intervalos_delimitados(linha)
    fora = [m for m in matches if not _dentro_de_delimitador(m.start(), faixas)]
    usaveis = fora if fora else matches

    # O valor medido é o último número "solto" da linha.
    m = usaveis[-1]
    limite_raw = (m.group(1) or "").strip()
    limite = None
    if limite_raw:
        limite = "<" if limite_raw[0] in "<≤" else ">"
    valor_texto = m.group(2)

    nome = linha[: m.start()].strip(" \t.:;-–—=…·")
    resto = linha[m.end():]
    unidade = _limpar_unidade(resto)

    if not nome:
        return None

    return ItemBruto(
        nome_original=nome,
        valor_texto=valor_texto,
        limite=limite,
        unidade_original=unidade,
        linha=linha.strip(),
    )


def parse_texto(texto: str) -> list[ItemBruto]:
    """Percorre o laudo linha a linha e devolve os itens brutos encontrados."""
    itens: list[ItemBruto] = []
    for linha in texto.splitlines():
        if not linha.strip():
            continue
        item = parse_linha(linha)
        if item is not None:
            itens.append(item)
    return itens
