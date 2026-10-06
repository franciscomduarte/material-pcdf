"""
Casos de teste do desafio. Rodam com o LLM REAL (PROVEDOR no .env: openai ou ollama) e com a pessoa SIMULADA
pelas decisões do teste (sim/nao). Cada teste faz várias chamadas ao LLM: com Ollama em CPU, leve alguns minutos.

Na pasta aula7/:
    python -m unittest desafio.test_desafio -v

Os testes conferem o CAMINHO do grafo (a estrutura), não o texto que o LLM escreve. Um espião só registra as
entradas que o grafo enviou aos agentes (ele repassa ao LLM real; não finge respostas).

Para testar a solução do professor:
    $env:DESAFIO_DIR = "desafio\\solucao"; python -m unittest desafio.test_desafio -v
"""
import importlib.util
import os
import sys
import unittest
import warnings
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[1]
PASTA = Path(os.getenv("DESAFIO_DIR", Path(__file__).resolve().parent))
if not PASTA.is_absolute():
    PASTA = RAIZ / PASTA

sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

spec = importlib.util.spec_from_file_location("desafio_main", PASTA / "main.py")
desafio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desafio)

from agents import Runner  # noqa: E402
from langgraph.checkpoint.memory import MemorySaver  # noqa: E402

from caso import DENUNCIA_045, DENUNCIA_BAIXO_VALOR  # noqa: E402
from provedor import configurar  # noqa: E402

configurar()  # para com uma mensagem clara se não houver provedor configurado

ALTO = DENUNCIA_045
BAIXO = DENUNCIA_BAIXO_VALOR
COMUM = ["receber", "investigar", "avaliar_risco"]


def rodar(texto, decisoes):
    """Roda o grafo com o LLM real e devolve (estado, caminho, entradas enviadas aos agentes)."""
    entradas: list[str] = []
    original = Runner.run_sync

    def espiao(agente, entrada, *args, **kwargs):
        entradas.append(str(entrada))
        return original(agente, entrada, *args, **kwargs)

    # o SDK deixa avisos de ResourceWarning (conexões HTTP) ao fechar o laço de cada chamada: não são erro do grafo
    with warnings.catch_warnings(), mock.patch.object(Runner, "run_sync", espiao):
        warnings.simplefilter("ignore", ResourceWarning)
        app = desafio.construir_grafo(MemorySaver())
        estado, caminho = desafio.executar(app, texto, decisoes)
    return estado, caminho, entradas


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
        estado, caminho, entradas = rodar(ALTO, ["nao", "sim"])
        self.assertEqual(caminho, COMUM + ["recomendar", "validacao_humana", "revisar",
                                           "recomendar", "validacao_humana", "finalizar"])
        self.assertEqual(estado["tentativas"], 2)
        # o feedback humano precisa ter CHEGADO ao agente na 2ª recomendação
        com_feedback = [e for e in entradas if desafio.FEEDBACK_PADRAO in e]
        self.assertTrue(com_feedback, "a entrada da 2ª recomendação deve conter o feedback do humano")

    def test_caso4_limite_de_tentativas(self):
        estado, caminho, _ = rodar(ALTO, ["nao", "nao", "nao"])
        self.assertEqual(caminho.count("recomendar"), desafio.MAX_TENTATIVAS)
        self.assertEqual(caminho[-1], "encerrar")
        self.assertEqual(estado["status"], "limite_de_revisoes")
        self.assertFalse(estado["aprovado"])


if __name__ == "__main__":
    unittest.main()
