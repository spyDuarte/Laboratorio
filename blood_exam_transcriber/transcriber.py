"""Orquestra a transcrição de um laudo de exame de sangue para o padrão."""

import csv
import io
import json
import re
from typing import List, Optional

from .catalog import Catalog, load_default_catalog
from .models import ExamResult
from .parser import parse_text

_PACIENTE_RE = re.compile(r"paciente\s*:\s*(.+)", re.IGNORECASE)
_DATA_RE = re.compile(r"data(?:\s+do\s+exame)?\s*:\s*([\d/\-]+)", re.IGNORECASE)

CSV_FIELDS = [
    "codigo",
    "nome_padrao",
    "categoria",
    "nome_original",
    "valor",
    "unidade_original",
    "unidade_padrao",
    "faixa_referencia_min",
    "faixa_referencia_max",
    "situacao",
    "linha_original",
]


def extract_metadata(text: str) -> dict:
    """Extrai metadados simples do laudo, como nome do paciente e data."""
    metadata: dict = {}
    paciente_match = _PACIENTE_RE.search(text)
    if paciente_match:
        metadata["paciente"] = paciente_match.group(1).strip()
    data_match = _DATA_RE.search(text)
    if data_match:
        metadata["data_exame"] = data_match.group(1).strip()
    return metadata


def transcribe_text(text: str, catalog: Optional[Catalog] = None) -> List[ExamResult]:
    """Transcreve o texto bruto de um exame para uma lista de ExamResult."""
    catalog = catalog or load_default_catalog()
    return parse_text(text, catalog)


def build_report(text: str, catalog: Optional[Catalog] = None) -> dict:
    """Monta o relatório padronizado completo (metadados + exames)."""
    catalog = catalog or load_default_catalog()
    metadata = extract_metadata(text)
    results = transcribe_text(text, catalog)
    return {
        "paciente": metadata.get("paciente"),
        "data_exame": metadata.get("data_exame"),
        "total_exames": len(results),
        "exames": [result.to_dict() for result in results],
    }


def report_to_json(report: dict, indent: int = 2) -> str:
    return json.dumps(report, ensure_ascii=False, indent=indent)


def results_to_csv(results: List[ExamResult]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for result in results:
        writer.writerow(result.to_dict())
    return buffer.getvalue()
