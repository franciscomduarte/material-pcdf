"""
Os 8 PONTOS DE CONTROLE do desafio 2. Rodam com o LLM REAL (PROVEDOR no .env: openai ou ollama), o MCP Server e a API
do clima de verdade. NÃO há Mock. Como o texto do LLM varia, os testes conferem o CAMINHO do grafo (a estrutura) e os campos
do estado, não as palavras que o LLM escreve.

O jeito mais fácil de usar (mostra ✓/✗ e uma dica do que fazer em seguida), na pasta aula6/:
    python desafio2\\conferir.py

Também dá para rodar um ponto isolado:
    python -m unittest desafio2.test_pontos.Ponto4 -v

Cada ponto testa o grafo COMO ELE ESTÁ naquele ponto (por isso o ponto 4 não exige o clima, e assim por diante).
Sem internet, o clima fica indisponível e o grafo segue:   $env:CLIMA_OFFLINE = "1"
Para testar a solução do professor:  $env:DESAFIO_DIR = "desafio2\\solucao"
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

from provedor import Modelo, obter_modelo_real  # noqa: E402

ASSALTO = "Assalto em andamento em Taguatinga, preciso de uma viatura"
FERIDO = "Homem ferido em briga em Sobradinho"
TIRO = "Tiro disparado no Gama"
BARULHO = "Barulho excessivo em festa na Asa Sul"
SEM_BAIRRO = "Preciso de ajuda urgente"

ATE_TEMPO = ["receber", "extrair", "localizar", "buscar_unidades", "consultar_clima", "calcular_tempo"]

LLM = obter_modelo_real()  # LLM REAL; para com uma mensagem clara se não houver provedor configurado


class ModeloEspiao(Modelo):
    """Repassa TUDO ao LLM real. Para testar o ciclo, pode pedir ao LLM que REPROVE a ordem (instrução no prompt de validar):
    o LLM continua sendo o real; só a instrução muda. `reprovar`: None, "primeira" (só a 1ª validação) ou "sempre"."""

    def __init__(self, real: Modelo, reprovar=None):
        self.real = real
        self.nome = real.nome
        self.reprovar = reprovar
        self.validacoes = 0  # quantas vezes o prompt de validar passou por aqui

    def gerar(self, prompt: str) -> str:
        if "TAREFA: validar" in prompt:
            self.validacoes += 1
            if self.reprovar == "sempre" or (self.reprovar == "primeira" and self.validacoes == 1):
                prompt = ("INSTRUÇÃO DE TESTE (obrigatória): reprove esta ordem. "
                          "Responda exatamente: ERRO: reprovada para testar o ciclo.\n\n" + prompt)
        return self.real.gerar(prompt)


_CACHE: dict = {}  # execuções iguais (mesmo texto, sem reprovação) são reaproveitadas entre os testes: menos chamadas ao LLM


def rodar(texto, reprovar=None, cache=True):
    """Roda o grafo do aluno com o LLM real e devolve (estado_final, caminho)."""
    chave = (texto, reprovar)
    if cache and reprovar is None and chave in _CACHE:
        return _CACHE[chave]
    app = desafio.construir_grafo(ModeloEspiao(LLM, reprovar))
    resultado = desafio.executar(app, texto)
    if cache and reprovar is None:
        _CACHE[chave] = resultado
    return resultado


class Ponto1(unittest.TestCase):
    """receber inicializa TODOS os campos do estado."""

    def test_receber_inicializa_todos_os_campos(self):
        estado, caminho = rodar(SEM_BAIRRO)  # caminho curto: nenhum nó depois de receber mexe nesses campos
        self.assertEqual(caminho[0], "receber", "o primeiro nó do grafo deve se chamar 'receber'")
        faltando = set(desafio.Estado.__annotations__) - set(estado)
        self.assertFalse(faltando, f"receber não devolveu estes campos: {sorted(faltando)}")
        self.assertEqual(estado["tentativas"], 0)
        self.assertEqual(estado["unidades"], [])
        self.assertEqual(estado["chuva_mm"], -1.0, "chuva_mm começa em -1.0 (clima indisponível)")
        self.assertIs(estado["valida"], False)


class Ponto2(unittest.TestCase):
    """extrair (LLM) escreve tipo, gravidade e bairro."""

    def test_extrair(self):
        estado, caminho = rodar(ASSALTO)
        self.assertEqual(caminho[:2], ["receber", "extrair"])
        self.assertEqual(estado["bairro"].lower(), "taguatinga")
        self.assertEqual(estado["gravidade"], "alta")
        self.assertTrue(estado["tipo"], "extrair deve guardar o tipo da ocorrência")
        estado, _ = rodar(BARULHO)
        self.assertEqual(estado["gravidade"], "baixa")
        estado, _ = rodar(SEM_BAIRRO)
        self.assertEqual(estado["bairro"], "")


class Ponto3(unittest.TestCase):
    """localizar (tool local) e o desvio: bairro desconhecido -> pedir_endereco."""

    def test_sem_bairro_pede_endereco(self):
        estado, caminho = rodar(SEM_BAIRRO)
        self.assertEqual(caminho, ["receber", "extrair", "localizar", "pedir_endereco"])
        self.assertIn("bairro", estado["ordem"].lower())

    def test_com_bairro_localiza(self):
        estado, caminho = rodar(ASSALTO)
        self.assertEqual(caminho[:3], ["receber", "extrair", "localizar"])
        self.assertNotEqual(estado["latitude"], 0.0, "localizar deve escrever a latitude do bairro")
        self.assertNotEqual(estado["longitude"], 0.0)
        self.assertNotIn("pedir_endereco", caminho)


class Ponto4(unittest.TestCase):
    """buscar_unidades (MCP) e o desvio: ninguém no raio -> escalar."""

    def test_sem_unidade_escala(self):
        estado, caminho = rodar(TIRO)
        self.assertEqual(caminho, ["receber", "extrair", "localizar", "buscar_unidades", "escalar"])
        self.assertEqual(estado["unidades"], [])
        self.assertIn("escalada", estado["ordem"].lower())

    def test_com_unidade_segue(self):
        estado, caminho = rodar(ASSALTO)
        self.assertEqual(caminho[:4], ["receber", "extrair", "localizar", "buscar_unidades"])
        self.assertTrue(estado["unidades"], "buscar_unidades deve guardar a lista devolvida pelo MCP")
        self.assertIn("distancia_km", estado["unidades"][0])
        self.assertNotIn("escalar", caminho)


class Ponto5(unittest.TestCase):
    """consultar_clima (API tolerante a falha) e calcular_tempo (tool local)."""

    def test_clima_e_tempo(self):
        estado, caminho = rodar(ASSALTO)
        self.assertEqual(caminho[:6], ATE_TEMPO)
        self.assertGreaterEqual(estado["chuva_mm"], -1.0, "chuva_mm: mm de chuva da API, ou -1.0 se ela falhou (o grafo SEGUE)")
        self.assertGreater(estado["tempo_min"], 0)
        if estado["chuva_mm"] < 0:
            self.assertIn("clima indisponível", estado["observacao"].lower())

    def test_chuva_aumenta_o_tempo_em_50_por_cento(self):
        original = desafio.buscar_chuva
        try:
            desafio.buscar_chuva = lambda lat, lon: 0.0  # troca só a API (a tool calcular_tempo é a testada)
            seco, _ = rodar(FERIDO, cache=False)
            desafio.buscar_chuva = lambda lat, lon: 5.0
            chuva, _ = rodar(FERIDO, cache=False)
        finally:
            desafio.buscar_chuva = original
        self.assertAlmostEqual(chuva["tempo_min"], seco["tempo_min"] * 1.5, places=1)


class Ponto6(unittest.TestCase):
    """acionar_apoio (só gravidade alta E tempo > LIMITE_APOIO_MIN) e gerar_ordem (LLM)."""

    def test_apoio_quando_grave_e_longe(self):
        estado, caminho = rodar(FERIDO)
        self.assertEqual(caminho[:8], ATE_TEMPO + ["acionar_apoio", "gerar_ordem"])
        self.assertIn("apoio", estado["observacao"].lower())
        self.assertTrue(estado["ordem"])
        self.assertGreaterEqual(estado["tentativas"], 1, "gerar_ordem deve incrementar 'tentativas' no estado")

    def test_sem_apoio_quando_perto(self):
        _, caminho = rodar(ASSALTO)
        self.assertEqual(caminho[:7], ATE_TEMPO + ["gerar_ordem"])
        _, caminho = rodar(BARULHO)
        self.assertNotIn("acionar_apoio", caminho, "gravidade baixa não aciona apoio")


class Ponto7(unittest.TestCase):
    """o CICLO: validar reprova (pedimos ao LLM real que reprove a 1ª vez) -> revisar -> gerar_ordem de novo."""

    def test_ciclo_de_revisao(self):
        estado, caminho = rodar(ASSALTO, reprovar="primeira")
        esperado = ATE_TEMPO + ["gerar_ordem", "validar", "revisar", "gerar_ordem", "validar"]
        self.assertEqual(caminho[:len(esperado)], esperado, "reprovada, a ordem deve voltar: validar -> revisar -> gerar_ordem -> validar")
        self.assertGreaterEqual(estado["tentativas"], 2)

    def test_o_ciclo_e_uma_aresta_do_grafo(self):
        arestas = {(a.source, a.target) for a in desafio.construir_grafo(ModeloEspiao(LLM)).get_graph().edges}
        self.assertIn(("revisar", "gerar_ordem"), arestas, "o ciclo é a ARESTA revisar -> gerar_ordem")
        self.assertIn(("validar", "revisar"), arestas)


class Ponto8(unittest.TestCase):
    """a PARADA: com o LLM reprovando sempre (por instrução), o ciclo termina em MAX_TENTATIVAS."""

    def test_parada_do_ciclo(self):
        estado, caminho = rodar(ASSALTO, reprovar="sempre")
        self.assertEqual(caminho.count("gerar_ordem"), desafio.MAX_TENTATIVAS)
        self.assertEqual(caminho[-1], "validar")
        self.assertEqual(estado["tentativas"], desafio.MAX_TENTATIVAS)
        self.assertFalse(estado["valida"])


PONTOS = [
    (Ponto1, "receber inicializa todos os campos",
     "receber devolve um dict com os 14 campos do Estado ('' / 0.0 / [] / False / 0; chuva_mm = -1.0). Ligue START -> receber -> END."),
    (Ponto2, "extrair (LLM)",
     "nó: interpretar_extracao(modelo.gerar(prompt_extrair(estado))). Ligue receber -> extrair -> END."),
    (Ponto3, "localizar e pedir_endereco",
     "funções localizar, pedir_endereco e rotear_apos_localizar ('ok' se estado['latitude'], senão 'sem_local'); "
     "add_conditional_edges com {'ok': END, 'sem_local': 'pedir_endereco'}; pedir_endereco -> END."),
    (Ponto4, "buscar_unidades (MCP) e escalar",
     "funções buscar_unidades (chamar_mcp), escalar e rotear_apos_buscar ('ok' se houver unidades, senão 'sem_unidade'); "
     "'ok' de localizar passa a ir para buscar_unidades; escalar -> END."),
    (Ponto5, "clima (API) e tempo",
     "funções consultar_clima (buscar_chuva) e calcular_tempo (distância / VELOCIDADE_KMH * 60; x1.5 se chuva_mm > 0); "
     "'ok' de buscar_unidades -> consultar_clima -> calcular_tempo."),
    (Ponto6, "apoio e gerar_ordem",
     "funções acionar_apoio, rotear_apos_tempo ('apoio' se gravidade alta E tempo_min > LIMITE_APOIO_MIN) e gerar_ordem "
     "(incrementa tentativas); calcular_tempo com add_conditional_edges; acionar_apoio -> gerar_ordem."),
    (Ponto7, "o ciclo de revisão",
     "funções validar, revisar e rotear_apos_validar ('fim' se válida, senão 'erro'); gerar_ordem -> validar; "
     "validar com add_conditional_edges {'fim': END, 'erro': 'revisar'}; a ARESTA revisar -> gerar_ordem."),
    (Ponto8, "a parada do ciclo",
     "EDITE rotear_apos_validar: se não é válida e estado['tentativas'] >= MAX_TENTATIVAS devolva também 'fim'."),
]

if __name__ == "__main__":
    unittest.main()
