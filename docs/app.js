// Camada de interface: liga o núcleo (transcritor.js) ao DOM.

import {
  transcrever, paraJson, paraRelatorio, fmtIntervalo, LAUDO_EXEMPLO,
  normalizarNome, CATALOGO, MODELOS,
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

let ultimoJson = "";
let ultimoTexto = "";
let modoAtual = "rapido"; // "rapido" | "texto"

// Lista de exames adicionados no modo de entrada rápida: { analito, valor }
let itensRapidos = [];

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

function adicionarModelo(chave) {
  const modelo = MODELOS.find((m) => m.chave === chave);
  if (!modelo) return;
  for (const analito of modelo.analitos) {
    if (!itensRapidos.some((it) => it.analito.codigoLoinc === analito.codigoLoinc)) {
      itensRapidos.push({ analito, valor: "" });
    }
  }
  renderItensRapidos();
  atualizar();
  mostrarToast(`Modelo "${modelo.nome}" adicionado`);
  const primeiroVazio = itensRapidos.find((it) => it.valor === "");
  const alvo = primeiroVazio || itensRapidos[itensRapidos.length - 1];
  const campo = itensRapidosEl.querySelector(
    `[data-codigo="${CSS.escape(alvo.analito.codigoLoinc)}"] .item-valor`
  );
  campo?.focus();
}

function removerItem(codigoLoinc) {
  itensRapidos = itensRapidos.filter((it) => it.analito.codigoLoinc !== codigoLoinc);
  renderItensRapidos();
  atualizar();
}

function renderItensRapidos() {
  if (!itensRapidos.length) {
    itensRapidosEl.innerHTML = `<p class="vazio">Nenhum exame adicionado ainda. Busque acima para começar.</p>`;
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
  const btn = ev.target.closest("[data-modelo]");
  if (!btn) return;
  adicionarModelo(btn.dataset.modelo);
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
  buscaExame.focus();
});
itensRapidosEl.addEventListener("click", (ev) => {
  const btn = ev.target.closest(".item-remover");
  if (!btn) return;
  const codigo = btn.closest(".item-rapido").dataset.codigo;
  removerItem(codigo);
});

// Estado inicial: modo de entrada rápida vazio; laudo de exemplo pronto no modo texto.
entrada.value = LAUDO_EXEMPLO;
atualizar();
