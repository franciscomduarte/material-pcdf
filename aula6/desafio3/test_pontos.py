"""
Os 6 PONTOS DE CONTROLE do desafio 3 (rodam com o JevMock e o ModeloMock: sem internet, sem API Key e SEM gastar créditos do JEV).

O jeito mais fácil de usar (mostra ✓/✗ e uma dica do que fazer em seguida), na pasta aula6/:
    python desafio3\\conferir.py

Também dá para rodar um ponto isolado:
    python -m unittest desafio3.test_pontos.Ponto4 -v

Cada ponto testa o grafo COMO ELE ESTÁ naquele ponto. Para testar a solução do professor:
    $env:DESAFIO_DIR = "desafio3\\solucao"
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

spec = importlib.util.spec_from_file_location("desafio3_main", PASTA / "main.py")
desafio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desafio)

from jev import JevMock  # noqa: E402
from modelo_mock import ModeloMock  # noqa: E402

URGENTE = "Estou sem medicação e passando mal, preciso de atendimento agora"
SENSIVEL = "Meu CPF é 123.456.789-00 e a senha do portal é abc123, podem verificar meu pedido?"
AMBIGUA = "Quero o passaporte, ou melhor, a segunda via do documento, não sei qual"
SEGUNDA_VIA = "Preciso saber como solicitar uma segunda via de um documento"
SEM_BASE = "Qual o prazo de restituição do imposto de renda de 2031?"

CAMPOS = ["solicitacao", "p_urgente", "p_sensivel", "assunto", "confianca", "informacao", "encaminhamento", "resposta"]


def rodar(texto):
    app = desafio.construir_grafo(ModeloMock(), JevMock())
    return desafio.executar(app, texto)


class Ponto1(unittest.TestCase):
    """receber inicializa TODOS os campos do estado."""

    def test_receber_inicializa_todos_os_campos(self):
        estado, caminho = rodar(URGENTE)
        self.assertEqual(caminho[0], "receber", "o primeiro nó do grafo deve se chamar 'receber'")
        faltando = set(CAMPOS) - set(estado)
        self.assertFalse(faltando, f"receber não devolveu estes campos: {sorted(faltando)}")


class Ponto2(unittest.TestCase):
    """avaliar (modelo de decisão) guarda os NÚMEROS no estado."""

    def test_avaliar_guarda_probabilidades(self):
        estado, caminho = rodar(URGENTE)
        self.assertEqual(caminho[:2], ["receber", "avaliar"])
        self.assertGreater(estado["p_urgente"], 0.9, "p_urgente deve vir de respostas['urgente']['noul']")
        self.assertLess(estado["p_sensivel"], 0.1)
        estado, _ = rodar(SEGUNDA_VIA)
        self.assertEqual(estado["assunto"], "segunda_via", "assunto deve vir de respostas['assunto']['choice']")
        self.assertGreater(estado["confianca"], 0.9, "confianca deve vir de respostas['assunto']['confidence']")
        self.assertIsInstance(estado["p_urgente"], float)


class Ponto3(unittest.TestCase):
    """o caminho URGENTE: o roteador decide pelo número."""

    def test_caminho_urgente(self):
        estado, caminho = rodar(URGENTE)
        self.assertEqual(caminho, ["receber", "avaliar", "encaminhar", "responder"])
        self.assertTrue(estado["encaminhamento"])
        self.assertIn("plantão", estado["resposta"].lower())
        _, caminho = rodar(SEGUNDA_VIA)
        self.assertNotIn("encaminhar", caminho, "só p_urgente >= LIMIAR_URGENTE vai ao plantão")


class Ponto4(unittest.TestCase):
    """o DADO SENSÍVEL: recusa, alerta e encerra (o LLM nem é chamado)."""

    def test_dado_sensivel(self):
        estado, caminho = rodar(SENSIVEL)
        self.assertEqual(caminho, ["receber", "avaliar", "alertar_dado_sensivel"])
        resposta = estado["resposta"].lower()
        self.assertTrue("cpf" in resposta or "senha" in resposta, "a resposta deve alertar sobre CPF/senha")
        self.assertEqual(estado["informacao"], "")


class Ponto5(unittest.TestCase):
    """o INCERTO: confiança baixa no assunto -> pede esclarecimento em vez de adivinhar."""

    def test_incerto(self):
        estado, caminho = rodar(AMBIGUA)
        self.assertEqual(caminho, ["receber", "avaliar", "pedir_esclarecimento"])
        self.assertLess(estado["confianca"], desafio.LIMIAR_CONFIANCA)
        self.assertIn("explicar", estado["resposta"].lower())


class Ponto6(unittest.TestCase):
    """COM BASE pesquisa e responde; SEM BASE admite que não sabe."""

    def test_com_base(self):
        estado, caminho = rodar(SEGUNDA_VIA)
        self.assertEqual(caminho, ["receber", "avaliar", "pesquisar", "responder"])
        self.assertIn("Agendar atendimento", estado["informacao"])

    def test_sem_base(self):
        estado, caminho = rodar(SEM_BASE)
        self.assertEqual(caminho, ["receber", "avaliar", "responder"], "sem base: não pesquisa, vai direto a responder")
        self.assertEqual(estado["informacao"], "")
        self.assertIn("não encontrei", estado["resposta"].lower())


PONTOS = [
    (Ponto1, "receber inicializa todos os campos",
     "receber devolve um dict com os 8 campos do Estado ('' / 0.0). Ligue START -> receber -> END."),
    (Ponto2, "avaliar (modelo de decisão): os números no estado",
     "respostas = jev.decidir(estado['solicitacao'], PERGUNTAS_JEV); devolva p_urgente, p_sensivel, assunto e confianca. "
     "Ligue receber -> avaliar -> END."),
    (Ponto3, "caminho urgente (o roteador decide pelo número)",
     "funções encaminhar, responder e rotear_apos_avaliar ('urgente' se p_urgente >= LIMIAR_URGENTE, senão 'outros'); "
     "add_conditional_edges('avaliar', ..., {'urgente': 'encaminhar', 'outros': END}); encaminhar -> responder -> END."),
    (Ponto4, "dado sensível",
     "função alertar_dado_sensivel e EDITE o roteador (depois do urgente: 'sensivel' se p_sensivel >= LIMIAR_SENSIVEL); "
     "acrescente 'sensivel' ao mapa e alertar_dado_sensivel -> END."),
    (Ponto5, "incerto (confiança baixa)",
     "função pedir_esclarecimento e EDITE o roteador ('incerto' se confianca < LIMIAR_CONFIANCA); "
     "acrescente 'incerto' ao mapa e pedir_esclarecimento -> END."),
    (Ponto6, "com base e sem base",
     "função pesquisar (BASE_CONHECIMENTO.get(assunto, '')) e a regra final do roteador ('com_base' se o assunto está na base, "
     "senão 'sem_base'); troque 'outros': END por 'com_base': 'pesquisar' e 'sem_base': 'responder'; pesquisar -> responder."),
]

if __name__ == "__main__":
    unittest.main()
