"""
Exemplo 12 (Observabilidade) -- responder, para qualquer execução do agente:

    Qual ferramenta foi chamada? Com quais parâmetros? Qual MCP Server
    recebeu a requisição? Qual foi o resultado? Onde ocorreu um erro?

O Agent Framework já registra cada chamada de tool em `result.new_items`.
Este exemplo não muda nenhum MCP Server -- só faz uma leitura estruturada
do que já aconteceu durante Runner.run(), reutilizando os MCP Servers
finais (Ocorrências + Operações + Serviços) do Exemplo 09.

Rodar:
    python agente_observavel.py
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from provedor import configurar

configurar()

RAIZ = Path(__file__).resolve().parents[2]
SERVER_OCORRENCIAS = str(RAIZ / "mcp-ocorrencias" / "server.py")
SERVER_OPERACOES = str(RAIZ / "mcp-operacoes" / "server.py")
SERVER_SERVICOS = str(RAIZ / "mcp-servicos" / "server.py")


def imprimir_trilha(resultado):
    """Percorre result.new_items e imprime cada chamada de tool MCP:
    nome, servidor, parâmetros, resultado (ou erro)."""
    print("\n" + "=" * 70)
    print("TRILHA DE EXECUÇÃO (observabilidade)")
    print("=" * 70)
    chamadas = {}  # call_id -> dict com name/args/servidor
    n_chamadas = 0
    for item in resultado.new_items:
        tipo_item = type(item).__name__
        if tipo_item == "ToolCallItem":
            raw = item.raw_item
            call_id = getattr(raw, "call_id", None)
            nome = getattr(raw, "name", "?")
            args = getattr(raw, "arguments", "{}")
            servidor = getattr(item.tool_origin, "mcp_server_name", None) if item.tool_origin else None
            n_chamadas += 1
            chamadas[call_id] = {"n": n_chamadas, "nome": nome, "args": args, "servidor": servidor}
            print(f"\n[{n_chamadas}] tool={nome!r}  servidor={servidor!r}")
            print(f"    parametros: {args}")
        elif tipo_item == "ToolCallOutputItem":
            call_id = item.call_id
            info = chamadas.get(call_id, {})
            saida = str(item.output)
            print(f"    resultado (tool #{info.get('n', '?')}, {len(saida)} chars): {saida[:200]}{'...' if len(saida) > 200 else ''}")
    print(f"\nTotal de chamadas a tools: {n_chamadas}")
    print("=" * 70)


async def main():
    async with MCPServerStdio(
        name="MCP Ocorrências",
        params={"command": "python", "args": [SERVER_OCORRENCIAS]},
    ) as mcp_ocorrencias, MCPServerStdio(
        name="MCP Operações",
        params={"command": "python", "args": [SERVER_OPERACOES]},
    ) as mcp_operacoes, MCPServerStdio(
        name="MCP Serviços",
        params={"command": "python", "args": [SERVER_SERVICOS]},
    ) as mcp_servicos:

        agente = Agent(
            name="Assistente Analítico CISP",
            instructions=(
                "Você integra os MCP Servers Ocorrências, Operações e Serviços "
                "da CISP para responder perguntas analíticas."
            ),
            mcp_servers=[mcp_ocorrencias, mcp_operacoes, mcp_servicos],
        )

        pergunta = (
            "Quais as 2 regiões com mais ocorrências nos últimos 30 dias? "
            "Para cada uma, diga quantas viaturas disponíveis a unidade "
            "principal tem."
        )

        inicio = time.perf_counter()
        resultado = await Runner.run(agente, pergunta, max_turns=15)
        duracao = time.perf_counter() - inicio

        print(resultado.final_output)
        imprimir_trilha(resultado)
        print(f"\nTempo total da execução: {duracao:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
