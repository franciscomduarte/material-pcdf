"""
ETAPA 5 (continuação) -- Usando o MCP Server do RH de dois jeitos.

  ETAPA 5.3 -- por um AGENTE: o AtendenteRH com MCPServerStdio (o LLM escolhe a tool)
  ETAPA 5.4 -- por CÓDIGO: chamar_mcp(tool, argumentos), sem LLM (é o que os nós do grafo e as tools dos
               especialistas vão usar: quem decide a tool é o SEU código)

REFERÊNCIAS NAS AULAS
  aula5/exemplos/04_agente_mcp/agente.py      MCPServerStdio + Agent(mcp_servers=[...])        (5.3)
  aula5/exemplos/07_multiplos_mcp/agente.py   o agente escolhendo tools sozinho
  aula6/desafio2/main.py                      chamar_mcp() com ClientSession, sem agente       <- o mais parecido (5.4)
  aula5/exemplos/02_mcp_basico/cliente.py     cliente MCP "cru" (initialize, call_tool)

Rodar:
    python cliente_mcp.py            # 5.4: chama as tools direto e registra o C1 duas vezes (idempotência)
    python cliente_mcp.py --agente   # 5.3: o AtendenteRH responde usando o server

Pronto quando: o agente responde "A equipe Cartório tem alguém de férias entre 12 e 26/07/2027?" usando o server, e
registrar o C1 duas vezes gera um único registro.
"""
import asyncio
import json
import os
import sys

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from dados_rh import PASTA

load_dotenv(PASTA / ".env")
SERVER = str(PASTA / "mcp_rh.py")


async def chamar_mcp_async(tool: str, argumentos: dict) -> dict:
    # ETAPA 5.4 -- suba o server por stdio, abra a sessão, initialize(), call_tool(tool, argumentos).
    #   Se resposta.is_error: levante RuntimeError com o conteúdo.
    #   Toda tool do mcp_rh.py devolve UM dict: devolva json.loads(resposta.content[0].text).
    #   Dica: StdioServerParameters(command=sys.executable, args=[SERVER]) e, para não poluir a tela,
    #   stdio_client(params, errlog=open(os.devnull, "w")).
    #   Referência: aula6/desafio2/main.py (chamar_mcp)
    raise NotImplementedError("ETAPA 5.4: chamar_mcp_async")


def chamar_mcp(tool: str, argumentos: dict) -> dict:
    """(PRONTO) Versão síncrona, para os nós do grafo (Etapa 7) e o fluxo linear (Etapa 6).
    Dentro de código async (tools dos agentes), use `await chamar_mcp_async(...)`."""
    return asyncio.run(chamar_mcp_async(tool, argumentos))


async def perguntar_ao_atendente(pergunta: str) -> str:
    # ETAPA 5.3 -- async with MCPServerStdio(params={"command": sys.executable, "args": [SERVER]},
    #                                        name="rh") as servidor:
    #       agente = Agent(name="AtendenteRH", instructions=..., mcp_servers=[servidor])
    #       devolva (await Runner.run(agente, pergunta)).final_output
    #   Compare com a Etapa 1: o agente perdeu a tool local e ganhou o server inteiro.
    #   Referência: aula5/exemplos/04_agente_mcp/agente.py
    raise NotImplementedError("ETAPA 5.3: perguntar_ao_atendente")


if __name__ == "__main__":
    if "--agente" in sys.argv:
        from provedor import configurar
        print(f"[modelo] {configurar()}")
        print(asyncio.run(perguntar_ao_atendente("A equipe Cartório tem alguém de férias entre 12 e 26/07/2027?")))
    else:
        print(chamar_mcp("consultar_servidor", {"matricula": "1002"}))
        print(chamar_mcp("consultar_escala", {"equipe": "Cartório", "inicio": "2027-07-12", "fim": "2027-07-26"}))
        print(chamar_mcp("consultar_normas", {"tema": "abono"}))
        registro = {"protocolo": "teste001", "matricula": "1001", "tipo": "abono", "inicio": "2027-04-09",
                    "fim": "2027-04-09", "decisao": "deferido", "aprovador": "sistema",
                    "despacho": "Despacho de teste.", "token": os.getenv("TOKEN_REGISTRO", "")}
        print("1ª gravação:", chamar_mcp("registrar_decisao", registro))
        print("2ª gravação:", chamar_mcp("registrar_decisao", registro), " <- deve dizer duplicado")
        print(json.dumps({"sem_token": chamar_mcp("registrar_decisao", {**registro, "token": "errado"})},
                         ensure_ascii=False), " <- depois da Etapa 9.2, deve ser negado")
