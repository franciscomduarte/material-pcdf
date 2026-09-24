"""
Exemplo 14 -- TRÊS FONTES, UM AGENTE.

    PostgreSQL (ocorrências)  ┐
    SQL Server (viaturas)     ├──> MCP ──> AGENTE ──> análise cruzada
    Planilha (eventos)        ┘

Nenhuma das três fontes conhece as outras. O cruzamento acontece no agente,
casando por região e por data.

Rodar:
    python agente.py
    python agente.py "Sua pergunta"
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # aula5/ (provedor.py)

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from provedor import configurar

configurar()

AQUI = Path(__file__).resolve().parent
EXEMPLOS = AQUI.parent
SERVER_OCORRENCIAS = str(AQUI / "server_ocorrencias_dia.py")                    # PostgreSQL
SERVER_OPERACOES = str(EXEMPLOS / "08_mcp_servicos" / "server_operacoes.py")    # SQL Server
SERVER_EVENTOS = str(EXEMPLOS / "12_mcp_eventos" / "server.py")                 # planilha

INSTRUCOES = (
    "Você integra três fontes independentes da CISP: o MCP Ocorrências "
    "(PostgreSQL: ranking de regiões e ocorrências por dia), o MCP Operações (SQL Server: "
    "unidades e viaturas) e o MCP Eventos (uma planilha com jogos, shows, feiras "
    "e manifestações). Elas não compartilham dados: o cruzamento é por REGIÃO e "
    "por DATA. Os dados de ocorrências vão de 2025-09-22 a 2026-09-21. "
    "Ao ligar um pico de ocorrências a um evento, diga que é COINCIDÊNCIA DE "
    "DATA, não prova de causa. Se um pico não tiver evento, diga isso. "
    "Informe de qual fonte veio cada dado."
)

PERGUNTA_PADRAO = (
    "Analise a Região Bravo de 2026-09-01 a 2026-09-21. Em quais dias houve pico "
    "de ocorrências? Havia eventos nesses dias? E quantas viaturas disponíveis "
    "as unidades da região têm hoje?"
)

PERGUNTA = sys.argv[1] if len(sys.argv) > 1 else PERGUNTA_PADRAO


def servidor(nome: str, caminho: str) -> MCPServerStdio:
    return MCPServerStdio(
        name=nome,
        params={"command": sys.executable, "args": [caminho]},
        client_session_timeout_seconds=30,
    )


async def main():
    async with servidor("MCP Ocorrências", SERVER_OCORRENCIAS) as ocorrencias, \
               servidor("MCP Operações", SERVER_OPERACOES) as operacoes, \
               servidor("MCP Eventos", SERVER_EVENTOS) as eventos:

        agente = Agent(
            name="Analista CISP",
            instructions=INSTRUCOES,
            mcp_servers=[ocorrencias, operacoes, eventos],
        )

        print(f"Pergunta: {PERGUNTA}")
        resultado = await Runner.run(agente, PERGUNTA, max_turns=25)

        # Trilha: qual tool, de qual fonte, com quais parâmetros.
        print("\n--- Trilha das chamadas ---")
        for item in resultado.new_items:
            if type(item).__name__ == "ToolCallItem":
                origem = getattr(item.tool_origin, "mcp_server_name", None)
                print(f"[tool] {origem} | {item.raw_item.name} {item.raw_item.arguments}")

        print("\n--- Resposta do agente ---")
        print(resultado.final_output)


if __name__ == "__main__":
    asyncio.run(main())
