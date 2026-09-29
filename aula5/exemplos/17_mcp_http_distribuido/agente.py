"""
Exemplo 17 -- AGENTE com vários MCP Servers remotos e tolerância a falhas.

    AGENTE --(HTTP)--> MCP Unidades     (Exemplo 14, aberto,   porta 8000)
           --(HTTP)--> MCP Protocolos   (Exemplo 16, com token, porta 8010)

No Exemplo 07 o agente falava com dois servers stdio: subprocessos filhos dele,
que nascem e morrem junto com o agente. Aqui os servers são serviços independentes,
possivelmente em máquinas e equipes diferentes, e isso traz um problema novo:
**um server pode estar fora do ar**.

Este agente trata isso de forma explícita:
  1. tenta conectar em cada server; o que não responde é descartado, não derruba tudo;
  2. avisa ao LLM quais fontes estão disponíveis, para ele NÃO inventar dados de
     uma fonte que caiu;
  3. mostra no terminal o estado de cada conexão.

Pré-requisito: os servers dos Exemplos 14 e 16 rodando (dois terminais):
    cd ../14_mcp_http_basico       && python server.py
    cd ../16_mcp_http_autenticado  && MCP_TOKEN=segredo python server.py

Rodar (o MESMO MCP_TOKEN do server 16):
    PowerShell: $env:MCP_TOKEN = "segredo"; python agente.py
    bash:       MCP_TOKEN=segredo python agente.py

Experimento: derrube um dos servers (Ctrl+C) e rode de novo.

Variáveis de ambiente:
    MCP_TOKEN            token do MCP Protocolos
    MCP_UNIDADES_URL     padrão http://127.0.0.1:8000/mcp
    MCP_PROTOCOLOS_URL   padrão http://127.0.0.1:8010/mcp
"""
import asyncio
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # aula5/ (provedor.py)

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

from provedor import configurar

configurar()

TOKEN = os.getenv("MCP_TOKEN", "")
URL_UNIDADES = os.getenv("MCP_UNIDADES_URL", "http://127.0.0.1:8000/mcp")
URL_PROTOCOLOS = os.getenv("MCP_PROTOCOLOS_URL", "http://127.0.0.1:8010/mcp")

PERGUNTA_PADRAO = (
    "Consulte a ocorrência de protocolo 2025-000101 e depois liste as unidades "
    "policiais da região onde ela aconteceu."
)

# (nome, o que o server oferece, parâmetros de conexão)
FONTES = [
    ("MCP Unidades", "unidades policiais e suas coordenadas",
     {"url": URL_UNIDADES, "timeout": 5}),
    ("MCP Protocolos", "ocorrências por número de protocolo, com situação e delegado",
     {"url": URL_PROTOCOLOS, "timeout": 5, "headers": {"Authorization": f"Bearer {TOKEN}"}}),
]


async def conectar(pilha: AsyncExitStack):
    """Conecta em cada fonte. Devolve (servers conectados, descrições disponíveis, nomes fora do ar)."""
    conectados, disponiveis, indisponiveis = [], [], []
    for nome, descricao, params in FONTES:
        server = MCPServerStreamableHttp(name=nome, params=params, cache_tools_list=True)
        try:
            await pilha.enter_async_context(server)
        except Exception as erro:  # conexão recusada, timeout, 401 (token errado)
            print(f"  [indisponível] {nome:<15} {params['url']}  ({type(erro).__name__})")
            indisponiveis.append(nome)
        else:
            print(f"  [conectado   ] {nome:<15} {params['url']}")
            conectados.append(server)
            disponiveis.append(f"{nome} ({descricao})")
    return conectados, disponiveis, indisponiveis


async def main():
    if not TOKEN:
        sys.exit("Defina MCP_TOKEN (o mesmo valor do server do Exemplo 16).")
    pergunta = sys.argv[1] if len(sys.argv) > 1 else PERGUNTA_PADRAO

    async with AsyncExitStack() as pilha:
        print("Conectando nas fontes:")
        conectados, disponiveis, indisponiveis = await conectar(pilha)
        if not conectados:
            sys.exit("\nNenhuma fonte de dados disponível: nada a fazer.")

        instrucoes = (
            "Você ajuda operadores da CISP. Responda SOMENTE com dados obtidos das ferramentas.\n"
            f"Fontes disponíveis agora: {'; '.join(disponiveis)}."
        )
        if indisponiveis:
            instrucoes += (
                f"\nFONTES FORA DO AR: {', '.join(indisponiveis)}. Se a pergunta depender delas, "
                "diga claramente que a fonte está indisponível e o que você conseguiu obter sem ela. "
                "NUNCA invente dados."
            )

        agente = Agent(name="Assistente CISP", instructions=instrucoes, mcp_servers=conectados)

        print(f"\nPergunta: {pergunta}")
        resultado = await Runner.run(agente, pergunta)

        for item in resultado.new_items:
            if type(item).__name__ == "ToolCallItem":
                print(f"[tool] {item.raw_item.name}  parametros: {item.raw_item.arguments}")

        print("\n--- Resposta do agente ---")
        print(resultado.final_output)


if __name__ == "__main__":
    asyncio.run(main())
