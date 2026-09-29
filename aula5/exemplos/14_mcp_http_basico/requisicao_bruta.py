"""
Exemplo 14 (extra) -- MCP por HTTP SEM a biblioteca MCP.

O objetivo é desmistificar: o transporte Streamable HTTP é só `POST` de JSON
(JSON-RPC 2.0) para uma URL. Aqui fazemos à mão a mesma conversa que o
`ClientSession` faz por baixo:

    1. POST initialize                   -> o server devolve um Mcp-Session-Id (cabeçalho)
    2. POST notifications/initialized    -> "handshake concluído"
    3. POST tools/list                   -> catálogo de tools
    4. POST tools/call                   -> executa uma tool

Todas as requisições seguintes repetem o cabeçalho Mcp-Session-Id. É isso que
liga as chamadas à mesma sessão.

O equivalente em curl (bash) do passo 1:
    curl -i http://127.0.0.1:8000/mcp \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'

Rodar (com o server do Exemplo 14 já rodando):
    python requisicao_bruta.py
"""
import json
import os

import httpx2 as httpx  # é o cliente HTTP que o SDK MCP 2.x já instala

URL = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp")
CABECALHOS = {
    "Content-Type": "application/json",
    # O server escolhe responder em JSON puro ou em stream SSE; o cliente precisa aceitar os dois.
    "Accept": "application/json, text/event-stream",
}


def ler_resposta(resp: httpx.Response) -> dict:
    """A resposta vem como JSON puro ou como SSE (linhas 'data: {...}')."""
    if resp.headers.get("content-type", "").startswith("text/event-stream"):
        for linha in resp.text.splitlines():
            if linha.startswith("data:"):
                return json.loads(linha[len("data:"):].strip())
        return {}
    return resp.json() if resp.content else {}


def mostrar(titulo: str, envio: dict, resp: httpx.Response) -> dict:
    print(f"=== {titulo} ===")
    print(">>> POST", URL)
    print(">>>", json.dumps(envio, ensure_ascii=False))
    corpo = ler_resposta(resp)
    print(f"<<< HTTP {resp.status_code}  content-type: {resp.headers.get('content-type')}")
    print("<<<", json.dumps(corpo, ensure_ascii=False)[:300])
    print()
    return corpo


def main():
    with httpx.Client(timeout=10) as http:
        # 1. initialize
        envio = {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "requisicao-bruta", "version": "0"},
            },
        }
        resp = http.post(URL, json=envio, headers=CABECALHOS)
        mostrar("1. initialize", envio, resp)
        sessao = resp.headers.get("mcp-session-id")
        print(f"Mcp-Session-Id devolvido pelo server: {sessao}\n")
        if sessao:
            CABECALHOS["Mcp-Session-Id"] = sessao

        # 2. notificação (não tem "id" e não espera resposta com conteúdo)
        envio = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        resp = http.post(URL, json=envio, headers=CABECALHOS)
        print(f"=== 2. notifications/initialized ===\n<<< HTTP {resp.status_code}\n")

        # 3. tools/list
        envio = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        resp = http.post(URL, json=envio, headers=CABECALHOS)
        mostrar("3. tools/list", envio, resp)

        # 4. tools/call
        envio = {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "listar_unidades", "arguments": {"regiao": "ALFA"}},
        }
        resp = http.post(URL, json=envio, headers=CABECALHOS)
        mostrar("4. tools/call listar_unidades", envio, resp)


if __name__ == "__main__":
    main()
