"""Testes do transcritor de exames de sangue (stdlib unittest)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transcritor import transcrever, para_json, para_relatorio, reduzir  # noqa: E402
from transcritor.catalogo import CATALOGO  # noqa: E402
from transcritor.texto import (  # noqa: E402
    parse_numero_br, normalizar_nome, normalizar_unidade,
)
from transcritor.parser import parse_linha  # noqa: E402
from transcritor.normalizador import identificar_analito  # noqa: E402


class TestNumeroBR(unittest.TestCase):
    def test_decimal_virgula(self):
        self.assertEqual(parse_numero_br("14,5"), 14.5)

    def test_milhar_ponto(self):
        self.assertEqual(parse_numero_br("7.200"), 7200.0)
        self.assertEqual(parse_numero_br("250.000"), 250000.0)

    def test_decimal_ponto(self):
        self.assertEqual(parse_numero_br("14.5"), 14.5)
        self.assertEqual(parse_numero_br("0.95"), 0.95)

    def test_milhar_e_decimal(self):
        self.assertEqual(parse_numero_br("1.234,5"), 1234.5)

    def test_inteiro(self):
        self.assertEqual(parse_numero_br("43"), 43.0)

    def test_invalido(self):
        self.assertIsNone(parse_numero_br("abc"))
        self.assertIsNone(parse_numero_br(""))


class TestNormalizacao(unittest.TestCase):
    def test_nome_sem_acento(self):
        self.assertEqual(normalizar_nome("Triglicerídeos"), "triglicerideos")
        self.assertEqual(normalizar_nome("Ácido Úrico:"), "acido urico")

    def test_unidade(self):
        self.assertEqual(normalizar_unidade("mg/dL"), "mg/dl")
        self.assertEqual(normalizar_unidade("µUI/mL"), "uui/ml")
        self.assertEqual(normalizar_unidade("10^3/µL"), "10e3/ul")
        self.assertEqual(normalizar_unidade("/mm³"), "/mm3")


class TestParserLinha(unittest.TestCase):
    def test_valor_simples(self):
        item = parse_linha("Hemoglobina: 14,5 g/dL")
        self.assertEqual(item.valor_texto, "14,5")
        self.assertEqual(item.unidade_original, "g/dL")
        self.assertIn("hemoglobina", item.nome_original.lower())

    def test_digitos_no_nome_nao_viram_valor(self):
        # 'B12' não deve ser lido como valor 12; o valor é 450.
        item = parse_linha("Vitamina B12 .................. 450 pg/mL")
        self.assertEqual(parse_numero_br(item.valor_texto), 450.0)

    def test_hba1c(self):
        item = parse_linha("Hemoglobina glicada (HbA1c) ... 5,4 %")
        self.assertEqual(item.valor_texto, "5,4")
        self.assertEqual(item.unidade_original, "%")

    def test_limite(self):
        item = parse_linha("PCR ........................... < 5 mg/L")
        self.assertEqual(item.limite, "<")
        self.assertEqual(parse_numero_br(item.valor_texto), 5.0)

    def test_linha_sem_numero(self):
        self.assertIsNone(parse_linha("Observação clínica sem valor."))

    def test_faixa_referencia_inline_ignorada(self):
        # O valor medido é 92; os números do intervalo (70-99) são ignorados.
        item = parse_linha("Glicose 92 mg/dL (70 - 99)")
        self.assertEqual(parse_numero_br(item.valor_texto), 92.0)
        self.assertEqual(item.unidade_original, "mg/dL")

    def test_faixa_referencia_colchetes(self):
        item = parse_linha("Creatinina 0,95 mg/dL [0,6 - 1,3]")
        self.assertEqual(parse_numero_br(item.valor_texto), 0.95)


class TestIdentificacao(unittest.TestCase):
    def test_hdl_vence_colesterol(self):
        a = identificar_analito("Colesterol HDL")
        self.assertEqual(a.nome, "Colesterol HDL")

    def test_colesterol_total(self):
        a = identificar_analito("Colesterol Total")
        self.assertEqual(a.nome, "Colesterol total")

    def test_sinonimo_tgo(self):
        a = identificar_analito("TGO (AST)")
        self.assertEqual(a.codigo_loinc, "1920-8")

    def test_desconhecido(self):
        self.assertIsNone(identificar_analito("Exame desconhecido ABCXYZ"))

    def test_bilirrubina_direta_vence_total(self):
        # 'bilirrubina' (sinônimo de total) não deve capturar 'Bilirrubina direta'.
        self.assertEqual(identificar_analito("Bilirrubina direta").nome, "Bilirrubina direta")
        self.assertEqual(identificar_analito("Bilirrubina total").nome, "Bilirrubina total")
        self.assertEqual(identificar_analito("Bilirrubina").nome, "Bilirrubina total")

    def test_novos_analitos(self):
        casos = {
            "Albumina": "Albumina",
            "Cálcio": "Cálcio total",
            "Magnésio": "Magnésio",
            "Ferro sérico": "Ferro sérico",
            "VHS": "VHS",
            "Colesterol VLDL": "Colesterol VLDL",
        }
        for rotulo, esperado in casos.items():
            self.assertEqual(identificar_analito(rotulo).nome, esperado, rotulo)


class TestConversaoEReferencia(unittest.TestCase):
    def test_conversao_glicose_mmol(self):
        t = transcrever("Glicose 5 mmol/L")
        r = t.resultados[0]
        self.assertEqual(r.unidade, "mg/dL")
        self.assertAlmostEqual(r.valor, 90.09, places=1)

    def test_leucocitos_10e3(self):
        # 7.2 10^3/µL deve virar 7200 /mm³
        t = transcrever("Leucócitos 7,2 10^3/µL")
        r = t.resultados[0]
        self.assertEqual(r.valor, 7200.0)
        self.assertEqual(r.unidade, "/mm³")
        self.assertEqual(r.situacao, "normal")

    def test_situacao_alto(self):
        t = transcrever("Colesterol Total 210 mg/dL")
        self.assertEqual(t.resultados[0].situacao, "acima")

    def test_situacao_baixo_hdl(self):
        t = transcrever("Colesterol HDL 38 mg/dL")
        self.assertEqual(t.resultados[0].situacao, "abaixo")

    def test_referencia_por_sexo(self):
        # Creatinina 1,2 é normal para M (0,7-1,3) e alto para F (0,6-1,1).
        tm = transcrever("Creatinina 1,2 mg/dL", sexo="M")
        tf = transcrever("Creatinina 1,2 mg/dL", sexo="F")
        self.assertEqual(tm.resultados[0].situacao, "normal")
        self.assertEqual(tf.resultados[0].situacao, "acima")

    def test_conversao_calcio_mmol(self):
        # 2,4 mmol/L de cálcio ≈ 9,62 mg/dL (normal).
        r = transcrever("Cálcio 2,4 mmol/L").resultados[0]
        self.assertEqual(r.unidade, "mg/dL")
        self.assertAlmostEqual(r.valor, 9.62, places=1)
        self.assertEqual(r.situacao, "normal")

    def test_glicose_com_faixa_inline(self):
        r = transcrever("Glicose de jejum 92 mg/dL (70 - 99)").resultados[0]
        self.assertEqual(r.valor, 92.0)
        self.assertEqual(r.situacao, "normal")


class TestLaudoCompleto(unittest.TestCase):
    def setUp(self):
        caminho = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "exemplos", "exame_exemplo.txt",
        )
        with open(caminho, encoding="utf-8") as f:
            self.texto = f.read()

    def test_reconhece_todos_os_analitos(self):
        t = transcrever(self.texto, sexo="M")
        nomes = {r.analito for r in t.resultados}
        for esperado in ["Hemoglobina", "Glicose", "Colesterol total",
                         "TSH", "Vitamina D (25-OH)", "Plaquetas"]:
            self.assertIn(esperado, nomes)

    def test_loinc_presente(self):
        t = transcrever(self.texto)
        for r in t.resultados:
            self.assertTrue(r.codigo_loinc, f"{r.analito} sem LOINC")

    def test_plaquetas_valor(self):
        t = transcrever(self.texto)
        plaq = next(r for r in t.resultados if r.analito == "Plaquetas")
        self.assertEqual(plaq.valor, 250000.0)

    def test_observacao_vira_nao_reconhecida(self):
        t = transcrever(self.texto)
        # A linha de observação não tem número -> nem entra como item.
        self.assertNotIn("Observação clínica", " ".join(t.nao_reconhecidos))

    def test_metadados_extraidos(self):
        t = transcrever(self.texto)
        self.assertEqual(t.metadados.get("paciente"), "João da Silva")
        self.assertEqual(t.metadados.get("data_coleta"), "10/07/2026")

    def test_data_nao_vira_ruido(self):
        t = transcrever(self.texto)
        self.assertNotIn("Data da coleta", " ".join(t.nao_reconhecidos))


class TestFormatoReduzido(unittest.TestCase):
    def test_catalogo_tem_abreviacao_unica(self):
        abreviacoes = [a.abreviacao for a in CATALOGO]
        self.assertTrue(all(abreviacoes), "há analito sem abreviação")
        self.assertEqual(len(abreviacoes), len(set(abreviacoes)), "abreviação duplicada")

    def test_resultado_carrega_abreviacao(self):
        r = transcrever("Hemoglobina 14,5 g/dL").resultados[0]
        self.assertEqual(r.abreviacao, "HB")

    def test_reduzir_omite_referencia_e_situacao(self):
        t = transcrever("Hemoglobina 11,2 g/dL\nColesterol Total 210 mg/dL")
        itens = reduzir(t)
        self.assertEqual(len(itens), 2)
        for item in itens:
            self.assertEqual(set(item), {"abreviacao", "valor", "unidade", "limite"})
        abreviacoes = {i["abreviacao"] for i in itens}
        self.assertEqual(abreviacoes, {"HB", "CT"})

    def test_para_json_reduzido_nao_tem_loinc_nem_situacao(self):
        t = transcrever("Glicose 92 mg/dL")
        bruto = para_json(t, formato="reduzido")
        self.assertNotIn("codigo_loinc", bruto)
        self.assertNotIn("situacao", bruto)
        self.assertIn('"GLIC"', bruto)

    def test_para_json_completo_mantem_todos_os_campos(self):
        t = transcrever("Glicose 92 mg/dL")
        bruto = para_json(t, formato="completo")
        self.assertIn("codigo_loinc", bruto)
        self.assertIn("situacao", bruto)

    def test_para_relatorio_reduzido_uma_linha_por_exame(self):
        t = transcrever("Hemoglobina 11,2 g/dL\nGlicose 92 mg/dL", metadados={"paciente": "Ana"})
        texto = para_relatorio(t, formato="reduzido")
        self.assertIn("HB: 11.2 g/dL", texto)
        self.assertIn("GLIC: 92 mg/dL", texto)
        self.assertIn("Paciente: Ana", texto)
        # Não deve haver situação nem faixa de referência no texto reduzido.
        self.assertNotIn("BAIXO", texto)
        self.assertNotIn("ALTO", texto)
        self.assertNotIn("ref:", texto)


if __name__ == "__main__":
    unittest.main()
