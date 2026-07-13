import pytest

from blood_exam_transcriber.catalog import load_default_catalog
from blood_exam_transcriber.parser import compute_situacao, parse_line, parse_text

CATALOG = load_default_catalog()


def test_parse_line_between_range_low():
    result = parse_line("Hemoglobina: 11.2 g/dL (12.0 - 16.0)", CATALOG)
    assert result is not None
    assert result.codigo == "HGB"
    assert result.valor == 11.2
    assert result.unidade_original == "g/dL"
    assert result.faixa_referencia_min == 12.0
    assert result.faixa_referencia_max == 16.0
    assert result.situacao == "baixo"


def test_parse_line_between_range_normal():
    result = parse_line("Ureia: 32 mg/dL (10 - 50)", CATALOG)
    assert result is not None
    assert result.situacao == "normal"


def test_parse_line_upper_bound_only():
    result = parse_line("Colesterol Total: 210 mg/dL (< 200)", CATALOG)
    assert result is not None
    assert result.faixa_referencia_min is None
    assert result.faixa_referencia_max == 200.0
    assert result.situacao == "alto"


def test_parse_line_lower_bound_only():
    result = parse_line("HDL: 38 mg/dL (> 40)", CATALOG)
    assert result is not None
    assert result.faixa_referencia_min == 40.0
    assert result.faixa_referencia_max is None
    assert result.situacao == "baixo"


def test_parse_line_falls_back_to_catalog_reference():
    result = parse_line("Glicose: 105", CATALOG)
    assert result is not None
    assert result.faixa_referencia_min == 70.0
    assert result.faixa_referencia_max == 99.0
    assert result.situacao == "alto"


def test_parse_line_unrecognized_exam_returns_none():
    assert parse_line("Observações: nada digno de nota", CATALOG) is None


def test_parse_line_no_value_returns_none():
    assert parse_line("Hemoglobina: resultado pendente", CATALOG) is None


@pytest.mark.parametrize(
    "valor,ref_min,ref_max,esperado",
    [
        (10, 5, 20, "normal"),
        (2, 5, 20, "baixo"),
        (25, 5, 20, "alto"),
        (10, None, 20, "normal"),
        (25, None, 20, "alto"),
        (10, 5, None, "normal"),
        (2, 5, None, "baixo"),
        (10, None, None, "indeterminado"),
    ],
)
def test_compute_situacao(valor, ref_min, ref_max, esperado):
    assert compute_situacao(valor, ref_min, ref_max) == esperado


def test_parse_text_ignores_headers_and_blank_lines():
    text = "HEMOGRAMA COMPLETO\n\nHemoglobina: 14 g/dL (12.0 - 16.0)\n"
    results = parse_text(text, CATALOG)
    assert len(results) == 1
    assert results[0].codigo == "HGB"
