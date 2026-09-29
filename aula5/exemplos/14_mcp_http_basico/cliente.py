"""
Cliente do Exemplo 14 -- fala com o MCP Server por HTTP, sem agente.

Compare com o cliente do Exemplo 02: lá o cliente usava `stdio_client` e
SUBIA o server. Aqui ele só recebe uma URL. O server já está de pé, talvez em
outra máquina; o cliente não sabe nem precisa saber.

O resto (ClientSession, initialize, list_tools, call_tool) é IDÊNTICO ao stdio.
É a prova de que o transporte é só o "cano"; o protocolo por cima não muda.

Rodar (com o server do Exemplo 14 já rodando em outro terminal):
    python cliente.py
    MCP_URL=http://192.168.0.10:8000/mcp python cliente.py     # server em outra máquina
    (PowerShell: $env:MCP_URL = "http://192.168.0.10:8000/mcp"; python cliente.py)
"""
import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp")


async def main():
    print(f"Conectando em {URL}\n")
    # Único ponto que muda em relação ao stdio: streamable_http_client(url).
    async with streamable_http_client(URL) as (leitura, escrita):
        async with ClientSession(leitura, escrita) as sessao:
            await sessao.initialize()

            print("--- Tools descobertas (list_tools) ---")
            ferramentas = await sessao.list_tools()
            for t in ferramentas.tools:
                print(f"  {t.name}: {t.description.splitlines()[0]}")

            print("\n--- listar_unidades(regiao='BRAVO') ---")
            resposta = await sessao.call_tool("listar_unidades", {"regiao": "BRAVO"})
            for item in resposta.content:
                u = json.loads(item.text)
                print(f"  {u['codigo']:<14} {u['nome']}")

            print("\n--- unidade_mais_proxima(-23.50, -46.55) ---")
            resposta = await sessao.call_tool(
                "unidade_mais_proxima", {"latitude": -23.50, "longitude": -46.55}
            )
            u = json.loads(resposta.content[0].text)
            print(f"  {u['nome']} a {u['distancia_km']} km")


if __name__ == "__main__":
    asyncio.run(main())
