"""Extração de resultados de exames a partir de texto bruto de laudos."""

import re
from typing import List, Optional, Tuple

from .catalog import Catalog
from .models import ExamResult

_VALUE_RE = re.compile(r"(\d+(?:[.,]\d+)?)")
_RANGE_BETWEEN_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:-|a|até)\s*(\d+(?:[.,]\d+)?)", re.IGNORECASE
)
_RANGE_MAX_RE = re.compile(r"[<≤]\s*(\d+(?:[.,]\d+)?)")
_RANGE_MIN_RE = re.compile(r"[>≥]\s*(\d+(?:[.,]\d+)?)")
_UNIT_RE = re.compile(r"^\s*([A-Za-zµ%/][A-Za-zµ%/0-9]*)")


def _to_float(raw: str) -> float:
    return float(raw.replace(",", "."))


def _extract_value(rest: str) -> Optional[Tuple[float, int]]:
    match = _VALUE_RE.search(rest)
    if not match:
        return None
    return _to_float(match.group(1)), match.end()


def _extract_unit(rest: str) -> Optional[str]:
    match = _UNIT_RE.match(rest)
    if not match:
        return None
    return match.group(1)


def _extract_reference(rest: str) -> Tuple[Optional[float], Optional[float]]:
    between = _RANGE_BETWEEN_RE.search(rest)
    if between:
        return _to_float(between.group(1)), _to_float(between.group(2))
    max_match = _RANGE_MAX_RE.search(rest)
    if max_match:
        return None, _to_float(max_match.group(1))
    min_match = _RANGE_MIN_RE.search(rest)
    if min_match:
        return _to_float(min_match.group(1)), None
    return None, None


def compute_situacao(
    valor: float, ref_min: Optional[float], ref_max: Optional[float]
) -> str:
    if ref_min is not None and ref_max is not None:
        if valor < ref_min:
            return "baixo"
        if valor > ref_max:
            return "alto"
        return "normal"
    if ref_max is not None:
        return "alto" if valor >= ref_max else "normal"
    if ref_min is not None:
        return "baixo" if valor <= ref_min else "normal"
    return "indeterminado"


def parse_line(line: str, catalog: Catalog) -> Optional[ExamResult]:
    """Tenta transcrever uma única linha de texto em um ExamResult."""
    found = catalog.find_in_line(line)
    if not found:
        return None
    entry, _start, end = found
    nome_original = line[_start:end]
    rest = line[end:]

    value_result = _extract_value(rest)
    if value_result is None:
        return None
    valor, value_end = value_result

    unidade = _extract_unit(rest[value_end:])
    ref_min, ref_max = _extract_reference(rest[value_end:])
    if ref_min is None and ref_max is None:
        ref_min, ref_max = entry.reference_min, entry.reference_max

    situacao = compute_situacao(valor, ref_min, ref_max)

    return ExamResult(
        codigo=entry.code,
        nome_padrao=entry.name,
        categoria=entry.category,
        nome_original=nome_original,
        valor=valor,
        unidade_original=unidade,
        unidade_padrao=entry.unit,
        faixa_referencia_min=ref_min,
        faixa_referencia_max=ref_max,
        situacao=situacao,
        linha_original=line,
    )


def parse_text(text: str, catalog: Catalog) -> List[ExamResult]:
    """Percorre todas as linhas do texto e retorna os exames reconhecidos."""
    results = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        result = parse_line(line, catalog)
        if result is not None:
            results.append(result)
    return results
