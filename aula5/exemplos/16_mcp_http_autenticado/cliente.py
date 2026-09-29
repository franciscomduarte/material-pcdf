"""
Cliente do Exemplo 16 -- mostra a autenticação funcionando, em três tentativas:

    1. sem token        -> HTTP 401
    2. com token errado -> HTTP 401
    3. com token certo  -> sessão MCP normal, tools chamadas

O token viaja no cabeçalho HTTP `Authorization`. Ele NUNCA vai no código: vem
de variável de ambiente (ver o `.env` da aula 5 e o `.gitignore`).

Rodar (com o server do Exemplo 16 já rodando, com o MESMO MCP_TOKEN):
    PowerShell: $env:MCP_TOKEN = "troque-por-um-segredo"; python cliente.py
    bash:       MCP_TOKEN=troque-por-um-segredo python cliente.py
"""
import asyncio
import json
import os
import sys

import httpx2 as httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = os.getenv("MCP_URL", "http://127.0.0.1:8010/mcp")
TOKEN = os.getenv("MCP_TOKEN", "")

# Mesmo `initialize` mínimo do Exemplo 14 (requisicao_bruta.py), só para provocar uma resposta do server.
INITIALIZE = {
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"protocolVersion": "2025-06-18", "capabilities": {},
               "clientInfo": {"name": "cliente-16", "version": "0"}},
}


def tentar(rotulo: str, token: str | None) -> int:
    cabecalhos = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if token is not None:
        cabecalhos["Authorization"] = f"Bearer {token}"
    resp = httpx.post(URL, json=INITIALIZE, headers=cabecalhos, timeout=10)
    print(f"{rotulo:<16} -> HTTP {resp.status_code}")
    return resp.status_code


async def sessao_autenticada() -> None:
    # O SDK recebe um cliente HTTP já configurado; é aqui que o cabeçalho entra.
    http = httpx.AsyncClient(headers={"Authorization": f"Bearer {TOKEN}"}, timeout=10)
    async with http:
        async with streamable_http_client(URL, http_client=http) as (leitura, escrita):
            async with ClientSession(leitura, escrita) as sessao:
                await sessao.initialize()

                protocolos = await sessao.call_tool("listar_protocolos", {})
                print("Protocolos:", [i.text for i in protocolos.content])

                resposta = await sessao.call_tool("consultar_ocorrencia", {"protocolo": "2025-000101"})
                o = json.loads(resposta.content[0].text)
                print(f"{o['protocolo']}: {o['tipo']} ({o['regiao']}), {o['situacao']}, {o['delegado_responsavel']}")


def main():
    if not TOKEN:
        sys.exit("Defina MCP_TOKEN com o mesmo valor usado no server.")
    print(f"Server: {URL}\n")
    print("--- Tentativas de acesso ---")
    tentar("sem token", None)
    tentar("token errado", "isso-nao-e-o-token")
    if tentar("token correto", TOKEN) == 401:
        sys.exit("\nO server recusou o seu MCP_TOKEN: use o mesmo valor com que o server foi iniciado.")
    print("\n--- Sessão MCP autenticada ---")
    asyncio.run(sessao_autenticada())


if __name__ == "__main__":
    main()
