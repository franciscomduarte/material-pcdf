"""
Exemplo 08 -- OPERAÇÕES: viaturas.

Problema que apareceu no Exemplo 07: sabemos quais unidades atendem as
regiões mais violentas, mas não sabemos se elas TÊM RECURSO. Precisamos
de viaturas. Adicionamos duas tools ao MCP Operações:

    consultar_viaturas(unidade, status)
    consultar_viaturas_disponiveis(unidade, regiao)

(Apesar do nome da pasta "08_mcp_servicos", este arquivo ainda é o MCP
OPERAÇÕES evoluindo -- o MCP Serviços puro entra no próximo passo da aula,
reaproveitando mcp-servicos/server.py. A pasta 08 reúne os dois porque a
pergunta deste bloco usa os dois.)

    npx @modelcontextprotocol/inspector python server_operacoes.py
"""
from mcp.server.mcpserver import MCPServer

from database import query

mcp = MCPServer("operacoes-mcp")


@mcp.tool()
def consultar_unidades(regiao: str | None = None) -> list[dict]:
    """Lista unidades operacionais, opcionalmente filtradas por região.

    Args:
        regiao: nome (parcial) da região. Opcional.
    """
    if regiao:
        return query(
            "SELECT codigo, nome, regiao, tipo, latitude, longitude FROM unidades WHERE regiao LIKE %s ORDER BY nome;",
            (f"%{regiao}%",),
        )
    return query("SELECT codigo, nome, regiao, tipo, latitude, longitude FROM unidades ORDER BY nome;")


@mcp.tool()
def consultar_viaturas(unidade: str | None = None, status: str | None = None) -> list[dict]:
    """Consulta viaturas, com filtros opcionais por unidade e status.

    Args:
        unidade: código ou nome (parcial) da unidade. Opcional.
        status: DISPONIVEL, EM_ATENDIMENTO, EM_DESLOCAMENTO, MANUTENCAO ou INDISPONIVEL. Opcional.
    """
    condicoes = []
    params: list = []
    if unidade:
        condicoes.append("(u.codigo = %s OR u.nome LIKE %s)")
        params.extend([unidade, f"%{unidade}%"])
    if status:
        condicoes.append("v.status = %s")
        params.append(status.upper())
    where = ("WHERE " + " AND ".join(condicoes)) if condicoes else ""
    sql = f"""
        SELECT v.prefixo, v.tipo, v.status, u.codigo AS unidade, u.nome AS unidade_nome
        FROM viaturas v JOIN unidades u ON u.id = v.unidade_id
        {where} ORDER BY v.prefixo;
    """
    return query(sql, tuple(params))


@mcp.tool()
def consultar_viaturas_disponiveis(unidade: str | None = None, regiao: str | None = None) -> list[dict]:
    """Consulta apenas viaturas DISPONIVEL, opcionalmente filtradas por unidade ou região.

    Args:
        unidade: código ou nome (parcial) da unidade. Opcional.
        regiao: nome (parcial) da região. Opcional.
    """
    condicoes = ["v.status = 'DISPONIVEL'"]
    params: list = []
    if unidade:
        condicoes.append("(u.codigo = %s OR u.nome LIKE %s)")
        params.extend([unidade, f"%{unidade}%"])
    if regiao:
        condicoes.append("u.regiao LIKE %s")
        params.append(f"%{regiao}%")
    sql = f"""
        SELECT v.prefixo, v.tipo, u.codigo AS unidade, u.nome AS unidade_nome, u.regiao
        FROM viaturas v JOIN unidades u ON u.id = v.unidade_id
        WHERE {' AND '.join(condicoes)} ORDER BY u.regiao, v.prefixo;
    """
    return query(sql, tuple(params))


if __name__ == "__main__":
    mcp.run(transport="stdio")
