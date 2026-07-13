"""Casamento com o catálogo, conversão de unidades e avaliação de referência."""

from __future__ import annotations

from typing import Optional

from .catalogo import INDICE_SINONIMOS
from .modelos import Analito, Resultado
from .parser import ItemBruto
from .texto import normalizar_nome, normalizar_unidade, parse_numero_br


def identificar_analito(nome_original: str) -> Optional[Analito]:
    """Encontra o analito do catálogo cujo sinônimo (mais longo) aparece
    como palavra(s) no rótulo. Retorna None se nada casar."""
    alvo = " " + normalizar_nome(nome_original) + " "
    for sinonimo, analito in INDICE_SINONIMOS:  # já ordenado por comprimento
        if (" " + sinonimo + " ") in alvo:
            return analito
    return None


def _selecionar_referencia(analito: Analito, sexo: Optional[str]):
    ref = analito.referencia
    if not ref:
        return None
    if sexo and sexo.upper() in ref:
        return ref[sexo.upper()]
    return ref.get("geral")


def _avaliar_situacao(valor: Optional[float], limite: Optional[str],
                      intervalo) -> str:
    if valor is None:
        return "nao_reconhecido"
    if intervalo is None:
        return "sem_referencia"
    minimo, maximo = intervalo
    # "<5" ou ">40" reportados no laudo: interpretamos o valor como limite.
    if limite == "<":
        # valor está abaixo de X; só conseguimos afirmar "abaixo" se X <= mínimo.
        if minimo is not None and valor <= minimo:
            return "abaixo"
        return "normal"
    if limite == ">":
        if maximo is not None and valor >= maximo:
            return "acima"
        return "normal"
    if minimo is not None and valor < minimo:
        return "abaixo"
    if maximo is not None and valor > maximo:
        return "acima"
    return "normal"


def normalizar_item(item: ItemBruto, sexo: Optional[str] = None) -> Resultado:
    """Transforma um ItemBruto em Resultado padronizado."""
    analito = identificar_analito(item.nome_original)
    valor_origem = parse_numero_br(item.valor_texto)
    observacoes: list[str] = []

    if analito is None:
        return Resultado(
            analito=item.nome_original.strip(),
            categoria="Não catalogado",
            codigo_loinc=None,
            valor=valor_origem,
            unidade=item.unidade_original or None,
            situacao="nao_reconhecido",
            nome_original=item.nome_original.strip(),
            valor_original=item.valor_texto,
            unidade_original=item.unidade_original,
            limite=item.limite,
        )

    unidade_norm = normalizar_unidade(item.unidade_original)
    canonica_norm = normalizar_unidade(analito.unidade)
    valor = valor_origem

    if valor_origem is not None and unidade_norm:
        if unidade_norm == canonica_norm:
            pass  # já está na unidade canônica
        elif unidade_norm in analito.conversoes:
            valor = valor_origem * analito.conversoes[unidade_norm]
            observacoes.append(
                f"Convertido de {item.unidade_original} para {analito.unidade}"
            )
        else:
            observacoes.append(
                f"Unidade '{item.unidade_original}' não reconhecida; "
                f"valor mantido sem conversão"
            )
    elif valor_origem is not None and not unidade_norm:
        observacoes.append(
            f"Unidade ausente; assumida a canônica ({analito.unidade})"
        )

    # Arredonda ruído de ponto flutuante das conversões.
    if valor is not None:
        valor = round(valor, 4)

    intervalo = _selecionar_referencia(analito, sexo)
    # Só avaliamos referência quando o valor está (ou foi levado à) unidade canônica.
    unidade_final_canonica = (
        not unidade_norm
        or unidade_norm == canonica_norm
        or unidade_norm in analito.conversoes
    )
    if unidade_final_canonica:
        situacao = _avaliar_situacao(valor, item.limite, intervalo)
    else:
        situacao = "sem_referencia"

    if analito.observacao:
        observacoes.append(analito.observacao)

    intervalo_dict = None
    if intervalo is not None:
        intervalo_dict = {"minimo": intervalo[0], "maximo": intervalo[1]}

    return Resultado(
        analito=analito.nome,
        categoria=analito.categoria,
        codigo_loinc=analito.codigo_loinc,
        valor=valor,
        unidade=analito.unidade,
        situacao=situacao,
        intervalo_referencia=intervalo_dict,
        nome_original=item.nome_original.strip(),
        valor_original=item.valor_texto,
        unidade_original=item.unidade_original,
        limite=item.limite,
        observacoes=observacoes,
    )
