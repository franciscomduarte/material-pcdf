"""
Exemplo 05 -- MAIS FERRAMENTAS.

Problema que apareceu no Exemplo 04: para filtrar por `tipo`, o agente
precisa ADIVINHAR o código certo ('ROUBO'? 'roubo'? 'Roubo'?). Ele até
acertou por sorte/contexto, mas isso não escala. A solução não é escrever
uma instrução mais longa -- é dar ao agente uma ferramenta para DESCOBRIR
os tipos válidos: listar_tipos_ocorrencia().

Segunda necessidade: perguntas agregadas ("quais os tipos mais comuns?",
"como está a gravidade das ocorrências?") não devem fazer o agente puxar
50 linhas cruas e somar na cabeça -- por custo (tokens) e por precisão.
Daí estatisticas_ocorrencias(), que agrega no banco.

Este server agora tem 3 tools. O aluno deve perceber: o MCP Server não é
"uma tool" -- é um CONJUNTO de capacidades relacionadas, versionado e
implantado junto.

    npx @modelcontextprotocol/inspector python server.py
"""
from mcp.server.mcpserver import MCPServer

from database import query

mcp = MCPServer("ocorrencias-mcp")


@mcp.tool()
def listar_tipos_ocorrencia() -> list[dict]:
    """Lista os tipos de ocorrência cadastrados (código, nome, categoria, gravidade típica).

    Use esta ferramenta ANTES de filtrar consultar_ocorrencias por tipo, para
    descobrir quais códigos de tipo existem (ex.: 'ROUBO', 'FURTO').
    """
    return query("SELECT codigo, nome, categoria, gravidade_base FROM tipos_ocorrencia ORDER BY nome;")


@mcp.tool()
def consultar_ocorrencias(
    regiao: str | None = None,
    periodo_dias: int = 30,
    tipo: str | None = None,
    gravidade: str | None = None,
) -> list[dict]:
    """Consulta ocorrências recentes, com filtros opcionais.

    Args:
        regiao: nome ou parte do nome da região (ex.: 'Bravo'). Opcional.
        periodo_dias: quantos dias para trás considerar (padrão 30).
        tipo: código do tipo de ocorrência. Use listar_tipos_ocorrencia
            para descobrir os códigos válidos. Opcional.
        gravidade: BAIXA, MEDIA, ALTA ou CRITICA. Opcional.
    """
    condicoes = ["o.data_hora >= NOW() - (%s || ' days')::interval"]
    params: list = [periodo_dias]
    if regiao:
        condicoes.append("r.nome ILIKE %s")
        params.append(f"%{regiao}%")
    if tipo:
        condicoes.append("t.codigo = %s")
        params.append(tipo.upper())
    if gravidade:
        condicoes.append("o.gravidade = %s")
        params.append(gravidade.upper())

    sql = f"""
        SELECT o.id, o.data_hora::text AS data_hora, t.codigo AS tipo,
               r.nome AS regiao, o.gravidade, o.status
        FROM ocorrencias o
        JOIN tipos_ocorrencia t ON t.id = o.tipo_ocorrencia_id
        JOIN regioes r ON r.id = o.regiao_id
        WHERE {' AND '.join(condicoes)}
        ORDER BY o.data_hora DESC
        LIMIT 50;
    """
    return query(sql, tuple(params))


@mcp.tool()
def estatisticas_ocorrencias(periodo_dias: int = 30, agrupar_por: str = "tipo") -> list[dict]:
    """Estatísticas agregadas de ocorrências no período (contagem por grupo).

    Args:
        periodo_dias: quantos dias para trás considerar (padrão 30).
        agrupar_por: 'tipo', 'gravidade', 'status' ou 'regiao' (padrão 'tipo').
    """
    colunas_validas = {
        "tipo": ("t.nome", "JOIN tipos_ocorrencia t ON t.id = o.tipo_ocorrencia_id"),
        "gravidade": ("o.gravidade", ""),
        "status": ("o.status", ""),
        "regiao": ("r.nome", "JOIN regioes r ON r.id = o.regiao_id"),
    }
    coluna, join_extra = colunas_validas.get(agrupar_por, colunas_validas["tipo"])
    sql = f"""
        SELECT {coluna} AS grupo, COUNT(*) AS total
        FROM ocorrencias o
        {join_extra}
        WHERE o.data_hora >= NOW() - (%s || ' days')::interval
        GROUP BY {coluna}
        ORDER BY total DESC;
    """
    return query(sql, (periodo_dias,))


if __name__ == "__main__":
    mcp.run(transport="stdio")
