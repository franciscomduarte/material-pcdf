"""
Exemplo 16 -- MCP Server via HTTP com AUTENTICAÇÃO (Bearer token).

No stdio, quem falava com o server era o processo-pai, que o próprio cliente
subiu: a "autenticação" era o sistema operacional. Em HTTP, qualquer máquina
que alcance a porta consegue chamar as tools. Sem autenticação, um server
com dados sensíveis vira uma API pública.

Aqui o server só atende quem enviar o cabeçalho:

    Authorization: Bearer <token>

A checagem fica num middleware ASGI, ANTES do MCP: uma requisição sem token
válido recebe 401 e nem chega a `initialize`. As tools não sabem que existe
autenticação; o código delas é igual ao dos exemplos anteriores.

Isto é o mínimo para a aula. Em produção, o MCP oferece um fluxo OAuth 2.1
completo (o SDK aceita `token_verifier` e `AuthSettings` no MCPServer), com
tokens emitidos por um servidor de autorização, expiração e escopos.

Tools:
    consultar_ocorrencia(protocolo)     dado sensível: por isso a autenticação
    listar_protocolos()

Rodar (o token é OBRIGATÓRIO; o server se recusa a subir sem ele):
    PowerShell: $env:MCP_TOKEN = "troque-por-um-segredo"; python server.py
    bash:       MCP_TOKEN=troque-por-um-segredo python server.py

Variáveis de ambiente:
    MCP_TOKEN  segredo esperado no cabeçalho Authorization (obrigatório)
    MCP_HOST   interface onde escutar. Padrão 127.0.0.1; 0.0.0.0 aceita outras máquinas.
    MCP_PORT   porta. Padrão 8010.

Endereço do server: http://127.0.0.1:8010/mcp
"""
import hmac
import os
import sys

import uvicorn
from mcp.server.mcpserver import MCPServer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

mcp = MCPServer("protocolos-mcp")

# Dados fictícios. O ponto é serem "sigilosos": só quem tem o token os enxerga.
OCORRENCIAS = {
    "2025-000101": {"protocolo": "2025-000101", "tipo": "Roubo de Veículo", "regiao": "BRAVO",
                    "gravidade": "ALTA", "situacao": "EM INVESTIGAÇÃO", "delegado_responsavel": "Dra. Helena Prado"},
    "2025-000102": {"protocolo": "2025-000102", "tipo": "Violência Doméstica", "regiao": "KILO",
                    "gravidade": "ALTA", "situacao": "MEDIDA PROTETIVA EMITIDA", "delegado_responsavel": "Dr. Marcos Vidal"},
    "2025-000103": {"protocolo": "2025-000103", "tipo": "Furto em Comércio", "regiao": "ALFA",
                    "gravidade": "BAIXA", "situacao": "ARQUIVADA", "delegado_responsavel": "Dr. Otávio Lemos"},
}


@mcp.tool()
def listar_protocolos() -> list[str]:
    """Lista os números de protocolo das ocorrências registradas."""
    return sorted(OCORRENCIAS)


@mcp.tool()
def consultar_ocorrencia(protocolo: str) -> dict:
    """Consulta uma ocorrência pelo número de protocolo, com situação e delegado responsável.

    Args:
        protocolo: número do protocolo, no formato AAAA-NNNNNN (ex.: 2025-000101).
    """
    ocorrencia = OCORRENCIAS.get(protocolo)
    if ocorrencia is None:
        raise ValueError(f"Protocolo {protocolo} não encontrado.")
    return ocorrencia


class ExigeToken(BaseHTTPMiddleware):
    """Barra qualquer requisição sem `Authorization: Bearer <token>` válido."""

    def __init__(self, app, token: str):
        super().__init__(app)
        self._token = token

    async def dispatch(self, request, call_next):
        recebido = request.headers.get("authorization", "")
        esquema, _, valor = recebido.partition(" ")
        # compare_digest compara em tempo constante: não vaza, pelo tempo de resposta,
        # quantos caracteres do token estavam certos.
        if esquema.lower() != "bearer" or not hmac.compare_digest(valor, self._token):
            return JSONResponse(
                {"erro": "não autorizado"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await call_next(request)


if __name__ == "__main__":
    token = os.getenv("MCP_TOKEN", "")
    if not token:
        sys.exit("Defina MCP_TOKEN antes de subir o server (ver instruções no topo do arquivo).")

    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8010"))

    # Diferente do Exemplo 14 (mcp.run), aqui pegamos o app ASGI para colocar o middleware na frente.
    app = mcp.streamable_http_app(host=host)
    app.add_middleware(ExigeToken, token=token)

    print(f"MCP Server (com autenticação) em http://{host}:{port}/mcp  (Ctrl+C para parar)")
    uvicorn.run(app, host=host, port=port)
