"""Transcritor de exames de sangue para um padrão canônico (LOINC).

Uso rápido:

    from transcritor import transcrever, para_json, para_relatorio

    t = transcrever("Hemoglobina: 14,5 g/dL\\nGlicose 92 mg/dL", sexo="M")
    print(para_relatorio(t))
    print(para_json(t))
"""

from .transcritor import transcrever, para_json, para_relatorio
from .modelos import Analito, Resultado, Transcricao
from .catalogo import CATALOGO

__all__ = [
    "transcrever",
    "para_json",
    "para_relatorio",
    "Analito",
    "Resultado",
    "Transcricao",
    "CATALOGO",
]

__version__ = "1.0.0"
