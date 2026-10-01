"""
Os 5 PONTOS DE CONTROLE da demonstração do cofre (sem LLM, sem internet, sem API Key).

O jeito mais fácil de usar, na pasta aula6/:
    python demo_cofre\\conferir.py

Também dá para rodar um ponto isolado:
    python -m unittest demo_cofre.test_pontos.Ponto3 -v

Cada ponto testa o grafo COMO ELE ESTÁ naquele ponto. Para testar a solução do professor:
    $env:DESAFIO_DIR = "demo_cofre\\solucao"
"""
import importlib.util
import os
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASTA = Path(os.getenv("DESAFIO_DIR", Path(__file__).resolve().parent))
if not PASTA.is_absolute():
    PASTA = RAIZ / PASTA

spec = importlib.util.spec_from_file_location("cofre_main", PASTA / "main.py")
cofre = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cofre)

ACERTA = ["1234"]
ERRA_E_ACERTA = ["0000", "1234"]
ERRA_SEMPRE = ["0", "1", "2", "1234"]


def rodar(entradas):
    return cofre.executar(cofre.construir_grafo(), entradas)


class Ponto1(unittest.TestCase):
    """receber inicializa o estado."""

    def test_receber(self):
        estado, caminho = rodar(ACERTA)
        self.assertEqual(caminho[0], "receber", "o primeiro nó do grafo deve se chamar 'receber'")
        faltando = set(cofre.Estado.__annotations__) - set(estado)
        self.assertFalse(faltando, f"faltam estes campos no estado: {sorted(faltando)}")
        self.assertIsInstance(estado["tentativas"], int)
        self.assertIsInstance(estado["acertou"], bool)
        self.assertIsInstance(estado["status"], str)


class Ponto2(unittest.TestCase):
    """tentar compara a senha e conta a tentativa."""

    def primeira_tentativa(self, entradas):
        """O que o nó `tentar` escreveu na 1ª vez em que rodou (independe do resto do grafo)."""
        app = cofre.construir_grafo()
        for passo in app.stream({"entradas": entradas}, {"recursion_limit": 40}, stream_mode="updates"):
            if "tentar" in passo:
                return passo["tentar"]
        self.fail("o nó 'tentar' nunca rodou: ligue receber -> tentar")

    def test_tentar(self):
        _, caminho = rodar(ACERTA)
        self.assertEqual(caminho[:2], ["receber", "tentar"])
        certa = self.primeira_tentativa(ACERTA)
        self.assertTrue(certa["acertou"])
        self.assertEqual(certa["tentativas"], 1, "tentar deve incrementar 'tentativas' no estado")
        errada = self.primeira_tentativa(["0000"])
        self.assertFalse(errada["acertou"])
        self.assertEqual(errada["tentativas"], 1)


class Ponto3(unittest.TestCase):
    """o caminho feliz: acertou -> liberar."""

    def test_caminho_feliz(self):
        estado, caminho = rodar(ACERTA)
        self.assertEqual(caminho, ["receber", "tentar", "liberar"])
        self.assertEqual(estado["status"], "liberado")
        self.assertEqual(estado["tentativas"], 1)


class Ponto4(unittest.TestCase):
    """o CICLO: errou -> tenta de novo (o nó volta para si mesmo)."""

    def test_ciclo(self):
        estado, caminho = rodar(ERRA_E_ACERTA)
        self.assertEqual(caminho, ["receber", "tentar", "tentar", "liberar"])
        self.assertEqual(estado["tentativas"], 2)
        self.assertEqual(estado["status"], "liberado")


class Ponto5(unittest.TestCase):
    """a PARADA: errou MAX_TENTATIVAS vezes -> bloquear."""

    def test_parada(self):
        estado, caminho = rodar(ERRA_SEMPRE)
        self.assertEqual(caminho, ["receber", "tentar", "tentar", "tentar", "bloquear"])
        self.assertEqual(estado["status"], "bloqueado")
        self.assertEqual(estado["tentativas"], cofre.MAX_TENTATIVAS)
        estado, caminho = rodar([])
        self.assertEqual(caminho.count("tentar"), cofre.MAX_TENTATIVAS, "sem senhas, o ciclo também precisa parar")


PONTOS = [
    (Ponto1, "receber inicializa o estado",
     "receber devolve {'tentativas': 0, 'acertou': False, 'status': ''}. Ligue START -> receber -> END."),
    (Ponto2, "tentar (compara a senha)",
     "tentar pega estado['entradas'][estado['tentativas']] ('' se acabou), compara com SENHA e devolve acertou e tentativas + 1. "
     "Ligue receber -> tentar -> END."),
    (Ponto3, "o caminho feliz",
     "funções liberar e rotear_apos_tentar ('ok' se acertou, senão 'erro'); "
     "add_conditional_edges('tentar', ..., {'ok': 'liberar', 'erro': END}); liberar -> END."),
    (Ponto4, "o ciclo (tentar de novo)",
     "só a ligação muda: troque 'erro': END por 'erro': 'tentar' (o nó volta para si mesmo)."),
    (Ponto5, "a parada (bloquear)",
     "função bloquear e EDITE rotear_apos_tentar: se não acertou e tentativas >= MAX_TENTATIVAS devolva 'bloquear'; "
     "acrescente 'bloquear': 'bloquear' ao mapa e bloquear -> END."),
]

if __name__ == "__main__":
    unittest.main()
