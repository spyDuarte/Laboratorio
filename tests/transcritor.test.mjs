// Testes do núcleo JavaScript (runner nativo do Node: `node --test`).
// Espelham os testes Python para garantir paridade das duas implementações.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import {
  transcrever, paraJson, CATALOGO,
  parseNumeroBr, normalizarNome, normalizarUnidade, parseLinha,
  identificarAnalito,
} from "../docs/transcritor.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const laudo = readFileSync(join(__dirname, "..", "exemplos", "exame_exemplo.txt"), "utf8");

test("números BR e internacionais", () => {
  assert.equal(parseNumeroBr("14,5"), 14.5);
  assert.equal(parseNumeroBr("7.200"), 7200);
  assert.equal(parseNumeroBr("250.000"), 250000);
  assert.equal(parseNumeroBr("14.5"), 14.5);
  assert.equal(parseNumeroBr("1.234,5"), 1234.5);
  assert.equal(parseNumeroBr("abc"), null);
});

test("normalização de nomes e unidades", () => {
  assert.equal(normalizarNome("Triglicerídeos"), "triglicerideos");
  assert.equal(normalizarNome("Ácido Úrico:"), "acido urico");
  assert.equal(normalizarUnidade("µUI/mL"), "uui/ml");
  assert.equal(normalizarUnidade("10^3/µL"), "10e3/ul");
  assert.equal(normalizarUnidade("/mm³"), "/mm3");
});

test("dígitos do nome/unidade não viram valor", () => {
  assert.equal(parseNumeroBr(parseLinha("Vitamina B12 .... 450 pg/mL").valorTexto), 450);
  assert.equal(parseLinha("Hemoglobina glicada (HbA1c) ... 5,4 %").valorTexto, "5,4");
  assert.equal(parseLinha("Leucócitos 7,2 10^3/µL").valorTexto, "7,2");
});

test("faixa de referência inline é ignorada", () => {
  assert.equal(parseNumeroBr(parseLinha("Glicose 92 mg/dL (70 - 99)").valorTexto), 92);
  assert.equal(parseLinha("Glicose 92 mg/dL (70 - 99)").unidadeOriginal, "mg/dL");
  assert.equal(parseNumeroBr(parseLinha("Creatinina 0,95 mg/dL [0,6 - 1,3]").valorTexto), 0.95);
});

test("identificação por sinônimo mais longo", () => {
  assert.equal(identificarAnalito("Colesterol HDL").nome, "Colesterol HDL");
  assert.equal(identificarAnalito("Colesterol Total").nome, "Colesterol total");
  assert.equal(identificarAnalito("Bilirrubina direta").nome, "Bilirrubina direta");
  assert.equal(identificarAnalito("Bilirrubina").nome, "Bilirrubina total");
  assert.equal(identificarAnalito("Exame desconhecido ABCXYZ"), null);
});

test("conversão de unidades e avaliação", () => {
  const glic = transcrever("Glicose 5 mmol/L").resultados[0];
  assert.ok(Math.abs(glic.valor - 90.09) < 0.02);
  const leuco = transcrever("Leucócitos 7,2 10^3/µL").resultados[0];
  assert.equal(leuco.valor, 7200);
  assert.equal(leuco.unidade, "/mm³");
  assert.equal(leuco.situacao, "normal");
  const ca = transcrever("Cálcio 2,4 mmol/L").resultados[0];
  assert.equal(ca.unidade, "mg/dL");
  assert.ok(Math.abs(ca.valor - 9.62) < 0.05);
});

test("situação frente à referência", () => {
  assert.equal(transcrever("Colesterol Total 210 mg/dL").resultados[0].situacao, "acima");
  assert.equal(transcrever("Colesterol HDL 38 mg/dL").resultados[0].situacao, "abaixo");
  assert.equal(transcrever("Creatinina 1,2 mg/dL", "M").resultados[0].situacao, "normal");
  assert.equal(transcrever("Creatinina 1,2 mg/dL", "F").resultados[0].situacao, "acima");
});

test("laudo completo: metadados, contagem e LOINC", () => {
  const t = transcrever(laudo, "M");
  assert.equal(t.metadados.paciente, "João da Silva");
  assert.equal(t.metadados.data_coleta, "10/07/2026");
  assert.equal(t.metadados.total_nao_reconhecidos, 0);
  assert.ok(t.metadados.total_reconhecidos >= 40);
  assert.ok(t.resultados.every((r) => r.codigo_loinc));
  const plaq = t.resultados.find((r) => r.analito === "Plaquetas");
  assert.equal(plaq.valor, 250000);
  // A saída JSON é sempre válida.
  assert.doesNotThrow(() => JSON.parse(paraJson(t)));
});

test("catálogo tem 47 analitos e códigos LOINC únicos por nome", () => {
  assert.equal(CATALOGO.length, 47);
  const nomes = new Set(CATALOGO.map((a) => a.nome));
  assert.equal(nomes.size, CATALOGO.length);
});
