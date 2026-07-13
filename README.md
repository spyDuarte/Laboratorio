# Laboratório — Transcritor de Exames de Sangue

Ferramenta em Python que lê o **texto livre de laudos de exames de sangue**
(como os emitidos por diferentes laboratórios) e o transcreve para um
**padrão canônico único**, ancorado nos códigos **LOINC** — o padrão
internacional para observações laboratoriais.

O objetivo é resolver um problema real: cada laboratório escreve o mesmo
exame de um jeito ("Hemácias", "Eritrócitos", "RBC"), com unidades
diferentes ("/mm³", "10³/µL") e formatação numérica variada ("7.200",
"14,5"). O transcritor normaliza tudo isso para nomes, unidades e códigos
padronizados, avalia cada valor contra intervalos de referência e emite uma
saída estruturada (JSON) ou um relatório de texto padronizado.

> ⚠️ **Aviso:** os intervalos de referência são orientativos e **não
> substituem** os intervalos do laboratório emissor nem avaliação médica.

## O que ele faz

- **Reconhece analitos** por sinônimos (PT-BR e siglas): `Hemoglobina`/`Hb`,
  `TGO`/`AST`, `Colesterol HDL`/`HDL`, `HbA1c`/`Hemoglobina glicada`, etc.
- **Interpreta números** no formato brasileiro (`14,5`, `250.000`) e
  internacional (`14.5`).
- **Converte unidades** quando há equivalência definida (ex.: glicose em
  `mmol/L` → `mg/dL`, leucócitos em `10³/µL` → `/mm³`).
- **Classifica** cada resultado como `normal`, `abaixo` ou `acima` do
  intervalo de referência (com faixas específicas por sexo quando aplicável).
- **Extrai metadados** do cabeçalho (paciente, data da coleta, laboratório,
  sexo).
- **Emite** JSON padronizado ou relatório de texto agrupado por categoria.

## Padrão de saída

Cada resultado transcrito segue esta estrutura:

```json
{
  "analito": "Hemoglobina",
  "categoria": "Hemograma",
  "codigo_loinc": "718-7",
  "valor": 14.5,
  "unidade": "g/dL",
  "situacao": "normal",
  "intervalo_referencia": { "minimo": 13.5, "maximo": 17.5 },
  "nome_original": "Hemoglobina",
  "valor_original": "14,5",
  "unidade_original": "g/dL",
  "limite": null,
  "observacoes": []
}
```

## Uso

Não há dependências externas — apenas a biblioteca padrão do Python (3.9+).

### Linha de comando

```bash
# Relatório de texto padronizado
python cli.py exemplos/exame_exemplo.txt

# Saída JSON, informando o sexo (para escolher intervalos de referência)
python cli.py exemplos/exame_exemplo.txt --formato json --sexo M

# Lendo da entrada padrão
cat laudo.txt | python cli.py --sexo F

# Gravando em arquivo
python cli.py laudo.txt --formato json --saida resultado.json
```

### Como biblioteca

```python
from transcritor import transcrever, para_json, para_relatorio

laudo = """
Hemoglobina: 14,5 g/dL
Glicose de jejum: 92 mg/dL
Colesterol Total: 210 mg/dL
"""

t = transcrever(laudo, sexo="M")
print(para_relatorio(t))   # relatório legível
print(para_json(t))        # JSON padronizado

for r in t.resultados:
    print(r.analito, r.codigo_loinc, r.valor, r.unidade, r.situacao)
```

## Analitos suportados

| Categoria        | Exames |
|------------------|--------|
| Hemograma        | Hemoglobina, Hematócrito, Eritrócitos, Leucócitos, Plaquetas, VCM, HCM, CHCM, RDW |
| Bioquímica       | Glicose, HbA1c, Ureia, Creatinina, Ácido úrico |
| Lipidograma      | Colesterol total, HDL, LDL, Triglicerídeos |
| Função hepática  | AST (TGO), ALT (TGP), Gama GT, Fosfatase alcalina, Bilirrubina total |
| Eletrólitos      | Sódio, Potássio |
| Tireoide         | TSH, T4 livre |
| Outros           | Ferritina, Vitamina D (25-OH), Vitamina B12, PCR |

Novos exames são adicionados incluindo uma entrada em
[`transcritor/catalogo.py`](transcritor/catalogo.py).

## Estrutura do projeto

```
transcritor/
  catalogo.py      # catálogo canônico (LOINC, unidades, sinônimos, referências)
  parser.py        # extrai (rótulo, valor, unidade) de cada linha do laudo
  normalizador.py  # casa com o catálogo, converte unidades, avalia referência
  metadados.py     # extrai cabeçalho (paciente, data, sexo...)
  texto.py         # normalização de texto/número/unidade
  transcritor.py   # orquestração e formatação (JSON / relatório)
  modelos.py       # dataclasses
cli.py             # interface de linha de comando
exemplos/          # laudo de exemplo
tests/             # testes (unittest, biblioteca padrão)
```

## Testes

```bash
python -m unittest discover -s tests -v
```

A CI do GitHub (`.github/workflows/ci.yml`) roda os testes em Python
3.9–3.12 a cada push e pull request.
