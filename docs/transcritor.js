// Transcritor de exames de sangue — núcleo em JavaScript (roda no navegador).
//
// Porte fiel do pacote Python `transcritor/` para uso 100% client-side,
// adequado ao GitHub Pages (sem servidor, sem dependências, sem build).
// Espelha: texto.py, catalogo.py, parser.py, normalizador.py,
// metadados.py e transcritor.py.

/* ------------------------------------------------------------------ texto */

export function removerAcentos(texto) {
  return texto.normalize("NFKD").replace(/[̀-ͯ]/g, "");
}

export function normalizarNome(texto) {
  let t = removerAcentos(texto).toLowerCase();
  t = t.replace(/[^a-z0-9]+/g, " ");
  t = t.replace(/\s+/g, " ").trim();
  return t;
}

export function normalizarUnidade(unidade) {
  if (!unidade) return "";
  let u = removerAcentos(unidade).toLowerCase().trim();
  u = u.replace(/µ/g, "u").replace(/μ/g, "u");
  u = u.replace(/×/g, "x");
  u = u.replace(/10\s*\^?\s*3/g, "10e3");
  u = u.replace(/10\s*\^?\s*6/g, "10e6");
  u = u.replace(/10\s*\^?\s*9/g, "10e9");
  u = u.replace(/10\s*\^?\s*12/g, "10e12");
  u = u.replace(/³/g, "3").replace(/²/g, "2");
  u = u.replace(/ /g, "");
  return u;
}

const NUM =
  "\\d{1,3}(?:\\.\\d{3})+(?:,\\d+)?" + // 250.000 / 1.234,5
  "|\\d+,\\d+" + // 14,5
  "|\\d+\\.\\d+" + // 14.5
  "|\\d+"; // 43

// Valor com marcador de limite opcional (<, >, ≤, ≥). Não pode estar colado
// a letra/dígito anterior nem fazer parte da notação científica da unidade.
const VALOR_RE = new RegExp(
  "(?<![A-Za-z0-9^³²])([<>≤≥]\\s*)?(" + NUM + ")(?![\\^³²\\d])",
  "g"
);

export function parseNumeroBr(texto) {
  if (texto == null) return null;
  let t = String(texto).trim().replace(/ /g, "");
  if (!t) return null;

  const temVirgula = t.includes(",");
  const qtdPontos = (t.match(/\./g) || []).length;

  if (temVirgula) {
    t = t.replace(/\./g, "").replace(",", ".");
  } else if (qtdPontos >= 2) {
    t = t.replace(/\./g, "");
  } else if (qtdPontos === 1) {
    const [inteiro, frac] = t.split(".");
    if (frac.length === 3) t = inteiro + frac;
  }
  const v = Number(t);
  return Number.isNaN(v) ? null : v;
}

/* ----------------------------------------------------------------- parser */

const REF_MARKERS = /valores? de referencia|referencia|vr|v\.?r\.?|intervalo/i;
const TRIM_LABEL = /^[\s.:;=…·\-–—]+|[\s.:;=…·\-–—]+$/g;
const TRIM_UNIT = /^[\s.;,:\-–—]+|[\s.;,:\-–—]+$/g;

function limparUnidade(bruto) {
  if (!bruto) return "";
  let corte = bruto.split(/[([]/)[0];
  corte = corte.split(REF_MARKERS)[0];
  corte = corte.replace(TRIM_UNIT, "");
  const tokens = corte.split(/\s+/).filter(Boolean);
  if (!tokens.length) return "";
  let unidade = tokens[0];
  if (tokens.length >= 2 && (unidade.endsWith("/") || tokens[1].startsWith("/"))) {
    unidade =
      tokens.length >= 3 && tokens[1] === "/"
        ? tokens.slice(0, 3).join("")
        : unidade + tokens[1];
  }
  return unidade.trim();
}

export function parseLinha(linha) {
  const matches = [...linha.matchAll(VALOR_RE)];
  if (!matches.length) return null;

  const m = matches[matches.length - 1];
  const limiteRaw = (m[1] || "").trim();
  let limite = null;
  if (limiteRaw) limite = "<≤".includes(limiteRaw[0]) ? "<" : ">";
  const valorTexto = m[2];

  const nome = linha.slice(0, m.index).replace(TRIM_LABEL, "");
  const resto = linha.slice(m.index + m[0].length);
  const unidade = limparUnidade(resto);

  if (!nome) return null;
  return {
    nomeOriginal: nome,
    valorTexto,
    limite,
    unidadeOriginal: unidade,
    linha: linha.trim(),
  };
}

export function parseTexto(texto) {
  const itens = [];
  for (const linha of texto.split(/\r?\n/)) {
    if (!linha.trim()) continue;
    const item = parseLinha(linha);
    if (item) itens.push(item);
  }
  return itens;
}

/* --------------------------------------------------------------- catálogo */

function mk(codigo, nome, categoria, unidade, sinonimos, conversoes, referencia, observacao) {
  const sin = [...new Set(sinonimos.map(normalizarNome))];
  const conv = {};
  for (const [u, f] of Object.entries(conversoes || {})) conv[normalizarUnidade(u)] = f;
  return {
    codigoLoinc: codigo,
    nome,
    categoria,
    unidade,
    sinonimos: sin,
    conversoes: conv,
    referencia: referencia || {},
    observacao: observacao || "",
  };
}

const MMOLL_GLICOSE = 18.0182;
const MMOLL_COLEST = 38.67;
const MMOLL_TRIG = 88.57;
const UMOLL_CREAT = 1 / 88.42;
const MMOLL_UREIA = 6.006;

export const CATALOGO = [
  // Hemograma
  mk("718-7", "Hemoglobina", "Hemograma", "g/dL", ["hemoglobina", "hb", "hgb"],
    { "g/l": 0.1 },
    { geral: [12.0, 17.5], M: [13.5, 17.5], F: [12.0, 16.0] }),
  mk("4544-3", "Hematócrito", "Hemograma", "%", ["hematocrito", "ht", "hct"], {},
    { geral: [36.0, 53.0], M: [41.0, 53.0], F: [36.0, 46.0] }),
  mk("789-8", "Eritrócitos", "Hemograma", "milhões/mm³",
    ["eritrocitos", "hemacias", "hemaceas", "rbc", "serie vermelha"],
    { "10e6/ul": 1.0, "milhoes/mm3": 1.0, "10e12/l": 1.0, "/mm3": 1e-6, "/ul": 1e-6 },
    { geral: [4.0, 5.9], M: [4.5, 5.9], F: [4.0, 5.2] }),
  mk("6690-2", "Leucócitos", "Hemograma", "/mm³",
    ["leucocitos", "wbc", "globulos brancos", "serie branca"],
    { "10e3/ul": 1000.0, "mil/mm3": 1000.0, "10e9/l": 1000.0, "/mm3": 1.0, "/ul": 1.0 },
    { geral: [4000.0, 11000.0] }),
  mk("777-3", "Plaquetas", "Hemograma", "/mm³", ["plaquetas", "plt", "plaquetometria"],
    { "10e3/ul": 1000.0, "mil/mm3": 1000.0, "10e9/l": 1000.0, "/mm3": 1.0, "/ul": 1.0 },
    { geral: [150000.0, 450000.0] }),
  mk("787-2", "VCM", "Hemograma", "fL", ["vcm", "volume corpuscular medio", "mcv"], {},
    { geral: [80.0, 100.0] }),
  mk("785-6", "HCM", "Hemograma", "pg", ["hcm", "hemoglobina corpuscular media", "mch"], {},
    { geral: [27.0, 33.0] }),
  mk("786-4", "CHCM", "Hemograma", "g/dL",
    ["chcm", "concentracao de hemoglobina corpuscular media", "mchc"], {},
    { geral: [32.0, 36.0] }),
  mk("788-0", "RDW", "Hemograma", "%", ["rdw", "red cell distribution width"], {},
    { geral: [11.5, 14.5] }),

  // Bioquímica
  mk("2345-7", "Glicose", "Bioquímica", "mg/dL",
    ["glicose", "glicemia", "glicemia de jejum", "glicose de jejum", "glicose em jejum"],
    { "mmol/l": MMOLL_GLICOSE }, { geral: [70.0, 99.0] }),
  mk("4548-4", "Hemoglobina glicada (HbA1c)", "Bioquímica", "%",
    ["hemoglobina glicada", "hba1c", "hb glicada", "a1c", "hemoglobina glicosilada"], {},
    { geral: [4.0, 5.6] }),
  mk("3094-0", "Ureia", "Bioquímica", "mg/dL", ["ureia", "uréia"],
    { "mmol/l": MMOLL_UREIA }, { geral: [15.0, 45.0] }),
  mk("2160-0", "Creatinina", "Bioquímica", "mg/dL", ["creatinina"],
    { "umol/l": UMOLL_CREAT }, { geral: [0.6, 1.3], M: [0.7, 1.3], F: [0.6, 1.1] }),
  mk("3084-1", "Ácido úrico", "Bioquímica", "mg/dL", ["acido urico", "urato"], {},
    { geral: [2.4, 7.0], M: [3.4, 7.0], F: [2.4, 6.0] }),
  mk("2093-3", "Colesterol total", "Lipidograma", "mg/dL",
    ["colesterol total", "colesterol"], { "mmol/l": MMOLL_COLEST },
    { geral: [null, 199.0] }, "Desejável < 200 mg/dL"),
  mk("2085-9", "Colesterol HDL", "Lipidograma", "mg/dL",
    ["colesterol hdl", "hdl colesterol", "hdl", "hdl c"], { "mmol/l": MMOLL_COLEST },
    { geral: [40.0, null] }, "Desejável > 40 mg/dL"),
  mk("2089-1", "Colesterol LDL", "Lipidograma", "mg/dL",
    ["colesterol ldl", "ldl colesterol", "ldl", "ldl c"], { "mmol/l": MMOLL_COLEST },
    { geral: [null, 129.0] }, "Desejável < 130 mg/dL"),
  mk("2571-8", "Triglicerídeos", "Lipidograma", "mg/dL",
    ["triglicerideos", "triglicerides", "trigliceridios", "tg"], { "mmol/l": MMOLL_TRIG },
    { geral: [null, 149.0] }, "Desejável < 150 mg/dL"),

  // Função hepática
  mk("1920-8", "AST (TGO)", "Função hepática", "U/L",
    ["ast", "tgo", "aspartato aminotransferase", "transaminase oxalacetica"], {},
    { geral: [5.0, 40.0] }),
  mk("1742-6", "ALT (TGP)", "Função hepática", "U/L",
    ["alt", "tgp", "alanina aminotransferase", "transaminase piruvica"], {},
    { geral: [7.0, 56.0] }),
  mk("2324-2", "Gama GT (GGT)", "Função hepática", "U/L",
    ["gama gt", "gamagt", "ggt", "gama glutamil transferase", "gama glutamiltransferase"], {},
    { geral: [5.0, 61.0], M: [8.0, 61.0], F: [5.0, 36.0] }),
  mk("6768-6", "Fosfatase alcalina", "Função hepática", "U/L",
    ["fosfatase alcalina", "fal", "alp"], {}, { geral: [40.0, 129.0] }),
  mk("1975-2", "Bilirrubina total", "Função hepática", "mg/dL",
    ["bilirrubina total", "bt bilirrubina", "bilirrubina"], {}, { geral: [0.1, 1.2] }),

  // Eletrólitos
  mk("2951-2", "Sódio", "Eletrólitos", "mmol/L", ["sodio", "na"], {},
    { geral: [135.0, 145.0] }),
  mk("2823-3", "Potássio", "Eletrólitos", "mmol/L", ["potassio", "k"], {},
    { geral: [3.5, 5.1] }),

  // Tireoide
  mk("3016-3", "TSH", "Tireoide", "µUI/mL",
    ["tsh", "hormonio tireoestimulante", "tireotrofina"], {}, { geral: [0.4, 4.0] }),
  mk("3024-7", "T4 livre", "Tireoide", "ng/dL", ["t4 livre", "tiroxina livre", "ft4"], {},
    { geral: [0.8, 1.8] }),

  // Outros
  mk("2276-4", "Ferritina", "Outros", "ng/mL", ["ferritina"], {},
    { geral: [15.0, 400.0], M: [30.0, 400.0], F: [15.0, 150.0] }),
  mk("1989-3", "Vitamina D (25-OH)", "Outros", "ng/mL",
    ["vitamina d", "vitamina d 25 oh", "25 oh vitamina d", "25 hidroxivitamina d",
      "25 hidroxi vitamina d", "vitamina d 25 hidroxi"], {},
    { geral: [30.0, 100.0] }, "Suficiência: 30-100 ng/mL"),
  mk("2132-9", "Vitamina B12", "Outros", "pg/mL",
    ["vitamina b12", "b12", "cobalamina", "cianocobalamina"], {}, { geral: [200.0, 900.0] }),
  mk("1988-5", "Proteína C reativa (PCR)", "Outros", "mg/L",
    ["proteina c reativa", "pcr", "pcr ultrassensivel", "crp"], {},
    { geral: [null, 5.0] }, "Valores < 5 mg/L; > 3 mg/L indica risco cardiovascular"),
];

const INDICE_SINONIMOS = [];
for (const analito of CATALOGO) {
  for (const sin of analito.sinonimos) INDICE_SINONIMOS.push([sin, analito]);
}
INDICE_SINONIMOS.sort((a, b) => b[0].length - a[0].length);

/* ----------------------------------------------------------- normalizador */

export function identificarAnalito(nomeOriginal) {
  const alvo = " " + normalizarNome(nomeOriginal) + " ";
  for (const [sinonimo, analito] of INDICE_SINONIMOS) {
    if (alvo.includes(" " + sinonimo + " ")) return analito;
  }
  return null;
}

function selecionarReferencia(analito, sexo) {
  const ref = analito.referencia;
  if (!ref || !Object.keys(ref).length) return null;
  if (sexo && ref[sexo.toUpperCase()]) return ref[sexo.toUpperCase()];
  return ref.geral || null;
}

function avaliarSituacao(valor, limite, intervalo) {
  if (valor == null) return "nao_reconhecido";
  if (intervalo == null) return "sem_referencia";
  const [minimo, maximo] = intervalo;
  if (limite === "<") {
    if (minimo != null && valor <= minimo) return "abaixo";
    return "normal";
  }
  if (limite === ">") {
    if (maximo != null && valor >= maximo) return "acima";
    return "normal";
  }
  if (minimo != null && valor < minimo) return "abaixo";
  if (maximo != null && valor > maximo) return "acima";
  return "normal";
}

function normalizarItem(item, sexo) {
  const analito = identificarAnalito(item.nomeOriginal);
  const valorOrigem = parseNumeroBr(item.valorTexto);
  const observacoes = [];

  if (analito == null) {
    return {
      analito: item.nomeOriginal.trim(),
      categoria: "Não catalogado",
      codigo_loinc: null,
      valor: valorOrigem,
      unidade: item.unidadeOriginal || null,
      situacao: "nao_reconhecido",
      intervalo_referencia: null,
      nome_original: item.nomeOriginal.trim(),
      valor_original: item.valorTexto,
      unidade_original: item.unidadeOriginal,
      limite: item.limite,
      observacoes: [],
    };
  }

  const unidadeNorm = normalizarUnidade(item.unidadeOriginal);
  const canonicaNorm = normalizarUnidade(analito.unidade);
  let valor = valorOrigem;

  if (valorOrigem != null && unidadeNorm) {
    if (unidadeNorm === canonicaNorm) {
      // já canônica
    } else if (unidadeNorm in analito.conversoes) {
      valor = valorOrigem * analito.conversoes[unidadeNorm];
      observacoes.push(`Convertido de ${item.unidadeOriginal} para ${analito.unidade}`);
    } else {
      observacoes.push(
        `Unidade '${item.unidadeOriginal}' não reconhecida; valor mantido sem conversão`
      );
    }
  } else if (valorOrigem != null && !unidadeNorm) {
    observacoes.push(`Unidade ausente; assumida a canônica (${analito.unidade})`);
  }

  if (valor != null) valor = Math.round(valor * 1e4) / 1e4;

  const intervalo = selecionarReferencia(analito, sexo);
  const unidadeFinalCanonica =
    !unidadeNorm || unidadeNorm === canonicaNorm || unidadeNorm in analito.conversoes;
  const situacao = unidadeFinalCanonica
    ? avaliarSituacao(valor, item.limite, intervalo)
    : "sem_referencia";

  if (analito.observacao) observacoes.push(analito.observacao);

  const intervaloDict =
    intervalo != null ? { minimo: intervalo[0], maximo: intervalo[1] } : null;

  return {
    analito: analito.nome,
    categoria: analito.categoria,
    codigo_loinc: analito.codigoLoinc,
    valor,
    unidade: analito.unidade,
    situacao,
    intervalo_referencia: intervaloDict,
    nome_original: item.nomeOriginal.trim(),
    valor_original: item.valorTexto,
    unidade_original: item.unidadeOriginal,
    limite: item.limite,
    observacoes,
  };
}

/* ---------------------------------------------------------------- metadados */

const CHAVES_META = {
  paciente: "paciente",
  nome: "paciente",
  "nome do paciente": "paciente",
  "data da coleta": "data_coleta",
  "data de coleta": "data_coleta",
  "data coleta": "data_coleta",
  coleta: "data_coleta",
  data: "data_coleta",
  laboratorio: "laboratorio",
  lab: "laboratorio",
  sexo: "sexo",
  genero: "sexo",
  medico: "medico",
  "medico requisitante": "medico",
  requisitante: "medico",
  convenio: "convenio",
};

function normalizarSexo(valor) {
  const m = valor.trim().match(/\b(masculino|feminino|m|f)\b/i);
  if (!m) return null;
  const inicial = m[1][0].toUpperCase();
  return inicial === "M" || inicial === "F" ? inicial : null;
}

function extrairMetadados(texto) {
  const metadados = {};
  const restantes = [];
  for (const linha of texto.split(/\r?\n/)) {
    if (!linha.includes(":")) {
      restantes.push(linha);
      continue;
    }
    const idx = linha.indexOf(":");
    const rotulo = linha.slice(0, idx);
    const valor = linha.slice(idx + 1).trim();
    const chave = CHAVES_META[normalizarNome(rotulo)];
    if (chave && valor) {
      if (chave === "sexo") {
        const sexo = normalizarSexo(valor);
        if (sexo) metadados[chave] = sexo;
      } else {
        metadados[chave] = valor;
      }
    } else {
      restantes.push(linha);
    }
  }
  return [metadados, restantes.join("\n")];
}

/* --------------------------------------------------------------- orquestração */

const ORDEM_CATEGORIAS = [
  "Hemograma", "Bioquímica", "Lipidograma", "Função hepática",
  "Eletrólitos", "Tireoide", "Outros", "Não catalogado",
];

const SIMBOLO_SITUACAO = {
  abaixo: "↓ BAIXO",
  acima: "↑ ALTO",
  normal: "normal",
  sem_referencia: "—",
  nao_reconhecido: "?",
};

export function transcrever(texto, sexo = null, metadados = null) {
  const [metaLaudo, corpo] = extrairMetadados(texto);
  if (sexo == null) sexo = metaLaudo.sexo || null;

  const itens = parseTexto(corpo);
  const resultados = [];
  const naoReconhecidos = [];

  for (const item of itens) {
    const r = normalizarItem(item, sexo);
    if (r.situacao === "nao_reconhecido") naoReconhecidos.push(item.linha);
    else resultados.push(r);
  }

  const ordemDe = (cat) => {
    const i = ORDEM_CATEGORIAS.indexOf(cat);
    return i === -1 ? ORDEM_CATEGORIAS.length : i;
  };
  resultados.sort((a, b) => {
    const oa = ordemDe(a.categoria), ob = ordemDe(b.categoria);
    if (oa !== ob) return oa - ob;
    return a.analito.localeCompare(b.analito, "pt");
  });

  const meta = { ...metaLaudo, ...(metadados || {}) };
  if (sexo && !("sexo" in meta)) meta.sexo = sexo;
  meta.total_reconhecidos = resultados.length;
  meta.total_nao_reconhecidos = naoReconhecidos.length;

  return { metadados: meta, resultados, nao_reconhecidos: naoReconhecidos };
}

export function paraJson(transcricao, indent = 2) {
  return JSON.stringify(
    {
      metadados: transcricao.metadados,
      resultados: transcricao.resultados,
      nao_reconhecidos: transcricao.nao_reconhecidos,
    },
    null,
    indent
  );
}

function fmtValor(valor) {
  if (valor == null) return "—";
  if (Number.isInteger(valor)) return String(valor);
  return String(valor);
}

export function fmtIntervalo(intervalo) {
  if (!intervalo) return "";
  const { minimo, maximo } = intervalo;
  if (minimo != null && maximo != null) return `${fmtValor(minimo)} - ${fmtValor(maximo)}`;
  if (minimo != null) return `> ${fmtValor(minimo)}`;
  if (maximo != null) return `< ${fmtValor(maximo)}`;
  return "";
}

export function paraRelatorio(transcricao) {
  const linhas = [];
  const barra = "=".repeat(64);
  linhas.push(barra);
  linhas.push("EXAME DE SANGUE — TRANSCRIÇÃO PADRONIZADA");
  linhas.push(barra);

  const meta = transcricao.metadados;
  const rotulos = {
    paciente: "Paciente", data_coleta: "Data Coleta",
    sexo: "Sexo", laboratorio: "Laboratorio",
  };
  for (const chave of ["paciente", "data_coleta", "sexo", "laboratorio"]) {
    if (chave in meta) linhas.push(`${rotulos[chave]}: ${meta[chave]}`);
  }
  linhas.push("");

  let categoriaAtual = null;
  for (const r of transcricao.resultados) {
    if (r.categoria !== categoriaAtual) {
      categoriaAtual = r.categoria;
      linhas.push(`[ ${categoriaAtual} ]`);
    }
    const limite = r.limite || "";
    const valor = `${limite}${fmtValor(r.valor)}`;
    const ref = fmtIntervalo(r.intervalo_referencia);
    const refTxt = ref ? `(ref: ${ref} ${r.unidade})` : "";
    const situacao = SIMBOLO_SITUACAO[r.situacao] || r.situacao;
    linhas.push(
      ("  " + r.analito.padEnd(32) + " " + valor.padStart(10) + " " +
        r.unidade.padEnd(8) + " " + situacao.padEnd(8) + " " + refTxt).replace(/\s+$/, "")
    );
  }
  linhas.push("");

  if (transcricao.nao_reconhecidos.length) {
    linhas.push("[ Itens não reconhecidos ]");
    for (const item of transcricao.nao_reconhecidos) linhas.push(`  ? ${item}`);
    linhas.push("");
  }

  linhas.push("-".repeat(64));
  linhas.push(
    `Reconhecidos: ${meta.total_reconhecidos || 0} | ` +
    `Não reconhecidos: ${meta.total_nao_reconhecidos || 0}`
  );
  linhas.push(
    "Intervalos de referência são orientativos e não substituem avaliação médica."
  );
  return linhas.join("\n");
}

export const LAUDO_EXEMPLO = `LABORATÓRIO CENTRAL DE ANÁLISES CLÍNICAS
Paciente: João da Silva
Data da coleta: 10/07/2026

HEMOGRAMA COMPLETO
Hemoglobina .................... 14,5 g/dL
Hematócrito .................... 43 %
Hemácias ...................... 4,80 milhões/mm³
Leucócitos .................... 7.200 /mm³
Plaquetas ..................... 250.000 /mm³
VCM ........................... 89 fL
HCM ........................... 30 pg
CHCM .......................... 33,5 g/dL
RDW ........................... 13,2 %

BIOQUÍMICA
Glicose de jejum .............. 92 mg/dL
Hemoglobina glicada (HbA1c) ... 5,4 %
Ureia ......................... 32 mg/dL
Creatinina .................... 0,95 mg/dL
Ácido úrico ................... 5,1 mg/dL

LIPIDOGRAMA
Colesterol Total .............. 210 mg/dL
Colesterol HDL ................ 38 mg/dL
Colesterol LDL ................ 142 mg/dL
Triglicerídeos ................ 180 mg/dL

FUNÇÃO HEPÁTICA
TGO (AST) ..................... 28 U/L
TGP (ALT) ..................... 35 U/L
Gama GT ....................... 45 U/L

TIREOIDE
TSH ........................... 2,1 µUI/mL
T4 livre ...................... 1,3 ng/dL

OUTROS
Vitamina D (25-OH) ............ 24 ng/mL
Vitamina B12 .................. 450 pg/mL
Ferritina ..................... 120 ng/mL
PCR ........................... < 5 mg/L`;
