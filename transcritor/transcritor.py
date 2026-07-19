"""Orquestração da transcrição e formatação das saídas."""

from __future__ import annotations

import json
from typing import Optional

from .metadados import extrair_metadados
from .modelos import Resultado, Transcricao
from .normalizador import normalizar_item
from .parser import parse_texto

_ORDEM_CATEGORIAS = [
    "Hemograma", "Bioquímica", "Lipidograma", "Função hepática",
    "Eletrólitos", "Tireoide", "Outros", "Não catalogado",
]

_SIMBOLO_SITUACAO = {
    "abaixo": "↓ BAIXO",
    "acima": "↑ ALTO",
    "normal": "normal",
    "sem_referencia": "—",
    "nao_reconhecido": "?",
}


def transcrever(texto: str, sexo: Optional[str] = None,
                metadados: Optional[dict] = None) -> Transcricao:
    """Transcreve o texto de um laudo para a estrutura padronizada.

    Args:
        texto: conteúdo bruto do laudo (texto livre).
        sexo: 'M' ou 'F' para escolher intervalos de referência específicos.
            Se omitido, tenta-se usar o sexo detectado no cabeçalho do laudo.
        metadados: informações extras a anexar (paciente, data etc.).
    """
    meta_laudo, corpo = extrair_metadados(texto)
    if sexo is None:
        sexo = meta_laudo.get("sexo")

    itens = parse_texto(corpo)
    resultados: list[Resultado] = []
    nao_reconhecidos: list[str] = []

    for item in itens:
        resultado = normalizar_item(item, sexo=sexo)
        if resultado.situacao == "nao_reconhecido":
            nao_reconhecidos.append(item.linha)
        else:
            resultados.append(resultado)

    resultados.sort(key=lambda r: (
        _ORDEM_CATEGORIAS.index(r.categoria)
        if r.categoria in _ORDEM_CATEGORIAS else len(_ORDEM_CATEGORIAS),
        r.analito,
    ))

    meta = dict(meta_laudo)
    meta.update(metadados or {})
    if sexo:
        meta.setdefault("sexo", sexo)
    meta["total_reconhecidos"] = len(resultados)
    meta["total_nao_reconhecidos"] = len(nao_reconhecidos)

    return Transcricao(
        resultados=resultados,
        nao_reconhecidos=nao_reconhecidos,
        metadados=meta,
    )


_META_REDUZIDA = ("paciente", "data_coleta", "sexo")


def reduzir(transcricao: Transcricao) -> list[dict]:
    """Reduz os resultados reconhecidos ao essencial para digitação/gravação
    rápida: nome abreviado, valor e unidade — sem código LOINC, categoria,
    faixa de referência ou situação (baixo/normal/alto)."""
    itens = []
    for r in transcricao.resultados:
        itens.append({
            "abreviacao": r.abreviacao or r.analito,
            "valor": r.valor,
            "unidade": r.unidade,
            "limite": r.limite,
        })
    return itens


def para_json(transcricao: Transcricao, formato: str = "completo",
              indent: int = 2) -> str:
    """Serializa a transcrição em JSON.

    Args:
        formato: "completo" (padrão, todos os campos) ou "reduzido"
            (apenas abreviação, valor e unidade dos exames reconhecidos).
    """
    if formato == "reduzido":
        dados = {
            "metadados": {
                k: v for k, v in transcricao.metadados.items()
                if k in _META_REDUZIDA
            },
            "exames": reduzir(transcricao),
        }
    else:
        dados = transcricao.to_dict()
    return json.dumps(dados, ensure_ascii=False, indent=indent)


def _fmt_valor(valor) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor)


def _fmt_intervalo(intervalo) -> str:
    if not intervalo:
        return ""
    minimo, maximo = intervalo.get("minimo"), intervalo.get("maximo")
    if minimo is not None and maximo is not None:
        return f"{_fmt_valor(minimo)} - {_fmt_valor(maximo)}"
    if minimo is not None:
        return f"> {_fmt_valor(minimo)}"
    if maximo is not None:
        return f"< {_fmt_valor(maximo)}"
    return ""


def _linha_reduzida(r) -> str:
    limite = r.limite or ""
    valor = f"{limite}{_fmt_valor(r.valor)}"
    rotulo = (r.abreviacao or r.analito).upper()
    return f"{rotulo}: {valor} {r.unidade}".rstrip()


def para_relatorio(transcricao: Transcricao, formato: str = "completo") -> str:
    """Gera um relatório de texto a partir da transcrição.

    Args:
        formato: "completo" (padrão, relatório detalhado agrupado por
            categoria, com situação e faixa de referência) ou "reduzido"
            (uma linha por exame reconhecido: abreviação, valor e unidade).
    """
    meta = transcricao.metadados

    if formato == "reduzido":
        linhas = [
            f"{chave.replace('_', ' ').title()}: {meta[chave]}"
            for chave in _META_REDUZIDA if chave in meta
        ]
        if linhas:
            linhas.append("")
        linhas.extend(_linha_reduzida(r) for r in transcricao.resultados)
        return "\n".join(linhas)

    linhas: list[str] = []
    linhas.append("=" * 64)
    linhas.append("EXAME DE SANGUE — TRANSCRIÇÃO PADRONIZADA")
    linhas.append("=" * 64)

    for chave in ("paciente", "data_coleta", "sexo", "laboratorio"):
        if chave in meta:
            linhas.append(f"{chave.replace('_', ' ').title()}: {meta[chave]}")
    linhas.append("")

    categoria_atual = None
    for r in transcricao.resultados:
        if r.categoria != categoria_atual:
            categoria_atual = r.categoria
            linhas.append(f"[ {categoria_atual} ]")
        limite = r.limite or ""
        valor = f"{limite}{_fmt_valor(r.valor)}"
        ref = _fmt_intervalo(r.intervalo_referencia)
        ref_txt = f"(ref: {ref} {r.unidade})" if ref else ""
        situacao = _SIMBOLO_SITUACAO.get(r.situacao, r.situacao)
        linhas.append(
            f"  {r.analito:<32} {valor:>10} {r.unidade:<8} "
            f"{situacao:<8} {ref_txt}".rstrip()
        )
    linhas.append("")

    if transcricao.nao_reconhecidos:
        linhas.append("[ Itens não reconhecidos ]")
        for item in transcricao.nao_reconhecidos:
            linhas.append(f"  ? {item}")
        linhas.append("")

    linhas.append("-" * 64)
    linhas.append(
        f"Reconhecidos: {meta.get('total_reconhecidos', 0)} | "
        f"Não reconhecidos: {meta.get('total_nao_reconhecidos', 0)}"
    )
    linhas.append(
        "Intervalos de referência são orientativos e não substituem "
        "avaliação médica."
    )
    return "\n".join(linhas)
