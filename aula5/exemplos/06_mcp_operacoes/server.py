"""
Exemplo 06 -- SEGUNDO SISTEMA: MCP Operações.

Mesmo padrão do Exemplo 02, agora sobre o SQL Server de Operações. Uma
única tool, sem parâmetros ainda: consultar_unidades().

Note o que NÃO muda em relação ao MCP Ocorrências: a forma de declarar
o server (MCPServer(...)), o decorator (@mcp.tool()), o jeito de rodar
(mcp.run(transport="stdio")). O que muda é só o database.py por trás --
e o agente, do lado de fora, nem vai perceber a diferença.

    npx @modelcontextprotocol/inspector python server.py
"""
from mcp.server.mcpserver import MCPServer

from database import query

mcp = MCPServer("operacoes-mcp")


@mcp.tool()
def consultar_unidades() -> list[dict]:
    """Lista as unidades operacionais (delegacias, batalhões, bases) da CISP."""
    return query("SELECT codigo, nome, regiao, tipo FROM unidades ORDER BY nome;")


if __name__ == "__main__":
    mcp.run(transport="stdio")
