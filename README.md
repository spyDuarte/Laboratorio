# Laboratorio

Ferramenta para **transcrever exames de sangue para um padrão canônico definido**, de duas formas: digitando os exames rapidamente (por busca e valor) ou colando o texto livre de um laudo. Devolve os resultados normalizados — nome padronizado, abreviação, código **LOINC**, valor, unidade, faixa de referência e situação (`baixo` / `normal` / `alto`) — em JSON ou texto, no nível **completo** ou **reduzido**.

Há duas implementações mantidas em paridade: um núcleo em **Python** (`transcritor/`, biblioteca + CLI) e um núcleo em **JavaScript** (`docs/`, a interface web que roda 100% no navegador, publicada via GitHub Pages).

## Como funciona

1. Um **catálogo canônico** (`transcritor/catalogo.py` e o espelho em `docs/transcritor.js`) define, para cada exame, o código LOINC, nome padronizado, abreviação, categoria, unidade, fatores de conversão de unidade, faixa de referência (inclusive por sexo) e os sinônimos reconhecidos em laudos.
2. O **parser** (`transcritor/parser.py`) varre o texto linha a linha, identifica exames pelo sinônimo (ignorando acentos e maiúsculas/minúsculas), extrai valor, unidade e faixa de referência informados no próprio laudo, converte para a unidade canônica quando necessário e calcula a situação do resultado.
3. O **transcritor** (`transcritor/transcritor.py`) monta a saída final, incluindo metadados simples do laudo (paciente, data, sexo), e exporta em JSON ou texto, no nível completo ou reduzido.

## Instalação

```bash
pip install -e .
```

Isso instala o pacote `transcritor` e o comando `transcritor`. Também é possível
rodar direto do repositório, sem instalar, via `python cli.py`.

## Uso via linha de comando

```bash
python cli.py exemplos/exame_exemplo.txt
python cli.py exemplos/exame_exemplo.txt --formato json --sexo M
cat laudo.txt | python cli.py --nivel reduzido
```

Ou, após instalado, usando o comando `transcritor` no lugar de `python cli.py`.

## Uso como biblioteca

```python
from transcritor import transcrever, para_json, para_relatorio

texto = open("exemplos/exame_exemplo.txt", encoding="utf-8").read()
transcricao = transcrever(texto, sexo="M")
print(para_relatorio(transcricao))            # relatório completo em texto
print(para_json(transcricao, formato="reduzido"))  # JSON reduzido
```

## Analitos suportados

| Categoria             | Exames |
|------------------------|--------|
| Hemograma              | Hemoglobina, Hematócrito, Eritrócitos, Leucócitos, Plaquetas, VCM, HCM, CHCM, RDW, Reticulócitos |
| Bioquímica             | Glicose, HbA1c, Ureia, Creatinina, Ácido úrico, Ferro sérico, LDH, CK/CPK, Amilase, Lipase, Homocisteína, Ácido fólico, Amônia, Lactato |
| Lipidograma            | Colesterol total, HDL, LDL, VLDL, Triglicerídeos |
| Função hepática        | AST (TGO), ALT (TGP), Gama GT, Fosfatase alcalina, Bilirrubina total/direta/indireta, Proteínas totais, Albumina |
| Eletrólitos            | Sódio, Potássio, Cloro, Cálcio, Magnésio, Fósforo |
| Coagulação             | INR, TTPA, Fibrinogênio, D-dímero |
| Marcadores cardíacos   | Troponina I, CK-MB, BNP |
| Tireoide               | TSH, T4 livre, T3 total |
| Hormônios              | Insulina, Peptídeo C, Cortisol, PTH |
| Marcadores tumorais    | PSA total, CEA, CA-125, CA 19-9, Alfafetoproteína (AFP) |
| Outros                 | Ferritina, Vitamina D (25-OH), Vitamina B12, PCR, VHS |

São **68 analitos** no total, cada um com uma **abreviação** curta (ex.:
Hemoglobina → `HB`, Colesterol total → `CT`, TGO → `TGO`), usada na entrada
rápida e no formato reduzido descritos abaixo, e um código **LOINC**
verificado individualmente contra a base oficial (loinc.org). O parser
ignora faixas de referência escritas na mesma linha entre parênteses ou
colchetes (ex.: `Glicose 92 mg/dL (70-99)`).

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
rápida** foi pensada para digitar o mais rápido possível, com várias formas
de adicionar exames:

- **Busca com autocompletar** por nome ou abreviação: digite, use **↑ / ↓**
  para navegar entre as sugestões e **Enter** para adicionar o exame
  realçado. No campo de valor, **Enter avança para o próximo exame ainda
  vazio** — dá para preencher uma lista inteira só com `valor Enter valor
  Enter…`, sem tocar no mouse.
- **Linha rápida**: digite tudo de uma vez, no formato `abreviação valor`,
  ex.: `hb 14 glic 92 ct 210 tgo 30`, e **Enter** adiciona todos de uma vez.
  Aceita limites (`pcr <5`) e nomes completos (`colesterol total 210`).
- **Modelos** (ver abaixo), incluindo modelos que você mesmo salva.

O seletor **Salvar como** alterna entre Completo e Reduzido, refletido na
tabela, no JSON e no texto exportados. A aba **Colar laudo** mantém o fluxo
original de colar um laudo em texto livre.

A lista de exames, os valores digitados e os modelos salvos ficam
**guardados no próprio navegador** (localStorage) — ao recarregar ou
reabrir a página, o trabalho continua de onde parou. Nada é enviado a
servidores. O botão **Limpar lista** recomeça do zero.

### Modelos pré-definidos e personalizados

Em vez de adicionar exame por exame, os botões **Modelos** preenchem a
entrada rápida com um painel de exames — bastando digitar os valores.
Já vêm dois painéis para condições crônicas:

- **HAS** (hipertensão): Glicose, Colesterol total, HDL, LDL,
  Triglicerídeos, Ácido úrico, Creatinina, Potássio, Sódio, TSH.
- **DM** (diabetes): Glicose, HbA1c, Colesterol total, HDL, LDL,
  Triglicerídeos, Creatinina, TSH, Insulina, Peptídeo C.

Com o botão **+ Salvar** você guarda a lista atual como um **modelo próprio**
(ex.: "Check-up", "Pré-operatório"), que passa a aparecer ao lado dos fixos e
pode ser reaplicado ou excluído a qualquer momento.

Os painéis fixos ficam em `docs/transcritor.js` (`MODELOS`), referenciando o
catálogo pelo código LOINC; os personalizados ficam no navegador do usuário.

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

O catálogo é a fonte da verdade do "padrão" de transcrição. Para adicionar um
novo exame ou ajustar nome/abreviação/unidade/faixa de referência, edite
`transcritor/catalogo.py` (Python) e o espelho em `docs/transcritor.js`
(JavaScript) — os testes verificam que os dois permaneçam em paridade. Os
modelos pré-definidos (HAS, DM) ficam em `MODELOS`, em `docs/transcritor.js`.

## Testes

```bash
# Núcleo Python (apenas biblioteca padrão, sem dependências externas)
python -m unittest discover -s tests -v

# Núcleo JavaScript da versão web (runner nativo do Node, sem dependências)
node --test tests/transcritor.test.mjs
```

A CI do GitHub (`.github/workflows/ci.yml`) roda os testes de Python
(3.9–3.12) e de JavaScript a cada push e pull request, garantindo que as
duas implementações permaneçam em paridade.
