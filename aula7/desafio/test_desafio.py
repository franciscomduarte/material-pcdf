"""
Casos de teste do desafio. Rodam com o LLM REAL (PROVEDOR no .env: openai ou ollama) e com a pessoa SIMULADA
pelas decisões do teste (sim/nao). Cada teste faz várias chamadas ao LLM: com Ollama em CPU, leve alguns minutos.

Na pasta aula7/:
    python -m unittest desafio.test_desafio -v

Os testes conferem o CAMINHO do grafo (a estrutura), não o texto que o LLM escreve. Um `ModeloEspiao` só
registra os prompts que o grafo enviou ao LLM (ele repassa ao LLM real; não finge respostas).

Para testar a solução do professor:
    $env:DESAFIO_DIR = "desafio\\solucao"; python -m unittest desafio.test_desafio -v
"""
import importlib.util
import os
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASTA = Path(os.getenv("DESAFIO_DIR", Path(__file__).resolve().parent))
if not PASTA.is_absolute():
    PASTA = RAIZ / PASTA

sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

spec = importlib.util.spec_from_file_location("desafio_main", PASTA / "main.py")
desafio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desafio)

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402

from caso import DENUNCIA_045, DENUNCIA_BAIXO_VALOR  # noqa: E402
from provedor import Modelo, obter_modelo  # noqa: E402

ALTO = DENUNCIA_045
BAIXO = DENUNCIA_BAIXO_VALOR
COMUM = ["receber", "investigar", "avaliar_risco"]


class ModeloEspiao(Modelo):
    """Repassa ao LLM REAL e guarda os prompts enviados."""

    def __init__(self, real: Modelo):
        self.real = real
        self.nome = real.nome
        self.prompts: list[str] = []

    def gerar(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.real.gerar(prompt)


LLM = obter_modelo()  # para com uma mensagem clara se não houver provedor configurado


def rodar(texto, decisoes):
    espiao = ModeloEspiao(LLM)
    app = desafio.construir_grafo(espiao, MemorySaver())
    estado, caminho = desafio.executar(app, texto, decisoes)
    return estado, caminho, espiao


class TestDesafio(unittest.TestCase):
    def test_caso1_baixo_risco_nao_chama_humano(self):
        estado, caminho, _ = rodar(BAIXO, [])
        self.assertEqual(caminho, COMUM + ["finalizar"])
        self.assertEqual(estado["status"], "aprovada_automaticamente")

    def test_caso2_alto_risco_pausa_e_aprova(self):
        estado, caminho, _ = rodar(ALTO, ["sim"])
        self.assertEqual(caminho, COMUM + ["recomendar", "validacao_humana", "finalizar"])
        self.assertEqual(estado["status"], "aprovada")
        self.assertEqual(estado["tentativas"], 1)

    def test_caso3_rejeicao_gera_revisao_com_feedback(self):
        estado, caminho, espiao = rodar(ALTO, ["nao", "sim"])
        self.assertEqual(caminho, COMUM + ["recomendar", "validacao_humana", "revisar",
                                           "recomendar", "validacao_humana", "finalizar"])
        self.assertEqual(estado["tentativas"], 2)
        # o feedback humano precisa ter CHEGADO ao LLM na 2ª recomendação
        com_feedback = [p for p in espiao.prompts if desafio.FEEDBACK_PADRAO in p]
        self.assertTrue(com_feedback, "o prompt da 2ª recomendação deve conter o feedback do humano")

    def test_caso4_limite_de_tentativas(self):
        estado, caminho, _ = rodar(ALTO, ["nao", "nao", "nao"])
        self.assertEqual(caminho.count("recomendar"), desafio.MAX_TENTATIVAS)
        self.assertEqual(caminho[-1], "encerrar")
        self.assertEqual(estado["status"], "limite_de_revisoes")
        self.assertFalse(estado["aprovado"])


if __name__ == "__main__":
    unittest.main()
