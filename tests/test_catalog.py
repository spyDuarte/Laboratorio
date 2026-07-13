from blood_exam_transcriber.catalog import load_default_catalog, normalize


def test_normalize_strips_accents_and_lowercases():
    assert normalize("Hemoglobina Glicada") == "hemoglobina glicada"
    assert normalize("Triglicerídeos") == "triglicerideos"
    assert normalize("ÁCIDO ÚRICO") == "acido urico"


def test_catalog_loads_entries():
    catalog = load_default_catalog()
    assert len(catalog.entries) > 0
    codes = {entry.code for entry in catalog.entries}
    assert "HGB" in codes
    assert "GLIC" in codes


def test_find_in_line_matches_alias_case_insensitive():
    catalog = load_default_catalog()
    found = catalog.find_in_line("hemoglobina: 13 g/dL")
    assert found is not None
    entry, start, end = found
    assert entry.code == "HGB"
    assert "hemoglobina" in "hemoglobina: 13 g/dL"[start:end].lower()


def test_find_in_line_prefers_longer_alias():
    catalog = load_default_catalog()
    found = catalog.find_in_line("Colesterol Total: 210 mg/dL")
    assert found is not None
    entry, _, _ = found
    assert entry.code == "COLT"


def test_find_in_line_returns_none_when_no_match():
    catalog = load_default_catalog()
    assert catalog.find_in_line("Paciente: Maria da Silva") is None
