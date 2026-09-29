"""
Exemplo 15 -- AGENTE + MCP por HTTP.

    USUÁRIO -> AGENTE -> MCP CLIENT --(HTTP)--> MCP SERVER -> TOOL

É o Exemplo 04 com uma troca: `MCPServerStdio` vira `MCPServerStreamableHttp`.
Repare no que SOME do código do agente:
  - `command` e `args`: o agente não sabe mais onde está o arquivo do server,
    nem qual Python o executa;
  - o subprocesso: o agente não é mais dono do ciclo de vida do server.

No lugar entra só uma URL. O server pode estar nesta máquina, na máquina do
colega, num container ou num servidor na nuvem. Para o agente é indiferente.

Pré-requisito: o server do Exemplo 14 rodando em outro terminal.
    cd ../14_mcp_http_basico
    python server.py

Rodar:
    python agente.py
    python agente.py "Qual a delegacia mais próxima do ponto -23.60, -46.54?"

Apontar para um server em OUTRA máquina (o server precisa escutar em 0.0.0.0):
    PowerShell: $env:MCP_URL = "http://192.168.0.10:8000/mcp"; python agente.py
    bash:       MCP_URL=http://192.168.0.10:8000/mcp python agente.py
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # aula5/ (provedor.py)

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

from provedor import configurar

configurar()

URL = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp")
PERGUNTA_PADRAO = (
    "Um roubo aconteceu no ponto de latitude -23.50 e longitude -46.55. "
    "Qual a unidade mais próxima e a que distância ela fica?"
)


async def main():
    pergunta = sys.argv[1] if len(sys.argv) > 1 else PERGUNTA_PADRAO

    # Se o server não estiver de pé, o erro aparece AQUI, na conexão -- não no meio da conversa.
    async with MCPServerStreamableHttp(
        name="MCP Unidades",
        params={"url": URL},
        cache_tools_list=True,  # o catálogo de tools não muda: evita um list_tools por chamada de rede
    ) as mcp_unidades:

        agente = Agent(
            name="Assistente CISP",
            instructions=(
                "Você ajuda operadores da CISP a encontrar a unidade policial certa para "
                "cada ocorrência. Use as ferramentas do MCP Unidades para responder com dados reais."
            ),
            mcp_servers=[mcp_unidades],
        )

        print(f"Server MCP: {URL}")
        print(f"Pergunta  : {pergunta}")
        resultado = await Runner.run(agente, pergunta)

        # O que o LLM decidiu enviar para a tool (a chamada saiu por HTTP até o server).
        for item in resultado.new_items:
            if type(item).__name__ == "ToolCallItem":
                print(f"\n[tool] {item.raw_item.name}  parametros: {item.raw_item.arguments}")

        print("\n--- Resposta do agente ---")
        print(resultado.final_output)


if __name__ == "__main__":
    asyncio.run(main())
