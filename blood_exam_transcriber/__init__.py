"""Transcritor de exames de sangue para um padrão estruturado definido."""

from .catalog import Catalog, load_catalog, load_default_catalog
from .models import ExamCatalogEntry, ExamResult
from .transcriber import (
    build_report,
    extract_metadata,
    report_to_json,
    results_to_csv,
    transcribe_text,
)

__all__ = [
    "Catalog",
    "load_catalog",
    "load_default_catalog",
    "ExamCatalogEntry",
    "ExamResult",
    "build_report",
    "extract_metadata",
    "report_to_json",
    "results_to_csv",
    "transcribe_text",
]

__version__ = "0.1.0"
