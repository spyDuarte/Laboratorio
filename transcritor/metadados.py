"""Extração de metadados do laudo (paciente, data, laboratório, sexo).

Linhas de cabeçalho não são analitos; separá-las evita que apareçam como
"itens não reconhecidos" e permite anexá-las ao resultado padronizado.
"""

from __future__ import annotations

import re

from .texto import normalizar_nome

# Rótulo normalizado -> chave nos metadados.
_CHAVES = {
    "paciente": "paciente",
    "nome": "paciente",
    "nome do paciente": "paciente",
    "data da coleta": "data_coleta",
    "data de coleta": "data_coleta",
    "data coleta": "data_coleta",
    "coleta": "data_coleta",
    "data": "data_coleta",
    "laboratorio": "laboratorio",
    "lab": "laboratorio",
    "sexo": "sexo",
    "genero": "sexo",
    "convenio": "convenio",
    "medico": "medico",
    "medico requisitante": "medico",
    "requisitante": "medico",
}

_SEXO_RE = re.compile(r"\b(masculino|feminino|m|f)\b", re.IGNORECASE)


def _normalizar_sexo(valor: str):
    m = _SEXO_RE.search(valor.strip())
    if not m:
        return None
    inicial = m.group(1)[0].upper()
    return inicial if inicial in ("M", "F") else None


def extrair_metadados(texto: str) -> tuple[dict, str]:
    """Separa linhas de cabeçalho do restante do laudo.

    Retorna (metadados, texto_restante) onde texto_restante contém apenas
    as linhas que devem seguir para a extração de exames.
    """
    metadados: dict = {}
    restantes: list[str] = []

    for linha in texto.splitlines():
        if ":" not in linha:
            restantes.append(linha)
            continue
        rotulo, _, valor = linha.partition(":")
        chave = _CHAVES.get(normalizar_nome(rotulo))
        valor = valor.strip()
        if chave and valor:
            if chave == "sexo":
                sexo = _normalizar_sexo(valor)
                if sexo:
                    metadados[chave] = sexo
                # se não deu para interpretar, ignora silenciosamente
            else:
                metadados[chave] = valor
        else:
            restantes.append(linha)

    return metadados, "\n".join(restantes)
