"""
Exemplo 11 -- UM GRAFO PRÓXIMO DO REAL: cada nó é um tipo diferente de capacidade.

Cenário: planejamento de efetivo para um período. O usuário pergunta, em texto
livre, o que a região terá pela frente, e o sistema junta várias fontes:

START
  ↓
receber ............. função Python (limpa a entrada)
  ↓
extrair ............. LLM  (texto livre -> região e datas, em JSON)
  ↓
 ┌────────────┴──────────────┐
 ↓ completo                  ↓ incompleto
 ├───────────┐             pedir_dados ... função (pede o que faltou) ─→ END
 ↓           ↓
consultar_eventos    consultar_feriados      <- DAG: rodam em paralelo
 (MCP: planilha)      (API HTTP: BrasilAPI)
 ↓           ↓
 └─────┬─────┘
       ↓
avaliar_risco ....... tool local (regra de negócio, sem IA)
       ↓
 ┌─────┴───────────┐
 ↓ médio/alto      ↓ baixo
estimar_efetivo   (pula)
 (MCP: cálculo)      ↓
 └─────┬─────────────┘
       ↓
redigir (LLM)  <──────────┐
       ↓                  │
validar (LLM)             │
  OK ↓      ERRO ↓        │
  END     revisar ────────┘   (para após MAX_TENTATIVAS)

O que este exemplo mostra: o grafo NÃO se importa com o TIPO do nó. LLM, MCP,
API, tool e função são todos "função que lê o estado e devolve uma atualização".
O grafo só decide a ORDEM; cada nó cuida do seu trabalho (e das suas falhas).

Rodar (LLM REAL por padrão: OpenAI, como nas Aulas 4 e 5; Ollama com $env:PROVEDOR = "ollama"; precisa do pacote `mcp`).
Sem OPENAI_API_KEY (ou com o Ollama fora do ar), AVISA e roda com o Mock; $env:PROVEDOR = "mock" força o Mock:
    python main.py
    python main.py "Planeje o efetivo da Região Bravo de 2026-09-25 a 2026-09-28"

Para simular a API de feriados fora do ar (usa o cache local):
    $env:FERIADOS_OFFLINE = "1"
"""
import asyncio
import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from langgraph.graph import END, START, StateGraph
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from modelo_mock import ModeloMock
from provedor import obter_modelo

modelo = obter_modelo(ModeloMock(), padrao="openai")  # LLM real por padrão; sem chave, cai no Mock com aviso

MAX_TENTATIVAS = 3
SERVER_MCP = str(Path(__file__).resolve().parent / "mcp_operacoes.py")


class Estado(TypedDict):
    solicitacao: str
    regiao: str
    data_inicio: str
    data_fim: str
    eventos: list        # consultar_eventos (MCP)
    feriados: list       # consultar_feriados (API)
    fonte_feriados: str  # "brasilapi" ou "cache_local"
    risco: str           # avaliar_risco: "baixo" | "medio" | "alto"
    efetivo: dict        # estimar_efetivo (MCP)
    resposta: str
    valida: bool
    tentativas: int
    feedback: str


# ---------------------------------------------------------------- integrações
def chamar_mcp(ferramenta: str, argumentos: dict) -> list:
    """Cliente MCP mínimo: sobe o server por stdio, chama UMA tool, devolve os itens.
    É o mesmo protocolo da Aula 5; aqui só o embrulhamos numa função síncrona."""

    async def _chamar():
        params = StdioServerParameters(command=sys.executable, args=[SERVER_MCP])
        with open(os.devnull, "w") as silencio:  # o log do server não polui a aula
            async with stdio_client(params, errlog=silencio) as (leitura, escrita):
                async with ClientSession(leitura, escrita) as sessao:
                    await sessao.initialize()
                    resposta = await sessao.call_tool(ferramenta, argumentos)
                    if resposta.is_error:
                        raise RuntimeError(f"MCP {ferramenta}: {resposta.content}")
                    return [json.loads(item.text) for item in resposta.content]

    return asyncio.run(_chamar())


# Cache local: usado quando a API está fora do ar (ou FERIADOS_OFFLINE=1).
FERIADOS_CACHE = {
    "2026-09-07": "Independência do Brasil",
    "2026-10-12": "Nossa Senhora Aparecida",
    "2026-11-02": "Finados",
    "2026-11-15": "Proclamação da República",
}


def buscar_feriados(inicio: str, fim: str) -> tuple[list, str]:
    """API HTTP pública (BrasilAPI). Toda API real falha: por isso o nó tem um plano B."""
    try:
        if os.getenv("FERIADOS_OFFLINE") == "1":
            raise OSError("modo offline")
        feriados = {}
        for ano in range(int(inicio[:4]), int(fim[:4]) + 1):
            pedido = urllib.request.Request(
                f"https://brasilapi.com.br/api/feriados/v1/{ano}", headers={"User-Agent": "curso-pcdf/1.0"}
            )  # sem User-Agent a API responde 403
            with urllib.request.urlopen(pedido, timeout=5) as r:
                feriados.update({f["date"]: f["name"] for f in json.load(r)})
        fonte = "brasilapi"
    except (OSError, ValueError):
        feriados, fonte = FERIADOS_CACHE, "cache_local"
    return [{"data": d, "nome": n} for d, n in sorted(feriados.items()) if inicio <= d <= fim], fonte


# --------------------------------------------------------------------- nós
def receber(estado: Estado) -> dict:  # FUNÇÃO
    print("[receber]")
    return {
        "solicitacao": estado["solicitacao"].strip(),
        "regiao": "", "data_inicio": "", "data_fim": "",
        "eventos": [], "feriados": [], "fonte_feriados": "",
        "risco": "", "efetivo": {}, "resposta": "",
        "valida": False, "tentativas": 0, "feedback": "",
    }


def extrair(estado: Estado) -> dict:  # LLM
    print("[extrair]   LLM")
    texto = modelo.gerar(
        "TAREFA: extrair\n"
        "Extraia da solicitação a região, a data inicial e a data final (AAAA-MM-DD).\n"
        'Responda só com JSON: {"regiao": ..., "data_inicio": ..., "data_fim": ...}. '
        "Use null no que não estiver na solicitação.\n"
        f"Solicitação: {estado['solicitacao']}"
    )
    try:
        dados = json.loads(texto[texto.index("{"): texto.rindex("}") + 1])
        date.fromisoformat(dados["data_inicio"])  # LLM erra: valida antes de confiar
        date.fromisoformat(dados["data_fim"])
    except (ValueError, KeyError, TypeError):
        return {"regiao": ""}  # sem região -> o roteador manda para pedir_dados
    if not dados.get("regiao"):
        return {"regiao": ""}
    return {"regiao": dados["regiao"], "data_inicio": dados["data_inicio"], "data_fim": dados["data_fim"]}


def pedir_dados(estado: Estado) -> dict:  # FUNÇÃO
    print("[pedir_dados]")
    return {
        "resposta": "Não consegui identificar a região e o período. "
                    "Informe, por exemplo: 'Região Bravo de 2026-09-25 a 2026-09-28'."
    }


def consultar_eventos(estado: Estado) -> dict:  # MCP
    print("[consultar_eventos]   MCP")
    eventos = chamar_mcp(
        "listar_eventos",
        {"regiao": estado["regiao"], "data_inicio": estado["data_inicio"], "data_fim": estado["data_fim"]},
    )
    return {"eventos": eventos}


def consultar_feriados(estado: Estado) -> dict:  # API
    feriados, fonte = buscar_feriados(estado["data_inicio"], estado["data_fim"])
    print(f"[consultar_feriados]  API ({fonte})")
    return {"feriados": feriados, "fonte_feriados": fonte}


def avaliar_risco(estado: Estado) -> dict:  # TOOL LOCAL (regra de negócio: nada de LLM aqui)
    pontos = sum(e["publico_estimado"] for e in estado["eventos"]) // 10_000 + 2 * len(estado["feriados"])
    risco = "alto" if pontos >= 4 else "medio" if pontos >= 2 else "baixo"
    print(f"[avaliar_risco]       pontos={pontos} -> {risco}")
    return {"risco": risco}


def estimar_efetivo(estado: Estado) -> dict:  # MCP
    print("[estimar_efetivo]     MCP")
    publico = sum(e["publico_estimado"] for e in estado["eventos"])
    (efetivo,) = chamar_mcp("estimar_efetivo", {"publico_total": publico, "dias_feriado": len(estado["feriados"])})
    return {"efetivo": efetivo}


def _fatos(estado: Estado) -> str:
    eventos = "; ".join(e["nome"] for e in estado["eventos"]) or "nenhum"
    feriados = "; ".join(f["nome"] for f in estado["feriados"]) or "nenhum"
    efetivo = estado["efetivo"]
    texto_efetivo = f"{efetivo['efetivo']} policiais e {efetivo['viaturas']} viaturas" if efetivo else "não necessário"
    return (
        f"Região: {estado['regiao']}\n"
        f"Período: {estado['data_inicio']} a {estado['data_fim']}\n"
        f"Eventos: {eventos}\n"
        f"Feriados: {feriados}\n"
        f"Risco: {estado['risco']}\n"
        f"Efetivo: {texto_efetivo}\n"
    )


def redigir(estado: Estado) -> dict:  # LLM
    tentativa = estado["tentativas"] + 1
    print(f"[redigir]   LLM, tentativa {tentativa}")
    correcao = f"Correção solicitada: {estado['feedback']}\n" if estado["feedback"] else ""
    resposta = modelo.gerar(
        "TAREFA: redigir\n"
        "Escreva um parecer curto para o comando, usando SOMENTE os fatos abaixo. "
        "Cite cada evento pelo nome. Não invente dados.\n"
        f"{correcao}FATOS:\n{_fatos(estado)}"
    )
    return {"resposta": resposta, "tentativas": tentativa}


def validar(estado: Estado) -> dict:  # LLM
    texto = modelo.gerar(
        "TAREFA: validar\n"
        "O parecer é válido se citar TODOS os eventos dos fatos e não afirmar nada além deles. "
        "Responda apenas 'OK' ou 'ERRO: <motivo>'.\n"
        f"FATOS:\n{_fatos(estado)}\n"
        f"Resposta: {estado['resposta']}"
    )
    ok = texto.strip().upper().startswith("OK")
    print(f"[validar]   LLM: {'OK' if ok else texto.strip()}")
    return {"valida": ok, "feedback": "" if ok else texto.strip()}


def revisar(estado: Estado) -> dict:  # FUNÇÃO
    print("[revisar]   volta para redigir")
    return {"feedback": f"corrija — {estado['feedback']}"}


# ------------------------------------------------------------- roteadores
def rotear_apos_extrair(estado: Estado) -> list[str]:
    if not estado["regiao"]:
        return ["incompleto"]
    return ["eventos", "feriados"]  # lista = ramificação: os dois nós rodam em paralelo


def rotear_apos_risco(estado: Estado) -> str:
    return "baixo" if estado["risco"] == "baixo" else "reforco"


def rotear_apos_validar(estado: Estado) -> str:
    if estado["valida"] or estado["tentativas"] >= MAX_TENTATIVAS:
        return "fim"  # válido, ou desistiu (condição de parada lida do estado)
    return "erro"


# ------------------------------------------------------------------- grafo
construtor = StateGraph(Estado)
for nome, funcao in [
    ("receber", receber),
    ("extrair", extrair),
    ("pedir_dados", pedir_dados),
    ("consultar_eventos", consultar_eventos),
    ("consultar_feriados", consultar_feriados),
    ("avaliar_risco", avaliar_risco),
    ("estimar_efetivo", estimar_efetivo),
    ("redigir", redigir),
    ("validar", validar),
    ("revisar", revisar),
]:
    construtor.add_node(nome, funcao)

construtor.add_edge(START, "receber")
construtor.add_edge("receber", "extrair")
construtor.add_conditional_edges(
    "extrair",
    rotear_apos_extrair,
    {"incompleto": "pedir_dados", "eventos": "consultar_eventos", "feriados": "consultar_feriados"},
)
construtor.add_edge("pedir_dados", END)
construtor.add_edge(["consultar_eventos", "consultar_feriados"], "avaliar_risco")  # merge: espera os dois
construtor.add_conditional_edges(
    "avaliar_risco", rotear_apos_risco, {"reforco": "estimar_efetivo", "baixo": "redigir"}
)
construtor.add_edge("estimar_efetivo", "redigir")
construtor.add_edge("redigir", "validar")
construtor.add_conditional_edges("validar", rotear_apos_validar, {"fim": END, "erro": "revisar"})
construtor.add_edge("revisar", "redigir")  # o ciclo

app = construtor.compile()


def executar(solicitacao: str) -> None:
    print("=" * 70)
    print("Solicitação:", solicitacao)
    print("=" * 70)
    estado: dict = {"solicitacao": solicitacao}
    caminho = []
    for passo in app.stream(estado, stream_mode="updates"):
        for no, atualizacao in passo.items():
            caminho.append(no)
            estado.update(atualizacao)
    print("\nCaminho:", " -> ".join(caminho))
    print(f"Risco: {estado.get('risco') or '-'} | tentativas de redação: {estado.get('tentativas', 0)}")
    print("Resposta:", estado["resposta"], "\n")


if __name__ == "__main__":
    print(f"Modelo em uso: {modelo.nome}\n")
    if len(sys.argv) > 1:
        executar(" ".join(sys.argv[1:]))
    else:
        executar("Planeje o efetivo da Região Bravo de 2026-09-25 a 2026-09-28")   # risco alto + ciclo
        executar("Como está a Região Bravo de 2026-09-05 a 2026-09-08?")           # só o feriado: médio
        executar("Como está a Região Alfa de 2026-09-25 a 2026-09-28?")            # sem nada: baixo
        executar("Planeje o efetivo da Região Bravo")                              # sem datas: pede dados
