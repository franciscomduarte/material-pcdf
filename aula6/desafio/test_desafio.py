"""
Casos de teste do desafio, PARTE A (rodam com o Mock: sem API Key, sem internet).

Na pasta aula6/:
    python -m unittest desafio.test_desafio -v

Cada teste confere o CAMINHO percorrido pelo grafo, que é o que prova que as
decisões e o ciclo estão no grafo (e não escondidos dentro de um nó).

Os testes ignoram os nós da Parte B (consultar_feriados e calcular_prazo): passam antes e depois da Parte B.
Os pontos de controle 1 a 10 estão em test_pontos.py (use python desafio\\conferir.py).

Para testar outra implementação (ex.: a solução do professor):
    $env:DESAFIO_DIR = "desafio\\solucao"; python -m unittest desafio.test_desafio -v
"""
import csv
import importlib.util
import os
import sys
import unittest
from pathlib import Path

os.environ["FERIADOS_OFFLINE"] = "1"  # determinístico: sem internet

RAIZ = Path(__file__).resolve().parents[1]
PASTA = Path(os.getenv("DESAFIO_DIR", Path(__file__).resolve().parent))
if not PASTA.is_absolute():
    PASTA = RAIZ / PASTA

sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

spec = importlib.util.spec_from_file_location("desafio_main", PASTA / "main.py")
desafio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desafio)

from modelo_mock import ModeloMock  # noqa: E402

NOS_PARTE_B = {"consultar_feriados", "calcular_prazo"}


def sem_parte_b(caminho):
    return [no for no in caminho if no not in NOS_PARTE_B]


def rodar(texto, modelo=None):
    app = desafio.construir_grafo(modelo or ModeloMock())
    return desafio.executar(app, texto)


class TestDesafio(unittest.TestCase):
    def test_caso1_urgente_pula_a_analise(self):
        estado, caminho = rodar("Estou sem medicação e passando mal, preciso de atendimento agora")
        self.assertEqual(sem_parte_b(caminho), ["receber", "classificar_urgencia", "encaminhar", "responder"])
        self.assertEqual(estado["urgencia"], "urgente")
        self.assertIn("plantão", estado["resposta"].lower())

    def test_caso2_normal_com_uma_revisao(self):
        estado, caminho = rodar("Preciso saber como solicitar uma segunda via de um documento")
        self.assertEqual(
            sem_parte_b(caminho),
            ["receber", "classificar_urgencia", "pesquisar", "analisar", "validar",
             "revisar", "analisar", "validar", "responder"],
        )
        self.assertEqual(estado["tentativas"], 2)
        self.assertTrue(estado["valida"])

    def test_caso3_sem_base_nao_deixa_o_llm_inventar(self):
        estado, caminho = rodar("Qual o prazo de restituição do imposto de renda de 2031?")
        self.assertEqual(sem_parte_b(caminho), ["receber", "classificar_urgencia", "pesquisar", "responder"])
        self.assertEqual(estado["analise"], "")  # 'analisar' nunca rodou
        self.assertIn("não encontrei", estado["resposta"].lower())

    def test_caso4_ciclo_para_em_tres_tentativas(self):
        estado, caminho = rodar(
            "Preciso saber como solicitar uma segunda via de um documento",
            ModeloMock(sempre_reprova=True),
        )
        self.assertEqual(caminho.count("analisar"), desafio.MAX_TENTATIVAS)
        self.assertEqual(caminho[-1], "responder")
        self.assertEqual(estado["tentativas"], desafio.MAX_TENTATIVAS)
        self.assertFalse(estado["valida"])
        self.assertIn("não passou pela validação", estado["resposta"])


class TestBase(unittest.TestCase):
    def test_base_igual_ao_csv(self):
        """A base local (Parte A) e o CSV servido pelo MCP (Parte B) precisam ter os mesmos assuntos e textos."""
        with open(Path(__file__).resolve().parent / "base_conhecimento.csv", encoding="utf-8", newline="") as arquivo:
            do_csv = {linha["assunto"]: linha["texto"] for linha in csv.DictReader(arquivo)}
        self.assertEqual(desafio.BASE_CONHECIMENTO, do_csv)


if __name__ == "__main__":
    unittest.main()
