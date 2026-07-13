"""Modelos de dados usados na transcrição de exames de sangue.

As estruturas aqui definidas descrevem tanto o *catálogo* de analitos
(o dicionário canônico para onde os resultados são normalizados) quanto o
resultado já transcrito para o padrão de saída.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass(frozen=True)
class Analito:
    """Entrada do catálogo canônico de exames.

    Cada analito representa "para onde" um resultado bruto é normalizado.
    """

    codigo_loinc: str
    nome: str
    categoria: str
    unidade: str
    # Sinônimos já normalizados (minúsculas, sem acento, sem pontuação).
    sinonimos: tuple[str, ...] = ()
    # Fatores de conversão: unidade_normalizada -> fator multiplicativo
    # aplicado ao valor de origem para chegar à unidade canônica.
    conversoes: dict[str, float] = field(default_factory=dict)
    # Intervalos de referência (adulto). Cada chave ("geral", "M", "F")
    # mapeia para (minimo, maximo); qualquer um dos limites pode ser None.
    referencia: dict[str, tuple[Optional[float], Optional[float]]] = field(
        default_factory=dict
    )
    observacao: str = ""


@dataclass
class Resultado:
    """Um resultado de exame já transcrito para o padrão de saída."""

    analito: str
    categoria: str
    codigo_loinc: Optional[str]
    valor: Optional[float]
    unidade: Optional[str]
    situacao: str  # normal | abaixo | acima | sem_referencia | nao_reconhecido
    intervalo_referencia: Optional[dict] = None
    nome_original: str = ""
    valor_original: str = ""
    unidade_original: str = ""
    limite: Optional[str] = None  # "<" ou ">" quando o laudo traz "<5", ">40"
    observacoes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Transcricao:
    """Resultado completo da transcrição de um laudo."""

    resultados: list[Resultado] = field(default_factory=list)
    nao_reconhecidos: list[str] = field(default_factory=list)
    metadados: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "metadados": self.metadados,
            "resultados": [r.to_dict() for r in self.resultados],
            "nao_reconhecidos": self.nao_reconhecidos,
        }
