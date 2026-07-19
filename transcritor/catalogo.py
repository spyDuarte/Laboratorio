"""Catálogo canônico de analitos.

Este é o "determinado padrão" para onde os exames são transcritos: cada
analito tem um nome canônico, abreviação curta (para entrada e exportação
rápidas), código LOINC (padrão internacional de observações laboratoriais),
unidade canônica, sinônimos reconhecidos, conversões de unidade e
intervalos de referência para adultos.

Os intervalos de referência são valores gerais de orientação e NÃO
substituem os intervalos do laboratório emissor nem avaliação médica.
"""

from __future__ import annotations

from .modelos import Analito
from .texto import normalizar_nome, normalizar_unidade


def _mk(codigo, abreviacao, nome, categoria, unidade, sinonimos, conversoes=None,
        referencia=None, observacao=""):
    """Cria um Analito normalizando sinônimos e chaves de conversão."""
    sin = tuple(dict.fromkeys(normalizar_nome(s) for s in sinonimos))
    conv = {normalizar_unidade(u): f for u, f in (conversoes or {}).items()}
    return Analito(
        codigo_loinc=codigo,
        nome=nome,
        abreviacao=abreviacao,
        categoria=categoria,
        unidade=unidade,
        sinonimos=sin,
        conversoes=conv,
        referencia=referencia or {},
        observacao=observacao,
    )


# Fatores de conversão reutilizados.
_MMOLL_GLICOSE = 18.0182       # mmol/L -> mg/dL (glicose)
_MMOLL_COLEST = 38.67          # mmol/L -> mg/dL (colesterol/HDL/LDL/VLDL)
_MMOLL_TRIG = 88.57            # mmol/L -> mg/dL (triglicerídeos)
_UMOLL_CREAT = 1 / 88.42       # µmol/L -> mg/dL (creatinina)
_MMOLL_UREIA = 6.006           # mmol/L -> mg/dL (ureia)
_MMOLL_CALCIO = 4.008          # mmol/L -> mg/dL (cálcio)
_MMOLL_MAGNESIO = 2.43         # mmol/L -> mg/dL (magnésio)
_MMOLL_FOSFORO = 3.097         # mmol/L -> mg/dL (fósforo)
_UMOLL_FERRO = 5.587           # µmol/L -> µg/dL (ferro)


CATALOGO: list[Analito] = [
    # ---------------------------------------------------------------- Hemograma
    _mk("718-7", "HB", "Hemoglobina", "Hemograma", "g/dL",
        ["hemoglobina", "hb", "hgb"],
        conversoes={"g/l": 0.1},
        referencia={"geral": (12.0, 17.5), "M": (13.5, 17.5), "F": (12.0, 16.0)}),
    _mk("4544-3", "HT", "Hematócrito", "Hemograma", "%",
        ["hematocrito", "ht", "hct"],
        referencia={"geral": (36.0, 53.0), "M": (41.0, 53.0), "F": (36.0, 46.0)}),
    _mk("789-8", "HM", "Eritrócitos", "Hemograma", "milhões/mm³",
        ["eritrocitos", "hemacias", "hemaceas", "rbc", "serie vermelha"],
        conversoes={"10e6/ul": 1.0, "milhoes/mm3": 1.0, "10e12/l": 1.0,
                    "/mm3": 1e-6, "/ul": 1e-6},
        referencia={"geral": (4.0, 5.9), "M": (4.5, 5.9), "F": (4.0, 5.2)}),
    _mk("6690-2", "LEUC", "Leucócitos", "Hemograma", "/mm³",
        ["leucocitos", "wbc", "globulos brancos", "serie branca"],
        conversoes={"10e3/ul": 1000.0, "mil/mm3": 1000.0, "10e9/l": 1000.0,
                    "/mm3": 1.0, "/ul": 1.0},
        referencia={"geral": (4000.0, 11000.0)}),
    _mk("777-3", "PLAQ", "Plaquetas", "Hemograma", "/mm³",
        ["plaquetas", "plt", "plaquetometria"],
        conversoes={"10e3/ul": 1000.0, "mil/mm3": 1000.0, "10e9/l": 1000.0,
                    "/mm3": 1.0, "/ul": 1.0},
        referencia={"geral": (150000.0, 450000.0)}),
    _mk("787-2", "VCM", "VCM", "Hemograma", "fL",
        ["vcm", "volume corpuscular medio", "mcv"],
        referencia={"geral": (80.0, 100.0)}),
    _mk("785-6", "HCM", "HCM", "Hemograma", "pg",
        ["hcm", "hemoglobina corpuscular media", "mch"],
        referencia={"geral": (27.0, 33.0)}),
    _mk("786-4", "CHCM", "CHCM", "Hemograma", "g/dL",
        ["chcm", "concentracao de hemoglobina corpuscular media", "mchc"],
        referencia={"geral": (32.0, 36.0)}),
    _mk("788-0", "RDW", "RDW", "Hemograma", "%",
        ["rdw", "red cell distribution width"],
        referencia={"geral": (11.5, 14.5)}),

    # ------------------------------------------------------------- Bioquímica
    _mk("2345-7", "GLIC", "Glicose", "Bioquímica", "mg/dL",
        ["glicose", "glicemia", "glicemia de jejum", "glicose de jejum",
         "glicose em jejum"],
        conversoes={"mmol/l": _MMOLL_GLICOSE},
        referencia={"geral": (70.0, 99.0)}),
    _mk("4548-4", "HBA1C", "Hemoglobina glicada (HbA1c)", "Bioquímica", "%",
        ["hemoglobina glicada", "hba1c", "hb glicada", "a1c",
         "hemoglobina glicosilada"],
        referencia={"geral": (4.0, 5.6)}),
    _mk("3094-0", "UR", "Ureia", "Bioquímica", "mg/dL",
        ["ureia", "uréia"],
        conversoes={"mmol/l": _MMOLL_UREIA},
        referencia={"geral": (15.0, 45.0)}),
    _mk("2160-0", "CREAT", "Creatinina", "Bioquímica", "mg/dL",
        ["creatinina"],
        conversoes={"umol/l": _UMOLL_CREAT},
        referencia={"geral": (0.6, 1.3), "M": (0.7, 1.3), "F": (0.6, 1.1)}),
    _mk("3084-1", "AU", "Ácido úrico", "Bioquímica", "mg/dL",
        ["acido urico", "urato"],
        referencia={"geral": (2.4, 7.0), "M": (3.4, 7.0), "F": (2.4, 6.0)}),
    _mk("2093-3", "CT", "Colesterol total", "Lipidograma", "mg/dL",
        ["colesterol total", "colesterol"],
        conversoes={"mmol/l": _MMOLL_COLEST},
        referencia={"geral": (None, 199.0)},
        observacao="Desejável < 200 mg/dL"),
    _mk("2085-9", "HDL", "Colesterol HDL", "Lipidograma", "mg/dL",
        ["colesterol hdl", "hdl colesterol", "hdl", "hdl c"],
        conversoes={"mmol/l": _MMOLL_COLEST},
        referencia={"geral": (40.0, None)},
        observacao="Desejável > 40 mg/dL"),
    _mk("2089-1", "LDL", "Colesterol LDL", "Lipidograma", "mg/dL",
        ["colesterol ldl", "ldl colesterol", "ldl", "ldl c"],
        conversoes={"mmol/l": _MMOLL_COLEST},
        referencia={"geral": (None, 129.0)},
        observacao="Desejável < 130 mg/dL"),
    _mk("2571-8", "TG", "Triglicerídeos", "Lipidograma", "mg/dL",
        ["triglicerideos", "triglicerides", "trigliceridios", "tg"],
        conversoes={"mmol/l": _MMOLL_TRIG},
        referencia={"geral": (None, 149.0)},
        observacao="Desejável < 150 mg/dL"),
    _mk("13458-5", "VLDL", "Colesterol VLDL", "Lipidograma", "mg/dL",
        ["colesterol vldl", "vldl colesterol", "vldl"],
        conversoes={"mmol/l": _MMOLL_COLEST},
        referencia={"geral": (None, 30.0)},
        observacao="Desejável < 30 mg/dL"),

    # ------------------------------------------------------------ Função hepática
    _mk("1920-8", "TGO", "AST (TGO)", "Função hepática", "U/L",
        ["ast", "tgo", "aspartato aminotransferase", "transaminase oxalacetica"],
        referencia={"geral": (5.0, 40.0)}),
    _mk("1742-6", "TGP", "ALT (TGP)", "Função hepática", "U/L",
        ["alt", "tgp", "alanina aminotransferase", "transaminase piruvica"],
        referencia={"geral": (7.0, 56.0)}),
    _mk("2324-2", "GGT", "Gama GT (GGT)", "Função hepática", "U/L",
        ["gama gt", "gamagt", "ggt", "gama glutamil transferase",
         "gama glutamiltransferase"],
        referencia={"geral": (5.0, 61.0), "M": (8.0, 61.0), "F": (5.0, 36.0)}),
    _mk("6768-6", "FA", "Fosfatase alcalina", "Função hepática", "U/L",
        ["fosfatase alcalina", "fal", "alp"],
        referencia={"geral": (40.0, 129.0)}),
    _mk("1975-2", "BT", "Bilirrubina total", "Função hepática", "mg/dL",
        ["bilirrubina total", "bt bilirrubina", "bilirrubina"],
        referencia={"geral": (0.1, 1.2)}),
    _mk("1968-7", "BD", "Bilirrubina direta", "Função hepática", "mg/dL",
        ["bilirrubina direta", "bd bilirrubina", "bilirrubina conjugada"],
        referencia={"geral": (0.0, 0.3)}),
    _mk("1971-1", "BI", "Bilirrubina indireta", "Função hepática", "mg/dL",
        ["bilirrubina indireta", "bi bilirrubina", "bilirrubina nao conjugada"],
        referencia={"geral": (0.1, 0.8)}),
    _mk("2885-2", "PT", "Proteínas totais", "Função hepática", "g/dL",
        ["proteinas totais", "proteina total", "proteinas totais e fracoes"],
        referencia={"geral": (6.0, 8.3)}),
    _mk("1751-7", "ALB", "Albumina", "Função hepática", "g/dL",
        ["albumina", "alb"],
        referencia={"geral": (3.5, 5.2)}),

    # --------------------------------------------------------------- Eletrólitos
    _mk("2951-2", "NA", "Sódio", "Eletrólitos", "mmol/L",
        ["sodio", "na"],
        referencia={"geral": (135.0, 145.0)}),
    _mk("2823-3", "K", "Potássio", "Eletrólitos", "mmol/L",
        ["potassio", "k"],
        referencia={"geral": (3.5, 5.1)}),
    _mk("2075-0", "CL", "Cloro", "Eletrólitos", "mmol/L",
        ["cloro", "cloreto"],
        referencia={"geral": (98.0, 107.0)}),
    _mk("17861-6", "CA", "Cálcio total", "Eletrólitos", "mg/dL",
        ["calcio", "calcio total", "ca"],
        conversoes={"mmol/l": _MMOLL_CALCIO},
        referencia={"geral": (8.5, 10.5)}),
    _mk("2601-3", "MG", "Magnésio", "Eletrólitos", "mg/dL",
        ["magnesio", "mg"],
        conversoes={"mmol/l": _MMOLL_MAGNESIO},
        referencia={"geral": (1.6, 2.6)}),
    _mk("2777-1", "P", "Fósforo", "Eletrólitos", "mg/dL",
        ["fosforo", "fosforo inorganico", "fosfato"],
        conversoes={"mmol/l": _MMOLL_FOSFORO},
        referencia={"geral": (2.5, 4.5)}),
    _mk("2498-4", "FE", "Ferro sérico", "Bioquímica", "µg/dL",
        ["ferro serico", "ferro"],
        conversoes={"umol/l": _UMOLL_FERRO},
        referencia={"geral": (50.0, 175.0), "M": (65.0, 175.0), "F": (50.0, 170.0)}),
    _mk("2532-0", "LDH", "Desidrogenase láctica (LDH)", "Bioquímica", "U/L",
        ["desidrogenase latica", "lactato desidrogenase", "ldh", "dhl"],
        referencia={"geral": (120.0, 246.0)}),
    _mk("2157-6", "CK", "Creatinoquinase (CK/CPK)", "Bioquímica", "U/L",
        ["creatinoquinase", "creatina quinase", "creatinofosfoquinase", "cpk", "ck"],
        referencia={"geral": (26.0, 308.0), "M": (39.0, 308.0), "F": (26.0, 192.0)}),
    _mk("1798-8", "AMI", "Amilase", "Bioquímica", "U/L",
        ["amilase"],
        referencia={"geral": (28.0, 100.0)}),
    _mk("3040-3", "LIP", "Lipase", "Bioquímica", "U/L",
        ["lipase"],
        referencia={"geral": (13.0, 60.0)}),

    # ----------------------------------------------------------------- Tireoide
    _mk("3016-3", "TSH", "TSH", "Tireoide", "µUI/mL",
        ["tsh", "hormonio tireoestimulante", "tireotrofina"],
        referencia={"geral": (0.4, 4.0)}),
    _mk("3024-7", "T4L", "T4 livre", "Tireoide", "ng/dL",
        ["t4 livre", "tiroxina livre", "ft4"],
        referencia={"geral": (0.8, 1.8)}),
    _mk("3053-6", "T3", "T3 total", "Tireoide", "ng/dL",
        ["t3", "t3 total", "triiodotironina"],
        referencia={"geral": (80.0, 200.0)}),

    # ------------------------------------------------------- Vitaminas e outros
    _mk("2276-4", "FERR", "Ferritina", "Outros", "ng/mL",
        ["ferritina"],
        referencia={"geral": (15.0, 400.0), "M": (30.0, 400.0), "F": (15.0, 150.0)}),
    _mk("1989-3", "VITD", "Vitamina D (25-OH)", "Outros", "ng/mL",
        ["vitamina d", "vitamina d 25 oh", "25 oh vitamina d",
         "25 hidroxivitamina d", "25 hidroxi vitamina d", "vitamina d 25 hidroxi"],
        referencia={"geral": (30.0, 100.0)},
        observacao="Suficiência: 30-100 ng/mL"),
    _mk("2132-9", "B12", "Vitamina B12", "Outros", "pg/mL",
        ["vitamina b12", "b12", "cobalamina", "cianocobalamina"],
        referencia={"geral": (200.0, 900.0)}),
    _mk("1988-5", "PCR", "Proteína C reativa (PCR)", "Outros", "mg/L",
        ["proteina c reativa", "pcr", "pcr ultrassensivel", "crp"],
        referencia={"geral": (None, 5.0)},
        observacao="Valores < 5 mg/L; > 3 mg/L indica risco cardiovascular"),
    _mk("30341-2", "VHS", "VHS", "Outros", "mm/h",
        ["vhs", "velocidade de hemossedimentacao", "hemossedimentacao", "vsg"],
        referencia={"geral": (None, 20.0)},
        observacao="Referência varia por idade e sexo"),
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
