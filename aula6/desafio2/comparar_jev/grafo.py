"""
Desafio 2 COM e SEM JEV: o MESMO grafo, com UMA chave: construir_grafo(modelo, jev=None).

    jev=None  -> o nó `extrair` é o do desafio 2: o LLM devolve um JSON em texto (tipo, gravidade, bairro).
    jev=<JEV> -> o nó `extrair` pergunta ao JEV: números (probabilidade de gravidade) e a CONFIANÇA no bairro.

Só o nó `extrair` muda. Os outros 11 nós, os roteadores e as arestas são os mesmos nos dois casos.
O que muda para o grafo: a gravidade passa a vir de uma PROBABILIDADE (p_grave) e um bairro de baixa confiança
NÃO é adivinhado: o grafo pede o endereço (caminho pedir_endereco), em vez de seguir com o bairro que o LLM "achou".

Rodar a comparação (a partir de aula6/):   python desafio2\\comparar_jev\\comparar.py
"""
import asyncio
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import TypedDict

RAIZ = Path(__file__).resolve().parents[2]  # aula6/
sys.path.insert(0, str(RAIZ))                      # provedor.py
sys.path.insert(0, str(RAIZ / "desafio3"))         # jev.py (o cliente do JEV, do desafio 3)

from langgraph.graph import END, START, StateGraph  # noqa: E402
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

MAX_TENTATIVAS = 3
LIMITE_APOIO_MIN = 8
VELOCIDADE_KMH = 40
SERVER_MCP = str(RAIZ / "desafio2" / "mcp_unidades.py")

# ---- limiares do JEV (só usados quando há JEV) ----
LIMIAR_GRAVE = 0.5       # p_grave a partir da qual a gravidade é "alta"
LIMIAR_CONFIANCA = 0.6   # confiança mínima no bairro; abaixo disso o grafo NÃO adivinha e pede o endereço

BAIRROS = {
    "asa sul": (-15.8267, -47.9218),
    "asa norte": (-15.7633, -47.8829),
    "taguatinga": (-15.8330, -48.0570),
    "ceilândia": (-15.8190, -48.1070),
    "sobradinho": (-15.6500, -47.7900),
    "gama": (-16.0200, -48.0600),
}

# As perguntas ao JEV: UMA chamada (1 crédito) responde as 3. As chaves do "bairro" são as MESMAS de BAIRROS.
PERGUNTAS_JEV = {
    "grave": {"type": "noul",
              "instructions": "A ocorrência envolve risco à vida, violência contra pessoa ou arma?"},
    "tipo": {"type": "choice", "instructions": "Qual o tipo da ocorrência?",
             "criteria": {"assalto": "roubo ou assalto", "agressao": "briga ou pessoa ferida",
                          "disparo": "tiro ou arma de fogo disparada", "perturbacao": "barulho ou perturbação do sossego",
                          "outro": "qualquer outro tipo"}},
    "bairro": {"type": "choice", "instructions": "Em qual bairro ocorre?",
               "criteria": {**{b: f"a ocorrência é em {b.title()}" for b in BAIRROS},
                            "nenhum": "nenhum bairro citado, ou não dá para saber qual"}},
}


class Estado(TypedDict):
    solicitacao: str
    tipo: str
    gravidade: str
    bairro: str
    p_grave: float        # NOVO: escrito por extrair (JEV); -1.0 = não há JEV (o LLM só devolve "alta"/"baixa")
    confianca_bairro: float  # NOVO: escrito por extrair (JEV); -1.0 = não há JEV
    latitude: float
    longitude: float
    unidades: list
    chuva_mm: float
    tempo_min: float
    observacao: str
    ordem: str
    valida: bool
    tentativas: int
    feedback: str


# ----------------------------------------------- integrações (as mesmas do desafio 2)
def chamar_mcp(ferramenta: str, argumentos: dict) -> list:
    async def _chamar():
        params = StdioServerParameters(command=sys.executable, args=[SERVER_MCP])
        with open(os.devnull, "w") as silencio:
            async with stdio_client(params, errlog=silencio) as (leitura, escrita):
                async with ClientSession(leitura, escrita) as sessao:
                    await sessao.initialize()
                    resposta = await sessao.call_tool(ferramenta, argumentos)
                    if resposta.is_error:
                        raise RuntimeError(f"MCP {ferramenta}: {resposta.content}")
                    return [json.loads(item.text) for item in resposta.content]
    return asyncio.run(_chamar())


def buscar_chuva(latitude: float, longitude: float) -> float:
    if os.getenv("CLIMA_OFFLINE") == "1":
        return -1.0
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=precipitation"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return float(json.load(r)["current"]["precipitation"])
    except (OSError, ValueError, KeyError):
        return -1.0


# ------------------------------------------------ prompts (os mesmos do desafio 2)
def prompt_extrair(estado: Estado) -> str:
    return (
        "TAREFA: extrair\n"
        "Extraia da solicitação o tipo da ocorrência, a gravidade ('alta' ou 'baixa') e o bairro.\n"
        'Responda só com JSON: {"tipo": ..., "gravidade": ..., "bairro": ...}. '
        "Use null no que não estiver na solicitação.\n"
        f"Solicitação: {estado['solicitacao']}"
    )


def _fatos(estado: Estado) -> str:
    return (
        f"Unidade: {estado['unidades'][0]['nome']}\n"
        f"Bairro: {estado['bairro']}\n"
        f"Tipo: {estado['tipo']}\n"
        f"Tempo: {estado['tempo_min']} min\n"
        f"Observação: {estado['observacao']}\n"
    )


def prompt_gerar_ordem(estado: Estado) -> str:
    correcao = f"Correção solicitada: {estado['feedback']}\n" if estado["feedback"] else ""
    return (
        "TAREFA: gerar_ordem\n"
        "Redija uma ordem de serviço de uma frase, usando SOMENTE os fatos abaixo.\n"
        f"{correcao}FATOS:\n{_fatos(estado)}"
    )


def prompt_validar(estado: Estado) -> str:
    return (
        "TAREFA: validar\n"
        "A ordem é válida se citar a unidade despachada. Responda apenas 'OK' ou 'ERRO: <motivo>'.\n"
        f"Unidade: {estado['unidades'][0]['nome']}\n"
        f"Ordem: {estado['ordem']}"
    )


def interpretar_extracao(texto: str) -> dict:
    """Texto livre do LLM -> campos do estado (o trabalho de 'interpretar texto' que o JEV dispensa)."""
    try:
        dados = json.loads(texto[texto.index("{"): texto.rindex("}") + 1])
    except ValueError:
        dados = {}
    return {
        "tipo": dados.get("tipo") or "",
        "gravidade": "alta" if dados.get("gravidade") == "alta" else "baixa",
        "bairro": dados.get("bairro") or "",
    }


def ordem_aprovada(texto: str) -> bool:
    return texto.strip().upper().startswith("OK")


# ------------------------------------------------------------------ o grafo
def construir_grafo(modelo, jev=None):
    """O grafo do desafio 2. Com `jev`, o nó extrair é decidido por probabilidades; sem ele, pelo LLM."""

    def receber(estado):
        return {"solicitacao": estado["solicitacao"].strip(), "tipo": "", "gravidade": "", "bairro": "",
                "p_grave": -1.0, "confianca_bairro": -1.0,
                "latitude": 0.0, "longitude": 0.0, "unidades": [], "chuva_mm": -1.0, "tempo_min": 0.0,
                "observacao": "", "ordem": "", "valida": False, "tentativas": 0, "feedback": ""}

    def extrair_llm(estado):  # SEM JEV: o LLM escreve um JSON; o código interpreta o texto
        return interpretar_extracao(modelo.gerar(prompt_extrair(estado)))

    def extrair_jev(estado):  # COM JEV: números tipados, sem interpretar texto, e com CONFIANÇA
        r = jev.decidir(estado["solicitacao"], PERGUNTAS_JEV)
        p_grave = r["grave"]["noul"]
        escolhido, confianca = r["bairro"]["choice"], r["bairro"]["confidence"]
        bairro = escolhido if escolhido in BAIRROS and confianca >= LIMIAR_CONFIANCA else ""  # baixa confiança: NÃO adivinha
        return {"tipo": r["tipo"]["choice"], "gravidade": "alta" if p_grave >= LIMIAR_GRAVE else "baixa",
                "bairro": bairro, "p_grave": p_grave, "confianca_bairro": confianca}

    def localizar(estado):
        coordenadas = BAIRROS.get(estado["bairro"].lower())
        if not coordenadas:
            return {"latitude": 0.0, "longitude": 0.0}
        return {"latitude": coordenadas[0], "longitude": coordenadas[1]}

    def pedir_endereco(estado):
        return {"ordem": "Não consegui localizar a ocorrência. Informe o bairro (ex.: Asa Sul, Taguatinga)."}

    def rotear_apos_localizar(estado):
        return "ok" if estado["latitude"] else "sem_local"

    def buscar_unidades(estado):
        return {"unidades": chamar_mcp("unidades_proximas", {"latitude": estado["latitude"],
                                                              "longitude": estado["longitude"],
                                                              "raio_km": 20, "limite": 2})}

    def escalar(estado):
        return {"ordem": f"Nenhuma unidade com viatura disponível em 20 km de {estado['bairro']}: "
                         "ocorrência escalada ao comando."}

    def rotear_apos_buscar(estado):
        return "ok" if estado["unidades"] else "sem_unidade"

    def consultar_clima(estado):
        return {"chuva_mm": buscar_chuva(estado["latitude"], estado["longitude"])}

    def calcular_tempo(estado):
        tempo = estado["unidades"][0]["distancia_km"] / VELOCIDADE_KMH * 60
        if estado["chuva_mm"] > 0:
            tempo *= 1.5
        observacao = "Clima indisponível: tempo sem ajuste por chuva." if estado["chuva_mm"] < 0 else ""
        return {"tempo_min": round(tempo, 1), "observacao": observacao}

    def acionar_apoio(estado):
        if len(estado["unidades"]) > 1:
            aviso = f"Apoio: {estado['unidades'][1]['nome']}."
        else:
            aviso = "Sem unidade de apoio no raio."
        return {"observacao": f"{estado['observacao']} {aviso}".strip()}

    def rotear_apos_tempo(estado):
        return "apoio" if estado["gravidade"] == "alta" and estado["tempo_min"] > LIMITE_APOIO_MIN else "normal"

    def gerar_ordem(estado):
        return {"ordem": modelo.gerar(prompt_gerar_ordem(estado)), "tentativas": estado["tentativas"] + 1}

    def validar(estado):
        texto = modelo.gerar(prompt_validar(estado))
        ok = ordem_aprovada(texto)
        return {"valida": ok, "feedback": "" if ok else texto.strip()}

    def revisar(estado):
        return {"feedback": f"corrija — {estado['feedback']}"}

    def rotear_apos_validar(estado):
        if estado["valida"] or estado["tentativas"] >= MAX_TENTATIVAS:
            return "fim"
        return "erro"

    construtor = StateGraph(Estado)
    for nome, funcao in [
        ("receber", receber), ("extrair", extrair_jev if jev else extrair_llm),  # <- a ÚNICA diferença entre os dois grafos
        ("localizar", localizar), ("pedir_endereco", pedir_endereco), ("buscar_unidades", buscar_unidades),
        ("escalar", escalar), ("consultar_clima", consultar_clima), ("calcular_tempo", calcular_tempo),
        ("acionar_apoio", acionar_apoio), ("gerar_ordem", gerar_ordem), ("validar", validar), ("revisar", revisar),
    ]:
        construtor.add_node(nome, funcao)

    construtor.add_edge(START, "receber")
    construtor.add_edge("receber", "extrair")
    construtor.add_edge("extrair", "localizar")
    construtor.add_conditional_edges("localizar", rotear_apos_localizar,
                                     {"ok": "buscar_unidades", "sem_local": "pedir_endereco"})
    construtor.add_edge("pedir_endereco", END)
    construtor.add_conditional_edges("buscar_unidades", rotear_apos_buscar,
                                     {"ok": "consultar_clima", "sem_unidade": "escalar"})
    construtor.add_edge("escalar", END)
    construtor.add_edge("consultar_clima", "calcular_tempo")
    construtor.add_conditional_edges("calcular_tempo", rotear_apos_tempo,
                                     {"apoio": "acionar_apoio", "normal": "gerar_ordem"})
    construtor.add_edge("acionar_apoio", "gerar_ordem")
    construtor.add_edge("gerar_ordem", "validar")
    construtor.add_conditional_edges("validar", rotear_apos_validar, {"fim": END, "erro": "revisar"})
    construtor.add_edge("revisar", "gerar_ordem")
    return construtor.compile()


def executar(app, solicitacao: str):
    """Roda o grafo e devolve (estado_final, caminho)."""
    estado: dict = {"solicitacao": solicitacao}
    caminho = []
    for passo in app.stream(estado, {"recursion_limit": 40}, stream_mode="updates"):
        for no, atualizacao in passo.items():
            caminho.append(no)
            estado.update(atualizacao)
    return estado, caminho
