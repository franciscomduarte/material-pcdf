"""
Exemplo 04 -- AGENTE + MCP: o fluxo completo.

    USUÁRIO -> AGENTE -> MCP CLIENT -> MCP SERVER -> TOOL -> POSTGRESQL
            -> RESULTADO -> AGENTE -> USUÁRIO

Este agente NÃO importa nenhuma função de banco. Ele só sabe que existe
um MCP Server (o mesmo do Exemplo 03) rodando via stdio, e delega a ele
a descoberta e a execução das tools.

MCPServerStdio faz o Agent Framework:
  1. subir `python server.py` como subprocesso;
  2. abrir uma sessão MCP com ele (handshake `initialize`);
  3. perguntar `list_tools` -- é AQUI que o schema (nome, parâmetros,
     docstring) vira algo que o LLM consegue ler;
  4. quando o LLM decide chamar uma tool, o Agent Framework traduz isso
     em `call_tool` sobre a sessão MCP.

Rodar:
    python agente.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # aula5/ (provedor.py)

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from provedor import configurar

configurar()

CAMINHO_SERVER = str(Path(__file__).resolve().parents[1] / "03_mcp_parametros" / "server.py")
LOG_SQL = Path(CAMINHO_SERVER).parent / "sql_executado.log"  # escrito pelo server


async def main():
    async with MCPServerStdio(
        name="MCP Ocorrências",
        params={"command": "python", "args": [CAMINHO_SERVER]},
    ) as mcp_ocorrencias:

        agente = Agent(
            name="Assistente CISP",
            instructions=(
                "Você ajuda operadores da CISP a entender as ocorrências recentes. "
                "Use as ferramentas do MCP Ocorrências para responder com dados reais."
            ),
            mcp_servers=[mcp_ocorrencias],
        )

        pergunta = "Quais ocorrências de Roubo de Veículo aconteceram na Região Kilo nos últimos 7 dias?"
        LOG_SQL.unlink(missing_ok=True)  # começa o log desta execução do zero
        resultado = await Runner.run(agente, pergunta)

        # O SQL que o server executou (lido do log que o próprio server escreve).
        if LOG_SQL.exists():
            print("\n--- SQL executado pelo server ---")
            print(LOG_SQL.read_text(encoding="utf-8").strip())

        # O que o LLM decidiu enviar para a tool.
        for item in resultado.new_items:
            if type(item).__name__ == "ToolCallItem":
                print(f"\n[tool] {item.raw_item.name}  parametros: {item.raw_item.arguments}")

        print("\n--- Resposta do agente ---")
        print(resultado.final_output)


if __name__ == "__main__":
    asyncio.run(main())
