# Laboratorio

Ferramenta em Python para **transcrever laudos de exames de sangue (texto) para um padrão estruturado definido**.

Recebe o texto de um laudo (por exemplo, extraído de um PDF/OCR) e devolve os resultados normalizados — nome padronizado do exame, valor, unidade, faixa de referência e situação (`baixo` / `normal` / `alto`) — em JSON ou CSV, prontos para armazenamento, integração ou análise.

## Como funciona

1. Um **catálogo padrão** (`blood_exam_transcriber/data/standard_catalog.json`) define, para cada exame, o código, nome padronizado, categoria, unidade, faixa de referência padrão e os apelidos/sinônimos usados em laudos (ex.: "Hemoglobina", "Hb", "HGB").
2. O **parser** (`blood_exam_transcriber/parser.py`) varre o texto linha a linha, identifica exames conhecidos pelo apelido (ignorando acentos e maiúsculas/minúsculas), extrai valor, unidade e faixa de referência informados no próprio laudo (ou usa a faixa padrão do catálogo quando o laudo não traz uma) e calcula a situação do resultado.
3. O **transcritor** (`blood_exam_transcriber/transcriber.py`) monta o relatório final, incluindo metadados simples do laudo (paciente, data), e exporta para JSON ou CSV.

## Instalação

```bash
pip install -e .
```

## Uso via linha de comando

```bash
python -m blood_exam_transcriber examples/sample_exam.txt
```

Ou, após instalado:

```bash
blood-exam-transcriber examples/sample_exam.txt --format json
blood-exam-transcriber examples/sample_exam.txt --format csv -o resultado.csv
```

Também é possível apontar para um catálogo padrão customizado:

```bash
blood-exam-transcriber laudo.txt --catalog meu_catalogo.json
```

## Uso como biblioteca

```python
from blood_exam_transcriber import build_report, report_to_json

texto = open("examples/sample_exam.txt", encoding="utf-8").read()
relatorio = build_report(texto)
print(report_to_json(relatorio))
```

## Analitos suportados

| Categoria        | Exames |
|------------------|--------|
| Hemograma        | Hemoglobina, Hematócrito, Eritrócitos, Leucócitos, Plaquetas, VCM, HCM, CHCM, RDW |
| Bioquímica       | Glicose, HbA1c, Ureia, Creatinina, Ácido úrico, Ferro sérico, LDH, CK/CPK, Amilase, Lipase |
| Lipidograma      | Colesterol total, HDL, LDL, VLDL, Triglicerídeos |
| Função hepática  | AST (TGO), ALT (TGP), Gama GT, Fosfatase alcalina, Bilirrubina total/direta/indireta, Proteínas totais, Albumina |
| Eletrólitos      | Sódio, Potássio, Cloro, Cálcio, Magnésio, Fósforo |
| Tireoide         | TSH, T4 livre, T3 total |
| Outros           | Ferritina, Vitamina D (25-OH), Vitamina B12, PCR, VHS |

São **47 analitos** no total, cada um com uma **abreviação** curta (ex.:
Hemoglobina → `HB`, Colesterol total → `CT`, TGO → `TGO`), usada na entrada
rápida e no formato reduzido descritos abaixo. O parser ignora faixas de
referência escritas na mesma linha entre parênteses ou colchetes (ex.:
`Glicose 92 mg/dL (70-99)`).

## Entrada rápida e nível de detalhe (completo ou reduzido)

O objetivo do transcritor é permitir **digitar exames rapidamente**: em vez
de escrever um laudo inteiro, você adiciona só os exames pedidos pelo
médico (por nome ou abreviação) e digita apenas o valor de cada um — a
unidade e o nome padronizado vêm do catálogo automaticamente.

O resultado pode ser salvo em dois níveis de detalhe:

- **Completo** (padrão): nome, código LOINC, unidade, faixa de referência e
  situação (`baixo` / `normal` / `alto`) de cada exame.
- **Reduzido**: só a abreviação, o valor e a unidade — sem faixa de
  referência nem situação. Pensado para registros rápidos e compactos.

Na CLI, use `--nivel reduzido` (ou `--nivel completo`, o padrão):

```bash
python cli.py laudo.txt --nivel reduzido
python cli.py laudo.txt --formato json --nivel reduzido
```

Saída reduzida em texto (uma linha por exame):

```
HB: 11.2 g/dL
GLIC: 105 mg/dL
CT: 210 mg/dL
```

Na versão web (`docs/`, publicada via GitHub Pages), a aba **Entrada
rápida** oferece uma busca com autocompletar por nome/abreviação: digite,
pressione Enter para adicionar o exame à lista, digite o valor e Enter
novamente para o próximo — sem precisar redigitar unidade, faixa de
referência ou nome completo. O seletor **Salvar como** alterna entre
Completo e Reduzido, refletido na tabela, no JSON e no texto exportados. A
aba **Colar laudo** mantém o fluxo original de colar um laudo em texto
livre.

JSON completo (`--formato json`, padrão `--nivel completo`):

```json
{
  "metadados": { "total_reconhecidos": 1, "total_nao_reconhecidos": 0 },
  "resultados": [
    {
      "analito": "Hemoglobina",
      "abreviacao": "HB",
      "categoria": "Hemograma",
      "codigo_loinc": "718-7",
      "valor": 11.2,
      "unidade": "g/dL",
      "situacao": "abaixo",
      "intervalo_referencia": { "minimo": 12.0, "maximo": 17.5 },
      "nome_original": "Hemoglobina",
      "valor_original": "11,2",
      "unidade_original": "g/dL",
      "limite": null,
      "observacoes": []
    }
  ],
  "nao_reconhecidos": []
}
```

JSON reduzido (`--formato json --nivel reduzido`):

```json
{
  "metadados": {},
  "exames": [
    { "abreviacao": "HB", "valor": 11.2, "unidade": "g/dL", "limite": null }
  ]
}
```

## Personalizando o padrão

O catálogo em `blood_exam_transcriber/data/standard_catalog.json` é a fonte da verdade do "padrão" de transcrição. Para adicionar um novo exame ou ajustar nomes/unidades/faixas de referência padrão, edite (ou substitua via `--catalog`) esse arquivo — não é necessário alterar código.

## Testes

```bash
# Núcleo Python (biblioteca padrão)
python -m unittest discover -s tests -v

# Núcleo JavaScript da versão web (runner nativo do Node, sem dependências)
node --test tests/transcritor.test.mjs
```

A CI do GitHub (`.github/workflows/ci.yml`) roda os testes de Python
(3.9–3.12) e de JavaScript a cada push e pull request, garantindo que as
duas implementações permaneçam em paridade.
