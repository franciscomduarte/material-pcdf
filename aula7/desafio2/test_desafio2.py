"""
Casos de teste do desafio 2. Rodam com o LLM REAL (PROVEDOR no .env: openai ou ollama) e com as pessoas (gestor e
diretor) SIMULADAS pelas decisões do teste (sim/nao). Cada teste faz várias chamadas ao LLM: com Ollama em CPU,
leve alguns minutos.

Na pasta aula7/:
    python -m unittest desafio2.test_desafio2 -v

Os testes conferem o CAMINHO do grafo (a estrutura), não o texto que o LLM escreve. A ordem entre `juridico` e
`risco` (rodam em paralelo) não é garantida; os testes a ignoram. Um `ModeloEspiao` só registra os prompts
(ele repassa ao LLM real; não finge respostas).

Para testar a solução do professor:
    $env:DESAFIO_DIR = "desafio2\\solucao"; python -m unittest desafio2.test_desafio2 -v
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

spec = importlib.util.spec_from_file_location("desafio2_main", PASTA / "main.py")
desafio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desafio)

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402

from caso import DENUNCIA_045, DENUNCIA_BAIXO_VALOR  # noqa: E402
from provedor import Modelo, obter_modelo  # noqa: E402

ALTO = DENUNCIA_045
BAIXO = DENUNCIA_BAIXO_VALOR


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


def normalizar(caminho):
    """Troca o par paralelo (juridico, risco), em qualquer ordem, por 'paralelo' e confere que os dois rodaram."""
    saida, i = [], 0
    while i < len(caminho):
        if caminho[i] in ("juridico", "risco"):
            assert {caminho[i], caminho[i + 1]} == {"juridico", "risco"}, "juridico e risco devem rodar juntos"
            saida.append("paralelo")
            i += 2
        else:
            saida.append(caminho[i])
            i += 1
    return saida


BASE = ["receber", "investigar", "paralelo", "consolidar", "aprovacao_gestor"]


class TestDesafio2(unittest.TestCase):
    def test_caso1_baixo_risco_so_gestor(self):
        estado, caminho, _ = rodar(BAIXO, ["sim"])
        self.assertEqual(normalizar(caminho), BASE + ["finalizar"])
        self.assertEqual(estado["status"], "aprovada")
        self.assertEqual(estado["nivel_risco"], "baixo")

    def test_caso2_alto_risco_exige_diretor(self):
        estado, caminho, _ = rodar(ALTO, ["sim", "sim"])
        self.assertEqual(normalizar(caminho), BASE + ["aprovacao_diretor", "finalizar"])
        self.assertEqual(estado["status"], "aprovada")

    def test_caso3_rejeicao_do_gestor_gera_revisao_com_feedback(self):
        estado, caminho, espiao = rodar(ALTO, ["nao", "sim", "sim"])
        self.assertEqual(normalizar(caminho),
                         BASE + ["revisar", "consolidar", "aprovacao_gestor", "aprovacao_diretor", "finalizar"])
        self.assertEqual(estado["tentativas"], 2)
        com_feedback = [p for p in espiao.prompts if desafio.FEEDBACK_PADRAO in p]
        self.assertTrue(com_feedback, "o prompt da 2ª versão deve conter o feedback do gestor")

    def test_caso4_diretor_nega(self):
        estado, caminho, _ = rodar(ALTO, ["sim", "nao"])
        self.assertEqual(normalizar(caminho), BASE + ["aprovacao_diretor", "negar"])
        self.assertEqual(estado["status"], "negada_pelo_diretor")

    def test_caso5_limite_de_revisoes(self):
        estado, caminho, _ = rodar(ALTO, ["nao", "nao", "nao"])
        self.assertEqual(caminho.count("consolidar"), desafio.MAX_TENTATIVAS)
        self.assertEqual(caminho[-1], "encerrar")
        self.assertEqual(estado["status"], "limite_de_revisoes")

    def test_juridico_e_risco_escrevem_campos_diferentes(self):
        estado, _, _ = rodar(ALTO, ["sim", "sim"])
        self.assertTrue(estado["analise_juridica"])
        self.assertTrue(estado["analise_risco"])


if __name__ == "__main__":
    unittest.main()
