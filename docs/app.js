// Camada de interface: liga o núcleo (transcritor.js) ao DOM.

import {
  transcrever, paraJson, paraRelatorio, fmtIntervalo, LAUDO_EXEMPLO,
  normalizarNome, identificarAnalito, CATALOGO, MODELOS,
} from "./transcritor.js";

const $ = (sel) => document.querySelector(sel);

const entrada = $("#entrada");
const sexoSel = $("#sexo");
const nivelSel = $("#nivel");
const meta = $("#meta");
const resumo = $("#resumo");
const vistaTabela = $("#vista-tabela");
const jsonSaida = $("#json-saida");
const textoSaida = $("#texto-saida");
const toast = $("#toast");
const buscaExame = $("#busca-exame");
const sugestoesEl = $("#sugestoes");
const itensRapidosEl = $("#itens-rapidos");
const modelosEl = $("#modelos");
const modelosBotoesEl = $("#modelos-botoes");
const linhaRapida = $("#linha-rapida");
const itensAcoesEl = $("#itens-acoes");

// Índices para resolver exames por código LOINC ou por abreviação.
const PORLOINC = new Map(CATALOGO.map((a) => [a.codigoLoinc, a]));
const PORABREV = new Map(CATALOGO.map((a) => [normalizarNome(a.abreviacao), a]));

const CHAVE_ESTADO = "laboratorio.estado.v1";
const CHAVE_MODELOS = "laboratorio.modelos.v1";

let ultimoJson = "";
let ultimoTexto = "";
let modoAtual = "rapido"; // "rapido" | "texto"

// Lista de exames adicionados no modo de entrada rápida: { analito, valor }
let itensRapidos = [];

// Modelos personalizados salvos pelo usuário: [{ nome, codigos: [loinc] }]
let modelosCustom = [];

// Índice da sugestão realçada (navegação por setas) na lista atual.
let sugestaoAtivaIdx = -1;

const SITUACAO = {
  normal: { rotulo: "Normal", cls: "ok" },
  abaixo: { rotulo: "↓ Baixo", cls: "baixo" },
  acima: { rotulo: "↑ Alto", cls: "alto" },
  sem_referencia: { rotulo: "—", cls: "neutro" },
};

const ROTULO_META = {
  paciente: "Paciente", data_coleta: "Coleta", sexo: "Sexo",
  laboratorio: "Laboratório", medico: "Médico", convenio: "Convênio",
};

function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function fmtNumero(v) {
  if (v == null) return "—";
  return v.toLocaleString("pt-BR", { maximumFractionDigits: 4 });
}

function renderMeta(m) {
  const chips = [];
  for (const chave of ["paciente", "data_coleta", "laboratorio", "medico", "convenio", "sexo"]) {
    if (chave in m && chave !== "total_reconhecidos") {
      let valor = m[chave];
      if (chave === "sexo") valor = valor === "M" ? "Masculino" : valor === "F" ? "Feminino" : valor;
      chips.push(`<span class="chip">${esc(ROTULO_META[chave])}: <strong>${esc(valor)}</strong></span>`);
    }
  }
  meta.innerHTML = chips.join("");
}

function renderResumo(t) {
  const m = t.metadados;
  resumo.innerHTML =
    `<span><strong>${m.total_reconhecidos}</strong> reconhecido(s), ` +
    `<strong>${m.total_nao_reconhecidos}</strong> não reconhecido(s)</span>` +
    `<span class="legenda"><span class="ponto ok"></span>normal</span>` +
    `<span class="legenda"><span class="ponto baixo"></span>abaixo</span>` +
    `<span class="legenda"><span class="ponto alto"></span>acima</span>`;
}

function renderTabelaCompleta(t) {
  let html = "";
  let categoriaAtual = null;
  let abriu = false;

  for (const r of t.resultados) {
    if (r.categoria !== categoriaAtual) {
      if (abriu) html += `</tbody></table></div></div>`;
      categoriaAtual = r.categoria;
      html += `<div class="cat"><h3>${esc(categoriaAtual)}</h3><div class="tabela-wrap">` +
        `<table><thead><tr><th>Exame</th><th class="num">Resultado</th>` +
        `<th>Situação</th><th>Referência</th><th>LOINC</th></tr></thead><tbody>`;
      abriu = true;
    }
    const s = SITUACAO[r.situacao] || SITUACAO.sem_referencia;
    const ref = fmtIntervalo(r.intervalo_referencia);
    const refTxt = ref ? `${esc(ref)} <span class="loinc">${esc(r.unidade)}</span>` : "—";
    const mostraOrig =
      normalizarNome(r.nome_original) !== normalizarNome(r.analito);
    const orig = mostraOrig ? `<span class="exame-orig">laudo: ${esc(r.nome_original)}</span>` : "";
    const limite = r.limite || "";
    html +=
      `<tr><td><span class="exame-nome">${esc(r.analito)}</span>${orig}</td>` +
      `<td class="num">${esc(limite)}${fmtNumero(r.valor)} ${esc(r.unidade)}</td>` +
      `<td><span class="badge ${s.cls}">${esc(s.rotulo)}</span></td>` +
      `<td>${refTxt}</td>` +
      `<td class="loinc">${esc(r.codigo_loinc || "—")}</td></tr>`;
  }
  if (abriu) html += `</tbody></table></div></div>`;
  return html;
}

function renderTabelaReduzida(t) {
  let html = "";
  let categoriaAtual = null;
  let abriu = false;

  for (const r of t.resultados) {
    if (r.categoria !== categoriaAtual) {
      if (abriu) html += `</tbody></table></div></div>`;
      categoriaAtual = r.categoria;
      html += `<div class="cat"><h3>${esc(categoriaAtual)}</h3><div class="tabela-wrap">` +
        `<table><thead><tr><th>Abrev.</th><th class="num">Resultado</th></tr></thead><tbody>`;
      abriu = true;
    }
    const limite = r.limite || "";
    html +=
      `<tr><td><span class="exame-nome">${esc((r.abreviacao || r.analito).toUpperCase())}</span></td>` +
      `<td class="num">${esc(limite)}${fmtNumero(r.valor)} ${esc(r.unidade)}</td></tr>`;
  }
  if (abriu) html += `</tbody></table></div></div>`;
  return html;
}

function renderTabela(t, nivel) {
  if (!t.resultados.length && !t.nao_reconhecidos.length) {
    vistaTabela.innerHTML = `<p class="vazio">${
      modoAtual === "rapido"
        ? "Adicione exames acima para ver a transcrição."
        : "Cole um laudo para ver a transcrição."
    }</p>`;
    return;
  }

  let html = nivel === "reduzido" ? renderTabelaReduzida(t) : renderTabelaCompleta(t);

  if (t.nao_reconhecidos.length) {
    html += `<div class="nao-reconhecidos"><strong>Itens não reconhecidos</strong>` +
      ` (não estão no catálogo ou não puderam ser interpretados):<ul>` +
      t.nao_reconhecidos.map((i) => `<li>${esc(i)}</li>`).join("") + `</ul></div>`;
  }

  vistaTabela.innerHTML = html;
}

/* ---- geração do texto-fonte a partir do modo ativo ---- */

function textoDoModoRapido() {
  return itensRapidos
    .filter((it) => it.valor.trim() !== "")
    .map((it) => `${it.analito.nome}: ${it.valor.trim()} ${it.analito.unidade}`)
    .join("\n");
}

function atualizar() {
  const texto = modoAtual === "rapido" ? textoDoModoRapido() : entrada.value;
  const sexo = sexoSel.value || null;
  const nivel = nivelSel.value;
  const t = transcrever(texto, sexo);

  ultimoJson = paraJson(t, nivel);
  ultimoTexto = paraRelatorio(t, nivel);

  renderMeta(t.metadados);
  renderResumo(t);
  renderTabela(t, nivel);
  jsonSaida.textContent = ultimoJson;
  textoSaida.textContent = ultimoTexto;
  salvarEstado();
}

/* ---- persistência local (localStorage) ---- */

function salvarEstado() {
  try {
    localStorage.setItem(CHAVE_ESTADO, JSON.stringify({
      itens: itensRapidos.map((it) => ({ c: it.analito.codigoLoinc, v: it.valor })),
      texto: entrada.value,
      sexo: sexoSel.value,
      nivel: nivelSel.value,
      modo: modoAtual,
    }));
  } catch { /* localStorage indisponível (ex.: modo privado) — segue sem salvar */ }
}

function restaurarEstado() {
  let dados = null;
  try { dados = JSON.parse(localStorage.getItem(CHAVE_ESTADO) || "null"); } catch { dados = null; }
  if (!dados) {
    entrada.value = LAUDO_EXEMPLO;
    return;
  }
  itensRapidos = (dados.itens || [])
    .map(({ c, v }) => {
      const analito = PORLOINC.get(c);
      return analito ? { analito, valor: v || "" } : null;
    })
    .filter(Boolean);
  entrada.value = dados.texto != null ? dados.texto : LAUDO_EXEMPLO;
  if (dados.sexo) sexoSel.value = dados.sexo;
  if (dados.nivel) nivelSel.value = dados.nivel;
  if (dados.modo) modoAtual = dados.modo;
}

function carregarModelosCustom() {
  try { modelosCustom = JSON.parse(localStorage.getItem(CHAVE_MODELOS) || "[]") || []; }
  catch { modelosCustom = []; }
}

function salvarModelosCustom() {
  try { localStorage.setItem(CHAVE_MODELOS, JSON.stringify(modelosCustom)); } catch { /* ignora */ }
}

/* ---- linha rápida: "hb 14 glic 92 ct 210" -> lista de exames ---- */

function resolverAnalito(nome) {
  return PORABREV.get(normalizarNome(nome)) || identificarAnalito(nome) || null;
}

function parseLinhaRapida(texto) {
  const tokens = (texto || "").trim().split(/\s+/).filter(Boolean);
  const encontrados = [];
  const naoReconhecidos = [];
  let buffer = [];

  const fecharBuffer = (valor) => {
    const nome = buffer.join(" ");
    buffer = [];
    if (!nome) {
      if (valor != null) naoReconhecidos.push(valor);
      return;
    }
    const analito = resolverAnalito(nome);
    if (analito) encontrados.push({ analito, valor: valor == null ? "" : valor });
    else naoReconhecidos.push(nome);
  };

  for (const tok of tokens) {
    if (/^[<>≤≥]?\d/.test(tok)) fecharBuffer(tok);
    else buffer.push(tok);
  }
  if (buffer.length) fecharBuffer(null); // nome ao final sem valor: adiciona vazio para preencher

  return { encontrados, naoReconhecidos };
}

function aplicarLinhaRapida() {
  const { encontrados, naoReconhecidos } = parseLinhaRapida(linhaRapida.value);
  if (!encontrados.length && !naoReconhecidos.length) return;

  for (const { analito, valor } of encontrados) {
    const item = itensRapidos.find((it) => it.analito.codigoLoinc === analito.codigoLoinc);
    if (item) { if (valor) item.valor = valor; }
    else itensRapidos.push({ analito, valor });
  }
  renderItensRapidos();
  atualizar();
  linhaRapida.value = "";

  let msg = `${encontrados.length} exame(s) adicionado(s)`;
  if (naoReconhecidos.length) msg += ` · não reconhecido(s): ${naoReconhecidos.join(", ")}`;
  mostrarToast(msg);

  focarPrimeiroValorVazio();
}

function focarPrimeiroValorVazio() {
  const alvo = itensRapidos.find((it) => it.valor === "") || itensRapidos[itensRapidos.length - 1];
  if (!alvo) return;
  const campo = itensRapidosEl.querySelector(
    `[data-codigo="${CSS.escape(alvo.analito.codigoLoinc)}"] .item-valor`
  );
  campo?.focus();
}

/* ---- modo de entrada rápida ---- */

function pontuarAnalito(analito, q) {
  const abrev = normalizarNome(analito.abreviacao);
  const nome = normalizarNome(analito.nome);
  if (abrev === q) return 0;
  if (abrev.startsWith(q)) return 1;
  if (nome.startsWith(q)) return 2;
  if (analito.sinonimos.some((s) => s.startsWith(q))) return 3;
  const alvo = [abrev, nome, ...analito.sinonimos];
  if (alvo.some((s) => s.includes(q))) return 4;
  return null;
}

function buscarAnalitos(consulta) {
  const q = normalizarNome(consulta);
  if (!q) return [];
  const pontuados = [];
  for (const analito of CATALOGO) {
    const pontos = pontuarAnalito(analito, q);
    if (pontos != null) pontuados.push([pontos, analito]);
  }
  pontuados.sort((a, b) => a[0] - b[0]);
  return pontuados.slice(0, 8).map(([, analito]) => analito);
}

function renderSugestoes(lista, ativaIdx = 0) {
  if (!lista.length) {
    sugestoesEl.classList.add("oculto");
    sugestoesEl.innerHTML = "";
    sugestoesEl._lista = [];
    sugestaoAtivaIdx = -1;
    return;
  }
  sugestaoAtivaIdx = Math.min(Math.max(ativaIdx, 0), lista.length - 1);
  sugestoesEl.innerHTML = lista
    .map((a, i) => `<button type="button" class="sugestao${i === sugestaoAtivaIdx ? " ativa" : ""}" ` +
      `data-idx="${i}" role="option" aria-selected="${i === sugestaoAtivaIdx}">` +
      `<span class="sugestao-abrev">${esc(a.abreviacao)}</span>` +
      `<span class="sugestao-nome">${esc(a.nome)}</span>` +
      `<span class="sugestao-cat">${esc(a.categoria)}</span></button>`)
    .join("");
  sugestoesEl.classList.remove("oculto");
  sugestoesEl._lista = lista;
  sugestoesEl.querySelector(".sugestao.ativa")?.scrollIntoView({ block: "nearest" });
}

function moverSugestaoAtiva(delta) {
  const lista = sugestoesEl._lista || [];
  if (!lista.length) return;
  const novoIdx = (sugestaoAtivaIdx + delta + lista.length) % lista.length;
  renderSugestoes(lista, novoIdx);
}

function adicionarItem(analito) {
  let item = itensRapidos.find((it) => it.analito.codigoLoinc === analito.codigoLoinc);
  if (!item) {
    item = { analito, valor: "" };
    itensRapidos.push(item);
  }
  renderItensRapidos();
  buscaExame.value = "";
  renderSugestoes([]);
  const campo = itensRapidosEl.querySelector(`[data-codigo="${CSS.escape(analito.codigoLoinc)}"] .item-valor`);
  campo?.focus();
}

function adicionarExames(analitos, nomeModelo) {
  for (const analito of analitos) {
    if (analito && !itensRapidos.some((it) => it.analito.codigoLoinc === analito.codigoLoinc)) {
      itensRapidos.push({ analito, valor: "" });
    }
  }
  renderItensRapidos();
  atualizar();
  if (nomeModelo) mostrarToast(`Modelo "${nomeModelo}" adicionado`);
  focarPrimeiroValorVazio();
}

function adicionarModelo(chave) {
  const modelo = MODELOS.find((m) => m.chave === chave);
  if (modelo) adicionarExames(modelo.analitos, modelo.nome);
}

function adicionarModeloCustom(nome) {
  const modelo = modelosCustom.find((m) => m.nome === nome);
  if (modelo) adicionarExames(modelo.codigos.map((c) => PORLOINC.get(c)), modelo.nome);
}

function salvarModeloAtual() {
  if (!itensRapidos.length) {
    mostrarToast("Adicione exames antes de salvar um modelo");
    return;
  }
  const nome = (prompt("Nome do modelo (ex.: Check-up, Pré-operatório):") || "").trim();
  if (!nome) return;
  const codigos = itensRapidos.map((it) => it.analito.codigoLoinc);
  const existente = modelosCustom.find((m) => m.nome === nome);
  if (existente) existente.codigos = codigos;
  else modelosCustom.push({ nome, codigos });
  salvarModelosCustom();
  renderModelos();
  mostrarToast(`Modelo "${nome}" salvo`);
}

function excluirModeloCustom(nome) {
  modelosCustom = modelosCustom.filter((m) => m.nome !== nome);
  salvarModelosCustom();
  renderModelos();
}

function renderModelos() {
  const fixos = MODELOS.map((m) =>
    `<button type="button" class="btn btn-sec" data-modelo="${esc(m.chave)}" ` +
    `title="${esc(m.nome)}">${esc(m.chave)}</button>`).join("");
  const custom = modelosCustom.map((m) =>
    `<span class="modelo-custom">` +
    `<button type="button" class="btn btn-sec" data-modelo-custom="${esc(m.nome)}">${esc(m.nome)}</button>` +
    `<button type="button" class="modelo-del" data-del-modelo="${esc(m.nome)}" ` +
    `aria-label="Excluir modelo ${esc(m.nome)}" title="Excluir modelo">×</button></span>`).join("");
  modelosBotoesEl.innerHTML = fixos + custom;
}

function limparItens() {
  if (!itensRapidos.length) return;
  itensRapidos = [];
  renderItensRapidos();
  atualizar();
}

function removerItem(codigoLoinc) {
  itensRapidos = itensRapidos.filter((it) => it.analito.codigoLoinc !== codigoLoinc);
  renderItensRapidos();
  atualizar();
}

function renderItensRapidos() {
  itensAcoesEl?.classList.toggle("oculto", !itensRapidos.length);
  if (!itensRapidos.length) {
    itensRapidosEl.innerHTML = `<p class="vazio">Nenhum exame adicionado ainda. Busque, use a linha rápida ou escolha um modelo.</p>`;
    salvarEstado();
    return;
  }
  itensRapidosEl.innerHTML = itensRapidos.map((it) => `
    <div class="item-rapido" data-codigo="${esc(it.analito.codigoLoinc)}">
      <span class="item-nome">${esc(it.analito.nome)} <span class="item-abrev">${esc(it.analito.abreviacao)}</span></span>
      <input class="item-valor" inputmode="decimal" autocomplete="off"
        placeholder="valor" value="${esc(it.valor)}" />
      <span class="item-unidade">${esc(it.analito.unidade)}</span>
      <button class="item-remover" type="button" aria-label="Remover ${esc(it.analito.nome)}">×</button>
    </div>
  `).join("");
  salvarEstado();
}

/* ---- interações ---- */

function mostrarToast(msg) {
  toast.textContent = msg;
  toast.classList.remove("oculto");
  clearTimeout(mostrarToast._t);
  mostrarToast._t = setTimeout(() => toast.classList.add("oculto"), 1800);
}

async function copiar(qual) {
  const conteudo = qual === "json" ? ultimoJson : ultimoTexto;
  try {
    await navigator.clipboard.writeText(conteudo);
    mostrarToast("Copiado para a área de transferência");
  } catch {
    mostrarToast("Não foi possível copiar");
  }
}

function baixar(qual) {
  const conteudo = qual === "json" ? ultimoJson : ultimoTexto;
  const nivel = nivelSel.value;
  const sufixo = nivel === "reduzido" ? "-reduzido" : "";
  const nome = qual === "json" ? `exame${sufixo}.json` : `exame${sufixo}.txt`;
  const tipo = qual === "json" ? "application/json" : "text/plain";
  const blob = new Blob([conteudo], { type: `${tipo};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nome;
  a.click();
  URL.revokeObjectURL(url);
}

function trocarVista(vista) {
  document.querySelectorAll("[data-vista]").forEach((b) =>
    b.classList.toggle("ativa", b.dataset.vista === vista));
  for (const v of ["tabela", "json", "texto"]) {
    $(`#vista-${v}`).classList.toggle("oculto", v !== vista);
  }
}

function trocarModo(modo) {
  modoAtual = modo;
  document.querySelectorAll("[data-modo]").forEach((b) =>
    b.classList.toggle("ativa", b.dataset.modo === modo));
  $("#modo-rapido").classList.toggle("oculto", modo !== "rapido");
  $("#modo-texto").classList.toggle("oculto", modo !== "texto");
  atualizar();
}

let debounce;
entrada.addEventListener("input", () => {
  clearTimeout(debounce);
  debounce = setTimeout(atualizar, 250);
});
sexoSel.addEventListener("change", atualizar);
nivelSel.addEventListener("change", atualizar);
$("#btn-exemplo").addEventListener("click", () => {
  entrada.value = LAUDO_EXEMPLO;
  atualizar();
});
$("#btn-limpar").addEventListener("click", () => {
  entrada.value = "";
  atualizar();
});

document.querySelectorAll("[data-vista]").forEach((b) =>
  b.addEventListener("click", () => trocarVista(b.dataset.vista)));
document.querySelectorAll("[data-modo]").forEach((b) =>
  b.addEventListener("click", () => trocarModo(b.dataset.modo)));
document.querySelectorAll("[data-copiar]").forEach((b) =>
  b.addEventListener("click", () => copiar(b.dataset.copiar)));
document.querySelectorAll("[data-baixar]").forEach((b) =>
  b.addEventListener("click", () => baixar(b.dataset.baixar)));

buscaExame.addEventListener("input", () => {
  renderSugestoes(buscarAnalitos(buscaExame.value));
});
buscaExame.addEventListener("keydown", (ev) => {
  const lista = sugestoesEl._lista || [];
  if (ev.key === "ArrowDown") {
    if (!lista.length) return;
    ev.preventDefault();
    moverSugestaoAtiva(1);
  } else if (ev.key === "ArrowUp") {
    if (!lista.length) return;
    ev.preventDefault();
    moverSugestaoAtiva(-1);
  } else if (ev.key === "Enter") {
    ev.preventDefault();
    if (lista.length) adicionarItem(lista[Math.max(sugestaoAtivaIdx, 0)]);
  } else if (ev.key === "Escape") {
    renderSugestoes([]);
  }
});
sugestoesEl.addEventListener("click", (ev) => {
  const btn = ev.target.closest(".sugestao");
  if (!btn) return;
  const lista = sugestoesEl._lista || [];
  const analito = lista[Number(btn.dataset.idx)];
  if (analito) adicionarItem(analito);
});
sugestoesEl.addEventListener("mousemove", (ev) => {
  const btn = ev.target.closest(".sugestao");
  if (!btn) return;
  const idx = Number(btn.dataset.idx);
  if (idx !== sugestaoAtivaIdx) renderSugestoes(sugestoesEl._lista, idx);
});
document.addEventListener("click", (ev) => {
  if (!ev.target.closest(".rapido-busca")) renderSugestoes([]);
});

modelosEl?.addEventListener("click", (ev) => {
  const fixo = ev.target.closest("[data-modelo]");
  const custom = ev.target.closest("[data-modelo-custom]");
  const del = ev.target.closest("[data-del-modelo]");
  const salvar = ev.target.closest("#btn-salvar-modelo");
  if (del) excluirModeloCustom(del.dataset.delModelo);
  else if (custom) adicionarModeloCustom(custom.dataset.modeloCustom);
  else if (fixo) adicionarModelo(fixo.dataset.modelo);
  else if (salvar) salvarModeloAtual();
});

linhaRapida?.addEventListener("keydown", (ev) => {
  if (ev.key !== "Enter") return;
  ev.preventDefault();
  aplicarLinhaRapida();
});

itensAcoesEl?.addEventListener("click", (ev) => {
  if (ev.target.closest("#btn-limpar-rapido")) limparItens();
});

itensRapidosEl.addEventListener("input", (ev) => {
  if (!ev.target.classList.contains("item-valor")) return;
  const linha = ev.target.closest(".item-rapido");
  const codigo = linha.dataset.codigo;
  const item = itensRapidos.find((it) => it.analito.codigoLoinc === codigo);
  if (item) item.valor = ev.target.value;
  clearTimeout(debounce);
  debounce = setTimeout(atualizar, 200);
});
itensRapidosEl.addEventListener("keydown", (ev) => {
  if (ev.key !== "Enter" || !ev.target.classList.contains("item-valor")) return;
  ev.preventDefault();
  atualizar();
  // Enter avança para o próximo campo de valor ainda vazio (ideal para modelos);
  // se não houver, volta para a busca para adicionar mais exames.
  const campos = [...itensRapidosEl.querySelectorAll(".item-valor")];
  const idx = campos.indexOf(ev.target);
  const proximoVazio = campos.slice(idx + 1).find((c) => c.value.trim() === "");
  if (proximoVazio) proximoVazio.focus();
  else buscaExame.focus();
});
itensRapidosEl.addEventListener("click", (ev) => {
  const btn = ev.target.closest(".item-remover");
  if (!btn) return;
  const codigo = btn.closest(".item-rapido").dataset.codigo;
  removerItem(codigo);
});

// Estado inicial: restaura a sessão anterior (localStorage) ou carrega o exemplo.
carregarModelosCustom();
restaurarEstado();
renderModelos();
renderItensRapidos();
document.querySelectorAll("[data-modo]").forEach((b) =>
  b.classList.toggle("ativa", b.dataset.modo === modoAtual));
$("#modo-rapido").classList.toggle("oculto", modoAtual !== "rapido");
$("#modo-texto").classList.toggle("oculto", modoAtual !== "texto");
atualizar();
