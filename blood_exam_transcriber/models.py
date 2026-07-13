"""Estruturas de dados usadas pelo transcritor de exames de sangue."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class ExamCatalogEntry:
    """Definição padrão de um exame no catálogo de referência."""

    code: str
    name: str
    category: str
    unit: str
    reference_min: Optional[float]
    reference_max: Optional[float]
    aliases: List[str] = field(default_factory=list)


@dataclass
class ExamResult:
    """Resultado de um exame já transcrito para o padrão definido."""

    codigo: str
    nome_padrao: str
    categoria: str
    nome_original: str
    valor: float
    unidade_original: Optional[str]
    unidade_padrao: str
    faixa_referencia_min: Optional[float]
    faixa_referencia_max: Optional[float]
    situacao: str
    linha_original: str

    def to_dict(self) -> dict:
        return asdict(self)
