import json
from pathlib import Path

from blood_exam_transcriber.transcriber import (
    build_report,
    extract_metadata,
    report_to_json,
    results_to_csv,
    transcribe_text,
)

SAMPLE_PATH = Path(__file__).parent.parent / "examples" / "sample_exam.txt"


def load_sample() -> str:
    return SAMPLE_PATH.read_text(encoding="utf-8")


def test_extract_metadata():
    metadata = extract_metadata(load_sample())
    assert metadata["paciente"] == "Maria da Silva"
    assert metadata["data_exame"] == "10/07/2026"


def test_transcribe_text_sample_exam():
    results = transcribe_text(load_sample())
    codigos = {r.codigo for r in results}
    assert len(results) == 13
    assert codigos == {
        "HGB",
        "HCT",
        "LEUC",
        "PLAQ",
        "GLIC",
        "COLT",
        "HDL",
        "TRIG",
        "UREA",
        "CREAT",
        "TGO",
        "TGP",
        "TSH",
    }


def test_transcribe_text_flags_abnormal_values():
    results = {r.codigo: r for r in transcribe_text(load_sample())}
    assert results["HGB"].situacao == "baixo"
    assert results["GLIC"].situacao == "alto"
    assert results["COLT"].situacao == "alto"
    assert results["HDL"].situacao == "baixo"
    assert results["UREA"].situacao == "normal"


def test_build_report_structure():
    report = build_report(load_sample())
    assert report["paciente"] == "Maria da Silva"
    assert report["total_exames"] == 13
    assert len(report["exames"]) == 13


def test_report_to_json_round_trips():
    report = build_report(load_sample())
    parsed = json.loads(report_to_json(report))
    assert parsed["total_exames"] == report["total_exames"]


def test_results_to_csv_has_header_and_rows():
    results = transcribe_text(load_sample())
    csv_text = results_to_csv(results)
    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("codigo,nome_padrao")
    assert len(lines) == len(results) + 1
