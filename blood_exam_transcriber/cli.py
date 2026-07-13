"""Interface de linha de comando do transcritor de exames de sangue."""

import argparse
import sys
from pathlib import Path

from .transcriber import build_report, report_to_json, results_to_csv, transcribe_text
from .catalog import load_default_catalog, load_catalog


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blood-exam-transcriber",
        description="Transcreve laudos de exames de sangue (texto) para um padrão definido.",
    )
    parser.add_argument("input", help="Arquivo de texto com o laudo de exame de sangue")
    parser.add_argument(
        "-o", "--output", help="Arquivo de saída (padrão: stdout)", default=None
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Formato de saída (padrão: json)",
    )
    parser.add_argument(
        "-c",
        "--catalog",
        help="Caminho para um catálogo de exames padrão customizado (JSON)",
        default=None,
    )
    return parser


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)

    input_path = Path(args.input)
    text = input_path.read_text(encoding="utf-8")

    catalog = load_catalog(Path(args.catalog)) if args.catalog else load_default_catalog()

    if args.format == "json":
        report = build_report(text, catalog)
        output = report_to_json(report)
    else:
        results = transcribe_text(text, catalog)
        output = results_to_csv(results)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
