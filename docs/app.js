// Camada de interface: liga o núcleo (transcritor.js) ao DOM.

import {
  transcrever, paraJson, paraRelatorio, fmtIntervalo, LAUDO_EXEMPLO,
  normalizarNome,
} from "./transcritor.js";

const $ = (sel) => document.querySelector(sel);

const entrada = $("#entrada");
const sexoSel = $("#sexo");
const meta = $("#meta");
const resumo = $("#resumo");
const vistaTabela = $("#vista-tabela");
const jsonSaida = $("#json-saida");
const textoSaida = $("#texto-saida");
const toast = $("#toast");

let ultimoJson = "";
let ultimoTexto = "";

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

function renderTabela(t) {
  if (!t.resultados.length && !t.nao_reconhecidos.length) {
    vistaTabela.innerHTML = `<p class="vazio">Cole um laudo para ver a transcrição.</p>`;
    return;
  }

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

  if (t.nao_reconhecidos.length) {
    html += `<div class="nao-reconhecidos"><strong>Itens não reconhecidos</strong>` +
      ` (não estão no catálogo ou não puderam ser interpretados):<ul>` +
      t.nao_reconhecidos.map((i) => `<li>${esc(i)}</li>`).join("") + `</ul></div>`;
  }

  vistaTabela.innerHTML = html;
}

function atualizar() {
  const texto = entrada.value;
  const sexo = sexoSel.value || null;
  const t = transcrever(texto, sexo);

  ultimoJson = paraJson(t);
  ultimoTexto = paraRelatorio(t);

  renderMeta(t.metadados);
  renderResumo(t);
  renderTabela(t);
  jsonSaida.textContent = ultimoJson;
  textoSaida.textContent = ultimoTexto;
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
  const nome = qual === "json" ? "exame-transcrito.json" : "exame-transcrito.txt";
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
  document.querySelectorAll(".aba").forEach((b) =>
    b.classList.toggle("ativa", b.dataset.vista === vista));
  for (const v of ["tabela", "json", "texto"]) {
    $(`#vista-${v}`).classList.toggle("oculto", v !== vista);
  }
}

let debounce;
entrada.addEventListener("input", () => {
  clearTimeout(debounce);
  debounce = setTimeout(atualizar, 250);
});
sexoSel.addEventListener("change", atualizar);
$("#btn-transcrever").addEventListener("click", atualizar);
$("#btn-exemplo").addEventListener("click", () => {
  entrada.value = LAUDO_EXEMPLO;
  atualizar();
});
$("#btn-limpar").addEventListener("click", () => {
  entrada.value = "";
  atualizar();
});

document.querySelectorAll(".aba").forEach((b) =>
  b.addEventListener("click", () => trocarVista(b.dataset.vista)));
document.querySelectorAll("[data-copiar]").forEach((b) =>
  b.addEventListener("click", () => copiar(b.dataset.copiar)));
document.querySelectorAll("[data-baixar]").forEach((b) =>
  b.addEventListener("click", () => baixar(b.dataset.baixar)));

// Estado inicial: carrega o laudo de exemplo.
entrada.value = LAUDO_EXEMPLO;
atualizar();
