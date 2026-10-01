"""
Os 10 PONTOS DE CONTROLE do desafio (rodam com o Mock: sem API Key e sem internet).

    PARTE A (pontos 1 a 7): o grafo de decisão e ciclo.
    PARTE B (pontos 8 a 10): os TIPOS de nó: MCP, API e tool.

O jeito mais fácil de usar (mostra ✓/✗ e uma dica do que fazer em seguida), na pasta aula6/:
    python desafio\\conferir.py

Também dá para rodar um ponto isolado:
    python -m unittest desafio.test_pontos.Ponto3 -v

Cada ponto testa o grafo COMO ELE ESTÁ naquele ponto. Os pontos da Parte A ignoram os nós novos da Parte B
(consultar_feriados e calcular_prazo), então continuam passando depois que você faz a Parte B.
Os testes finais do grafo completo (Parte A) continuam em test_desafio.py.

Para testar a solução do professor:  $env:DESAFIO_DIR = "desafio\\solucao"
"""
import importlib.util
import os
import sys
import unittest
from datetime import date
from pathlib import Path

os.environ["FERIADOS_OFFLINE"] = "1"  # determinístico: sem internet; o grafo segue com a lista local de feriados

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
from provedor import Modelo  # noqa: E402

URGENTE = "Estou sem medicação e passando mal, preciso de atendimento agora"
SEGUNDA_VIA = "Preciso saber como solicitar uma segunda via de um documento"
PASSAPORTE = "Preciso renovar o passaporte"
HORARIO = "Qual o horário de atendimento?"
SEM_BASE = "Qual o prazo de restituição do imposto de renda de 2031?"

CAMPOS_PARTE_A = ["solicitacao", "urgencia", "informacao", "encaminhamento", "analise", "valida",
                  "tentativas", "feedback", "resposta"]
CAMPOS_PARTE_B = ["prazo_dias", "feriados", "prazo_final"]
NOS_PARTE_B = {"consultar_feriados", "calcular_prazo"}


def sem_parte_b(caminho):
    """Os pontos da Parte A não enxergam os nós novos da Parte B."""
    return [no for no in caminho if no not in NOS_PARTE_B]


class ModeloEspiao(Modelo):
    """Repassa ao Mock e guarda os prompts recebidos."""

    nome = "espiao"

    def __init__(self):
        self.real = ModeloMock()
        self.prompts = []

    def gerar(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.real.gerar(prompt)


def rodar(texto, modelo=None):
    app = desafio.construir_grafo(modelo or ModeloMock())
    return desafio.executar(app, texto)


# ------------------------------------------------------------------------------------ PARTE A
class Ponto1(unittest.TestCase):
    """receber inicializa TODOS os campos do estado."""

    def test_receber_inicializa_todos_os_campos(self):
        estado, caminho = rodar(URGENTE)
        self.assertEqual(caminho[0], "receber", "o primeiro nó do grafo deve se chamar 'receber'")
        faltando = set(CAMPOS_PARTE_A) - set(estado)
        self.assertFalse(faltando, f"receber não devolveu estes campos: {sorted(faltando)}")
        self.assertEqual(estado["tentativas"], 0)
        self.assertIs(estado["valida"], False)
        self.assertEqual(estado["informacao"], "")


class Ponto2(unittest.TestCase):
    """classificar_urgencia (LLM) escreve 'urgente' ou 'normal'."""

    def test_classificar_urgencia(self):
        estado, caminho = rodar(URGENTE)
        self.assertEqual(caminho[:2], ["receber", "classificar_urgencia"])
        self.assertEqual(estado["urgencia"], "urgente")
        estado, _ = rodar(SEGUNDA_VIA)
        self.assertEqual(estado["urgencia"], "normal")


class Ponto3(unittest.TestCase):
    """caminho URGENTE completo: encaminhar (tool) e responder."""

    def test_caminho_urgente(self):
        estado, caminho = rodar(URGENTE)
        self.assertEqual(sem_parte_b(caminho), ["receber", "classificar_urgencia", "encaminhar", "responder"])
        self.assertTrue(estado["encaminhamento"])
        self.assertIn("plantão", estado["resposta"].lower())


class Ponto4(unittest.TestCase):
    """caminho SEM BASE: a aresta impede o LLM de inventar."""

    def test_sem_base(self):
        estado, caminho = rodar(SEM_BASE)
        self.assertEqual(sem_parte_b(caminho), ["receber", "classificar_urgencia", "pesquisar", "responder"])
        self.assertEqual(estado["informacao"], "")
        self.assertEqual(estado["analise"], "", "'analisar' não pode rodar sem informação na base")
        self.assertIn("não encontrei", estado["resposta"].lower())


class Ponto5(unittest.TestCase):
    """caminho normal COM base: pesquisar -> analisar -> validar (ainda sem o ciclo)."""

    def test_analisar_e_validar(self):
        estado, caminho = rodar(SEGUNDA_VIA)
        self.assertEqual(sem_parte_b(caminho)[:5],
                         ["receber", "classificar_urgencia", "pesquisar", "analisar", "validar"])
        self.assertTrue(estado["analise"])
        self.assertGreaterEqual(estado["tentativas"], 1, "analisar deve incrementar 'tentativas' no estado")
        self.assertEqual(caminho[-1], "responder")


class Ponto6(unittest.TestCase):
    """o CICLO: validar reprova -> revisar -> analisar de novo."""

    def test_ciclo_de_revisao(self):
        estado, caminho = rodar(SEGUNDA_VIA)
        self.assertEqual(
            sem_parte_b(caminho),
            ["receber", "classificar_urgencia", "pesquisar", "analisar", "validar",
             "revisar", "analisar", "validar", "responder"],
        )
        self.assertEqual(estado["tentativas"], 2)
        self.assertTrue(estado["valida"])


class Ponto7(unittest.TestCase):
    """a PARADA: com validador que reprova sempre, o ciclo termina em MAX_TENTATIVAS."""

    def test_parada_do_ciclo(self):
        estado, caminho = rodar(SEGUNDA_VIA, ModeloMock(sempre_reprova=True))
        self.assertEqual(caminho.count("analisar"), desafio.MAX_TENTATIVAS)
        self.assertEqual(caminho[-1], "responder")
        self.assertEqual(estado["tentativas"], desafio.MAX_TENTATIVAS)
        self.assertFalse(estado["valida"])
        self.assertIn("não passou pela validação", estado["resposta"])


# ------------------------------------------------------------------------------------ PARTE B
class Ponto8(unittest.TestCase):
    """pesquisar vira um nó MCP: o serviço devolve o texto E o prazo."""

    def test_pesquisar_chama_o_mcp(self):
        chamadas = []
        original = desafio.chamar_mcp

        def espiao(ferramenta, argumentos):
            chamadas.append(ferramenta)
            return original(ferramenta, argumentos)

        desafio.chamar_mcp = espiao
        try:
            estado, _ = rodar(SEGUNDA_VIA)
            sem_base, caminho_sem_base = rodar(SEM_BASE)
        finally:
            desafio.chamar_mcp = original
        self.assertIn("consultar_base", chamadas, "pesquisar deve chamar chamar_mcp('consultar_base', ...)")
        self.assertIn("Agendar atendimento", estado["informacao"])
        self.assertEqual(estado["prazo_dias"], 5, "o MCP devolve prazo_dias_uteis: guarde em estado['prazo_dias']")
        self.assertEqual(sem_base["informacao"], "", "sem base, o MCP devolve lista vazia: informacao fica ''")
        self.assertEqual(sem_base["prazo_dias"], 0)
        self.assertEqual(sem_parte_b(caminho_sem_base), ["receber", "classificar_urgencia", "pesquisar", "responder"])
        faltando = set(CAMPOS_PARTE_B) - set(estado)
        self.assertFalse(faltando, f"receber deve inicializar também: {sorted(faltando)}")


class Ponto9(unittest.TestCase):
    """consultar_feriados é um nó de API, só no caminho COM base."""

    def test_api_de_feriados(self):
        estado, caminho = rodar(SEGUNDA_VIA)
        sem_prazo = [no for no in caminho if no != "calcular_prazo"]  # o ponto 10 ainda não é exigido aqui
        self.assertEqual(sem_prazo[:5], ["receber", "classificar_urgencia", "pesquisar", "consultar_feriados", "analisar"])
        self.assertIn("2026-10-12", estado["feriados"], "estado['feriados'] deve guardar a lista devolvida por buscar_feriados")
        _, caminho_urgente = rodar(URGENTE)
        self.assertNotIn("consultar_feriados", caminho_urgente)
        _, caminho_sem_base = rodar(SEM_BASE)
        self.assertNotIn("consultar_feriados", caminho_sem_base, "sem base o grafo vai direto para responder")


class Ponto10(unittest.TestCase):
    """calcular_prazo é uma TOOL (cálculo local) e o prazo chega ao LLM."""

    def test_somar_dias_uteis(self):
        ferias = desafio.FERIADOS_2026
        self.assertEqual(desafio.somar_dias_uteis(date(2026, 9, 29), 5, ferias), date(2026, 10, 6))
        self.assertEqual(desafio.somar_dias_uteis(date(2026, 9, 29), 10, ferias), date(2026, 10, 14), "pula o feriado de 12/10")
        self.assertEqual(desafio.somar_dias_uteis(date(2026, 10, 2), 1, []), date(2026, 10, 5), "pula o fim de semana")
        self.assertEqual(desafio.somar_dias_uteis(date(2026, 9, 29), 0, []), date(2026, 9, 29))

    def test_calcular_prazo_no_grafo(self):
        espiao = ModeloEspiao()
        estado, caminho = rodar(SEGUNDA_VIA, espiao)
        self.assertEqual(caminho[:6], ["receber", "classificar_urgencia", "pesquisar", "consultar_feriados",
                                       "calcular_prazo", "analisar"])
        self.assertEqual(estado["prazo_final"], "2026-10-06")
        self.assertTrue(any("2026-10-06" in p for p in espiao.prompts), "o prazo deve chegar ao prompt do LLM")
        passaporte, _ = rodar(PASSAPORTE)
        self.assertEqual(passaporte["prazo_final"], "2026-10-14")
        horario, _ = rodar(HORARIO)
        self.assertEqual(horario["prazo_final"], "", "assunto sem prazo (0 dias): prazo_final fica ''")


PONTOS = [
    (Ponto1, "receber inicializa todos os campos",
     "receber devolve um dict com os 9 campos do Estado ('' / False / 0). Ligue START -> receber -> END."),
    (Ponto2, "classificar_urgencia (LLM)",
     "nó: {'urgencia': normalizar_urgencia(modelo.gerar(prompt_classificar(estado)))}. Ligue receber -> classificar_urgencia -> END."),
    (Ponto3, "caminho urgente",
     "nós encaminhar (tool) e responder; roteador que devolve estado['urgencia']; add_conditional_edges com "
     "{'urgente': 'encaminhar', 'normal': END}; encaminhar -> responder -> END."),
    (Ponto4, "caminho sem base",
     "nó pesquisar (tool); roteador 'com_base' se estado['informacao'] senão 'sem_base'; 'normal' vai para pesquisar; "
     "por ora os dois rótulos vão para responder."),
    (Ponto5, "análise e validação",
     "nós analisar (incrementa tentativas) e validar; 'com_base' -> analisar -> validar -> responder."),
    (Ponto6, "o ciclo de revisão",
     "função revisar e rotear_apos_validar ('ok' ou 'erro'); ligue validar com add_conditional_edges e a ARESTA revisar -> analisar."),
    (Ponto7, "a parada do ciclo",
     "EDITE rotear_apos_validar: se não é válida e estado['tentativas'] >= MAX_TENTATIVAS devolva 'desistir' "
     "(o mapa do ponto 6 já o leva a responder)."),
    (Ponto8, "pesquisar vira um nó MCP",
     "EDITE pesquisar: achados = chamar_mcp('consultar_base', {'solicitacao': ...}); devolva informacao (achados[0]['texto']) e "
     "prazo_dias (achados[0]['prazo_dias_uteis']), ou '' e 0 se a lista vier vazia. Em receber, acrescente prazo_dias=0, feriados=[], prazo_final=''."),
    (Ponto9, "consultar_feriados (API)",
     "nó consultar_feriados: {'feriados': buscar_feriados(DATA_PEDIDO.year)}; no mapa de pesquisar troque 'com_base': 'analisar' por "
     "'com_base': 'consultar_feriados' e ligue consultar_feriados -> analisar."),
    (Ponto10, "calcular_prazo (tool)",
     "escreva a tool somar_dias_uteis() (topo do arquivo) e o nó calcular_prazo (prazo_dias 0 -> ''); ligue "
     "consultar_feriados -> calcular_prazo -> analisar (apague consultar_feriados -> analisar)."),
]

if __name__ == "__main__":
    unittest.main()
