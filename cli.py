#!/usr/bin/env python3
"""Interface de linha de comando do transcritor de exames de sangue.

Exemplos:
    python cli.py exemplos/exame_exemplo.txt
    python cli.py exemplos/exame_exemplo.txt --formato json --sexo M
    cat laudo.txt | python cli.py --sexo F
"""

from __future__ import annotations

import argparse
import sys

from transcritor import transcrever, para_json, para_relatorio


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Transcreve exames de sangue (texto livre) para um "
                    "padrão canônico ancorado em códigos LOINC."
    )
    parser.add_argument(
        "arquivo", nargs="?",
        help="Arquivo de texto com o laudo. Se omitido, lê da entrada padrão.",
    )
    parser.add_argument(
        "-f", "--formato", choices=["relatorio", "json"], default="relatorio",
        help="Formato de saída (padrão: relatorio).",
    )
    parser.add_argument(
        "-s", "--sexo", choices=["M", "F"],
        help="Sexo do paciente, para escolher intervalos de referência.",
    )
    parser.add_argument(
        "-o", "--saida",
        help="Arquivo de saída. Se omitido, imprime na saída padrão.",
    )
    args = parser.parse_args(argv)

    if args.arquivo:
        try:
            with open(args.arquivo, "r", encoding="utf-8") as f:
                texto = f.read()
        except OSError as exc:
            print(f"Erro ao ler '{args.arquivo}': {exc}", file=sys.stderr)
            return 1
    else:
        texto = sys.stdin.read()

    if not texto.strip():
        print("Nenhum conteúdo de laudo recebido.", file=sys.stderr)
        return 1

    transcricao = transcrever(texto, sexo=args.sexo)
    saida = para_json(transcricao) if args.formato == "json" \
        else para_relatorio(transcricao)

    if args.saida:
        with open(args.saida, "w", encoding="utf-8") as f:
            f.write(saida + "\n")
    else:
        print(saida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
