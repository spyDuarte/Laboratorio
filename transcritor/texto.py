"""Funções utilitárias de normalização de texto, números e unidades.

Separadas em um módulo próprio porque são usadas tanto pelo catálogo
(para gerar sinônimos normalizados) quanto pelo parser e pelo normalizador.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional


def remover_acentos(texto: str) -> str:
    """Remove acentos preservando o comprimento (1 caractere de entrada
    gera 1 caractere de saída), o que mantém posições alinhadas."""
    saida = []
    for ch in texto:
        decomposto = unicodedata.normalize("NFKD", ch)
        base = decomposto[0] if decomposto else ch
        saida.append(base)
    return "".join(saida)


def normalizar_nome(texto: str) -> str:
    """Normaliza um rótulo de exame para comparação: minúsculas, sem
    acento, com pontuação convertida em espaço e espaços colapsados."""
    t = remover_acentos(texto).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalizar_unidade(unidade: str) -> str:
    """Normaliza uma unidade para uma forma canônica comparável.

    Ex.: 'mg/dL', 'MG / DL', 'mg/dl ' -> 'mg/dl'.
    """
    if not unidade:
        return ""
    u = remover_acentos(unidade).lower().strip()
    # micro (µ ou μ) -> u
    u = u.replace("µ", "u").replace("μ", "u")
    # expoentes: 10^3, 10³, x10^3 -> 10e3
    u = u.replace("×", "x")
    u = re.sub(r"10\s*\^?\s*3", "10e3", u)
    u = re.sub(r"10\s*\^?\s*6", "10e6", u)
    u = re.sub(r"10\s*\^?\s*9", "10e9", u)
    u = re.sub(r"10\s*\^?\s*12", "10e12", u)
    u = u.replace("³", "3").replace("²", "2")
    u = u.replace(" ", "")
    return u


# Casa um número no formato brasileiro OU internacional.
# Alternativas ordenadas para preferir agrupamento de milhar com ponto.
_NUM = (
    r"\d{1,3}(?:\.\d{3})+(?:,\d+)?"   # 250.000  /  1.234,5
    r"|\d+,\d+"                        # 14,5
    r"|\d+\.\d+"                       # 14.5
    r"|\d+"                            # 43
)

# Um valor pode vir prefixado por um marcador de limite (<, >, ≤, ≥). Ele não
# pode estar "colado" a uma letra/dígito anterior (evita capturar o '12' de
# 'B12' ou o '1' de 'A1c') nem fazer parte da notação científica de uma
# unidade (o '10' e o '3' de '10^3/µL', o '10' de '10³/µL').
VALOR_RE = re.compile(
    r"(?<![A-Za-z0-9^³²])([<>≤≥]\s*)?(" + _NUM + r")(?![\^³²\d])"
)


def parse_numero_br(texto: str) -> Optional[float]:
    """Converte um número em texto (formato BR ou internacional) para float.

    Heurística para o ponto isolado: '7.200' e '250.000' (exatamente 3
    dígitos após o ponto e sem vírgula) são tratados como separador de
    milhar; '14.5' e '1.2' permanecem decimais.
    """
    if texto is None:
        return None
    t = texto.strip().replace(" ", "")
    if not t:
        return None

    tem_virgula = "," in t
    qtd_pontos = t.count(".")

    if tem_virgula:
        # Vírgula é o separador decimal; pontos são de milhar.
        t = t.replace(".", "").replace(",", ".")
    elif qtd_pontos >= 2:
        # Vários pontos só fazem sentido como separadores de milhar.
        t = t.replace(".", "")
    elif qtd_pontos == 1:
        inteiro, frac = t.split(".")
        if len(frac) == 3:
            # Ex.: 7.200 / 250.000 -> milhar.
            t = inteiro + frac
        # senão, mantém como decimal (14.5).
    try:
        return float(t)
    except ValueError:
        return None
