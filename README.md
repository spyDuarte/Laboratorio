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

O projeto tem duas frentes que compartilham a mesma lógica:

- **Aplicação web** (`docs/`) — roda 100% no navegador, pronta para o
  **GitHub Pages**. Cole o laudo e veja a transcrição na hora; nada é enviado
  a servidores.
- **Pacote Python + CLI** (`transcritor/`, `cli.py`) — para uso em scripts,
  automações e processamento em lote.

## Aplicação web (GitHub Pages)

A pasta [`docs/`](docs/) contém um site estático (HTML + CSS + JavaScript,
sem dependências e sem build). A lógica de transcrição foi portada de Python
para JavaScript em [`docs/transcritor.js`](docs/transcritor.js).

**Como publicar no GitHub Pages** (escolha uma opção):

1. **GitHub Actions (recomendado):** em `Settings > Pages`, defina
   *Source: GitHub Actions*. O workflow
   [`.github/workflows/pages.yml`](.github/workflows/pages.yml) publica a
   pasta `docs/` a cada push na branch padrão. O site fica em
   `https://<usuario>.github.io/<repositorio>/`.
2. **Deploy a partir de uma branch:** em `Settings > Pages`, defina
   *Source: Deploy from a branch*, branch `main`, pasta `/docs`.

**Rodar localmente:**

```bash
cd docs
python -m http.server 8000
# abra http://localhost:8000
```

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
| Bioquímica       | Glicose, HbA1c, Ureia, Creatinina, Ácido úrico, Ferro sérico, LDH, CK/CPK, Amilase, Lipase |
| Lipidograma      | Colesterol total, HDL, LDL, VLDL, Triglicerídeos |
| Função hepática  | AST (TGO), ALT (TGP), Gama GT, Fosfatase alcalina, Bilirrubina total/direta/indireta, Proteínas totais, Albumina |
| Eletrólitos      | Sódio, Potássio, Cloro, Cálcio, Magnésio, Fósforo |
| Tireoide         | TSH, T4 livre, T3 total |
| Outros           | Ferritina, Vitamina D (25-OH), Vitamina B12, PCR, VHS |

São **47 analitos** no total. O parser ignora faixas de referência escritas
na mesma linha entre parênteses ou colchetes (ex.: `Glicose 92 mg/dL (70-99)`).

Novos exames são adicionados incluindo uma entrada em
[`transcritor/catalogo.py`](transcritor/catalogo.py).

## Estrutura do projeto

```
docs/                # aplicação web (GitHub Pages)
  index.html
  style.css
  app.js             # interface (DOM)
  transcritor.js     # núcleo portado de Python para JavaScript
transcritor/         # pacote Python (mesma lógica)
  catalogo.py        # catálogo canônico (LOINC, unidades, sinônimos, referências)
  parser.py          # extrai (rótulo, valor, unidade) de cada linha do laudo
  normalizador.py    # casa com o catálogo, converte unidades, avalia referência
  metadados.py       # extrai cabeçalho (paciente, data, sexo...)
  texto.py           # normalização de texto/número/unidade
  transcritor.py     # orquestração e formatação (JSON / relatório)
  modelos.py         # dataclasses
cli.py               # interface de linha de comando
exemplos/            # laudo de exemplo
tests/               # testes (unittest, biblioteca padrão)
.github/workflows/   # CI (testes) e deploy do GitHub Pages
```

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
