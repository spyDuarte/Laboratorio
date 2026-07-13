"""Catálogo canônico de analitos.

Este é o "determinado padrão" para onde os exames são transcritos: cada
analito tem um nome canônico, código LOINC (padrão internacional de
observações laboratoriais), unidade canônica, sinônimos reconhecidos,
conversões de unidade e intervalos de referência para adultos.

Os intervalos de referência são valores gerais de orientação e NÃO
substituem os intervalos do laboratório emissor nem avaliação médica.
"""

from __future__ import annotations

from .modelos import Analito
from .texto import normalizar_nome, normalizar_unidade


def _mk(codigo, nome, categoria, unidade, sinonimos, conversoes=None, referencia=None,
        observacao=""):
    """Cria um Analito normalizando sinônimos e chaves de conversão."""
    sin = tuple(dict.fromkeys(normalizar_nome(s) for s in sinonimos))
    conv = {normalizar_unidade(u): f for u, f in (conversoes or {}).items()}
    return Analito(
        codigo_loinc=codigo,
        nome=nome,
        categoria=categoria,
        unidade=unidade,
        sinonimos=sin,
        conversoes=conv,
        referencia=referencia or {},
        observacao=observacao,
    )


# Fatores de conversão reutilizados.
_MMOLL_GLICOSE = 18.0182       # mmol/L -> mg/dL (glicose)
_MMOLL_COLEST = 38.67          # mmol/L -> mg/dL (colesterol/HDL/LDL)
_MMOLL_TRIG = 88.57            # mmol/L -> mg/dL (triglicerídeos)
_UMOLL_CREAT = 1 / 88.42       # µmol/L -> mg/dL (creatinina)
_MMOLL_UREIA = 6.006           # mmol/L -> mg/dL (ureia)


CATALOGO: list[Analito] = [
    # ---------------------------------------------------------------- Hemograma
    _mk("718-7", "Hemoglobina", "Hemograma", "g/dL",
        ["hemoglobina", "hb", "hgb"],
        conversoes={"g/l": 0.1},
        referencia={"geral": (12.0, 17.5), "M": (13.5, 17.5), "F": (12.0, 16.0)}),
    _mk("4544-3", "Hematócrito", "Hemograma", "%",
        ["hematocrito", "ht", "hct"],
        referencia={"geral": (36.0, 53.0), "M": (41.0, 53.0), "F": (36.0, 46.0)}),
    _mk("789-8", "Eritrócitos", "Hemograma", "milhões/mm³",
        ["eritrocitos", "hemacias", "hemaceas", "rbc", "serie vermelha"],
        conversoes={"10e6/ul": 1.0, "milhoes/mm3": 1.0, "10e12/l": 1.0,
                    "/mm3": 1e-6, "/ul": 1e-6},
        referencia={"geral": (4.0, 5.9), "M": (4.5, 5.9), "F": (4.0, 5.2)}),
    _mk("6690-2", "Leucócitos", "Hemograma", "/mm³",
        ["leucocitos", "wbc", "globulos brancos", "serie branca"],
        conversoes={"10e3/ul": 1000.0, "mil/mm3": 1000.0, "10e9/l": 1000.0,
                    "/mm3": 1.0, "/ul": 1.0},
        referencia={"geral": (4000.0, 11000.0)}),
    _mk("777-3", "Plaquetas", "Hemograma", "/mm³",
        ["plaquetas", "plt", "plaquetometria"],
        conversoes={"10e3/ul": 1000.0, "mil/mm3": 1000.0, "10e9/l": 1000.0,
                    "/mm3": 1.0, "/ul": 1.0},
        referencia={"geral": (150000.0, 450000.0)}),
    _mk("787-2", "VCM", "Hemograma", "fL",
        ["vcm", "volume corpuscular medio", "mcv"],
        referencia={"geral": (80.0, 100.0)}),
    _mk("785-6", "HCM", "Hemograma", "pg",
        ["hcm", "hemoglobina corpuscular media", "mch"],
        referencia={"geral": (27.0, 33.0)}),
    _mk("786-4", "CHCM", "Hemograma", "g/dL",
        ["chcm", "concentracao de hemoglobina corpuscular media", "mchc"],
        referencia={"geral": (32.0, 36.0)}),
    _mk("788-0", "RDW", "Hemograma", "%",
        ["rdw", "red cell distribution width"],
        referencia={"geral": (11.5, 14.5)}),

    # ------------------------------------------------------------- Bioquímica
    _mk("2345-7", "Glicose", "Bioquímica", "mg/dL",
        ["glicose", "glicemia", "glicemia de jejum", "glicose de jejum",
         "glicose em jejum"],
        conversoes={"mmol/l": _MMOLL_GLICOSE},
        referencia={"geral": (70.0, 99.0)}),
    _mk("4548-4", "Hemoglobina glicada (HbA1c)", "Bioquímica", "%",
        ["hemoglobina glicada", "hba1c", "hb glicada", "a1c",
         "hemoglobina glicosilada"],
        referencia={"geral": (4.0, 5.6)}),
    _mk("3094-0", "Ureia", "Bioquímica", "mg/dL",
        ["ureia", "uréia"],
        conversoes={"mmol/l": _MMOLL_UREIA},
        referencia={"geral": (15.0, 45.0)}),
    _mk("2160-0", "Creatinina", "Bioquímica", "mg/dL",
        ["creatinina"],
        conversoes={"umol/l": _UMOLL_CREAT},
        referencia={"geral": (0.6, 1.3), "M": (0.7, 1.3), "F": (0.6, 1.1)}),
    _mk("3084-1", "Ácido úrico", "Bioquímica", "mg/dL",
        ["acido urico", "urato"],
        referencia={"geral": (2.4, 7.0), "M": (3.4, 7.0), "F": (2.4, 6.0)}),
    _mk("2093-3", "Colesterol total", "Lipidograma", "mg/dL",
        ["colesterol total", "colesterol"],
        conversoes={"mmol/l": _MMOLL_COLEST},
        referencia={"geral": (None, 199.0)},
        observacao="Desejável < 200 mg/dL"),
    _mk("2085-9", "Colesterol HDL", "Lipidograma", "mg/dL",
        ["colesterol hdl", "hdl colesterol", "hdl", "hdl c"],
        conversoes={"mmol/l": _MMOLL_COLEST},
        referencia={"geral": (40.0, None)},
        observacao="Desejável > 40 mg/dL"),
    _mk("2089-1", "Colesterol LDL", "Lipidograma", "mg/dL",
        ["colesterol ldl", "ldl colesterol", "ldl", "ldl c"],
        conversoes={"mmol/l": _MMOLL_COLEST},
        referencia={"geral": (None, 129.0)},
        observacao="Desejável < 130 mg/dL"),
    _mk("2571-8", "Triglicerídeos", "Lipidograma", "mg/dL",
        ["triglicerideos", "triglicerides", "trigliceridios", "tg"],
        conversoes={"mmol/l": _MMOLL_TRIG},
        referencia={"geral": (None, 149.0)},
        observacao="Desejável < 150 mg/dL"),

    # ------------------------------------------------------------ Função hepática
    _mk("1920-8", "AST (TGO)", "Função hepática", "U/L",
        ["ast", "tgo", "aspartato aminotransferase", "transaminase oxalacetica"],
        referencia={"geral": (5.0, 40.0)}),
    _mk("1742-6", "ALT (TGP)", "Função hepática", "U/L",
        ["alt", "tgp", "alanina aminotransferase", "transaminase piruvica"],
        referencia={"geral": (7.0, 56.0)}),
    _mk("2324-2", "Gama GT (GGT)", "Função hepática", "U/L",
        ["gama gt", "gamagt", "ggt", "gama glutamil transferase",
         "gama glutamiltransferase"],
        referencia={"geral": (5.0, 61.0), "M": (8.0, 61.0), "F": (5.0, 36.0)}),
    _mk("6768-6", "Fosfatase alcalina", "Função hepática", "U/L",
        ["fosfatase alcalina", "fal", "alp"],
        referencia={"geral": (40.0, 129.0)}),
    _mk("1975-2", "Bilirrubina total", "Função hepática", "mg/dL",
        ["bilirrubina total", "bt bilirrubina", "bilirrubina"],
        referencia={"geral": (0.1, 1.2)}),

    # --------------------------------------------------------------- Eletrólitos
    _mk("2951-2", "Sódio", "Eletrólitos", "mmol/L",
        ["sodio", "na"],
        referencia={"geral": (135.0, 145.0)}),
    _mk("2823-3", "Potássio", "Eletrólitos", "mmol/L",
        ["potassio", "k"],
        referencia={"geral": (3.5, 5.1)}),

    # ----------------------------------------------------------------- Tireoide
    _mk("3016-3", "TSH", "Tireoide", "µUI/mL",
        ["tsh", "hormonio tireoestimulante", "tireotrofina"],
        referencia={"geral": (0.4, 4.0)}),
    _mk("3024-7", "T4 livre", "Tireoide", "ng/dL",
        ["t4 livre", "tiroxina livre", "ft4"],
        referencia={"geral": (0.8, 1.8)}),

    # ------------------------------------------------------- Vitaminas e outros
    _mk("2276-4", "Ferritina", "Outros", "ng/mL",
        ["ferritina"],
        referencia={"geral": (15.0, 400.0), "M": (30.0, 400.0), "F": (15.0, 150.0)}),
    _mk("1989-3", "Vitamina D (25-OH)", "Outros", "ng/mL",
        ["vitamina d", "vitamina d 25 oh", "25 oh vitamina d",
         "25 hidroxivitamina d", "25 hidroxi vitamina d", "vitamina d 25 hidroxi"],
        referencia={"geral": (30.0, 100.0)},
        observacao="Suficiência: 30-100 ng/mL"),
    _mk("2132-9", "Vitamina B12", "Outros", "pg/mL",
        ["vitamina b12", "b12", "cobalamina", "cianocobalamina"],
        referencia={"geral": (200.0, 900.0)}),
    _mk("1988-5", "Proteína C reativa (PCR)", "Outros", "mg/L",
        ["proteina c reativa", "pcr", "pcr ultrassensivel", "crp"],
        referencia={"geral": (None, 5.0)},
        observacao="Valores < 5 mg/L; > 3 mg/L indica risco cardiovascular"),
]


def _construir_indice() -> list[tuple[str, Analito]]:
    """Índice (sinonimo_normalizado, analito) ordenado do sinônimo mais
    longo para o mais curto, para que 'colesterol hdl' vença 'colesterol'."""
    pares: list[tuple[str, Analito]] = []
    for analito in CATALOGO:
        for sin in analito.sinonimos:
            pares.append((sin, analito))
    pares.sort(key=lambda p: len(p[0]), reverse=True)
    return pares


INDICE_SINONIMOS: list[tuple[str, Analito]] = _construir_indice()
