"""Carregamento e busca no catálogo de exames padrão."""

import json
import re
import unicodedata
from pathlib import Path
from typing import List, Optional, Tuple

from .models import ExamCatalogEntry

DEFAULT_CATALOG_PATH = Path(__file__).parent / "data" / "standard_catalog.json"


def normalize(text: str) -> str:
    """Remove acentos e caixa alta para permitir comparação tolerante."""
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return without_accents.lower()


class Catalog:
    """Catálogo de exames padrão, indexado para busca por apelido (alias)."""

    def __init__(self, entries: List[ExamCatalogEntry]):
        self.entries = entries
        # Ordena por tamanho do alias normalizado (maior primeiro) para que
        # apelidos mais específicos (ex: "colesterol total") sejam
        # verificados antes de apelidos genéricos (ex: "colesterol").
        pairs = [
            (normalize(alias), entry)
            for entry in entries
            for alias in entry.aliases
        ]
        self._aliases_desc: List[Tuple[str, ExamCatalogEntry]] = sorted(
            pairs, key=lambda pair: len(pair[0]), reverse=True
        )

    def find_in_line(
        self, line: str
    ) -> Optional[Tuple[ExamCatalogEntry, int, int]]:
        """Procura o primeiro apelido conhecido dentro de uma linha de texto.

        Retorna a entrada do catálogo e os índices (start, end) do trecho
        correspondente na linha original, ou None se nada for encontrado.
        """
        normalized_line = normalize(line)
        for alias, entry in self._aliases_desc:
            match = re.search(r"\b" + re.escape(alias) + r"\b", normalized_line)
            if match:
                return entry, match.start(), match.end()
        return None

    def get(self, code: str) -> Optional[ExamCatalogEntry]:
        for entry in self.entries:
            if entry.code == code:
                return entry
        return None


def load_catalog(path: Path = DEFAULT_CATALOG_PATH) -> Catalog:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = [ExamCatalogEntry(**item) for item in data]
    return Catalog(entries)


def load_default_catalog() -> Catalog:
    return load_catalog(DEFAULT_CATALOG_PATH)
