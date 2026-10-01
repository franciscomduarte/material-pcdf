"""
cliente_teste.py -- JÁ VEM PRONTO. Um cliente MCP mínimo para você testar o seu servidor SEM Claude.

    python cliente_teste.py                              # lista as tools do servidor
    python cliente_teste.py listar_exemplos              # chama uma tool sem argumentos
    python cliente_teste.py mermaid_do_grafo 07_dag      # chama uma tool com 1 argumento (exemplo=...)
    python cliente_teste.py descrever_grafo 07_dag

Por padrão testa o SEU servidor (mcp_grafos.py, nesta pasta). Para testar a solução: defina SERVIDOR.
"""
import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVIDOR = os.getenv("SERVIDOR") or str(Path(__file__).resolve().parent / "mcp_grafos.py")


async def main(argumentos: list[str]) -> None:
    params = StdioServerParameters(command=sys.executable, args=[SERVIDOR])
    with open(os.devnull, "w") as silencio:
        async with stdio_client(params, errlog=silencio) as (leitura, escrita):
            async with ClientSession(leitura, escrita) as sessao:
                await sessao.initialize()
                if not argumentos:
                    print("Tools do servidor:")
                    for tool in (await sessao.list_tools()).tools:
                        print(f"  - {tool.name}: {(tool.description or '').splitlines()[0]}")
                    return
                resposta = await sessao.call_tool(argumentos[0], {"exemplo": argumentos[1]} if len(argumentos) > 1 else {})
                if resposta.is_error:
                    print("ERRO da tool:", resposta.content)
                for item in resposta.content:
                    print(item.text)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
