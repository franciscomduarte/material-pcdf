"""
Exemplo 03 -- EXPLORANDO A TOOL: parâmetros.

Mesmo server do Exemplo 02, mas agora consultar_ocorrencias() recebe
parâmetros (regiao, periodo_dias, tipo). Repare o que muda no SCHEMA da
tool -- é isso que o MCP Inspector (e o LLM) vai enxergar de diferente.

Pergunta da aula: como o LLM sabe QUAIS parâmetros mandar, e com quais
valores? Resposta: pelo nome do parâmetro, pelo tipo Python (str, int,
'| None') e pela docstring -- é a MESMA fonte de informação que ele usa em
function_tool local (Aula 4). MCP não muda essa parte; o que muda é ONDE a
função roda.

    npx @modelcontextprotocol/inspector python server.py
"""
import sys
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from database import query

mcp = MCPServer("ocorrencias-mcp")

# Log do SQL executado. O stdout é do protocolo MCP e o stderr nem sempre chega
# ao terminal de quem rodou o cliente; um arquivo funciona em qualquer ambiente.
LOG_SQL = Path(__file__).resolve().parent / "sql_executado.log"


@mcp.tool()
def consultar_ocorrencias(
    regiao: str | None = None,
    periodo_dias: int = 30,
    tipo: str | None = None,
) -> list[dict]:
    """Consulta ocorrências recentes, com filtros opcionais.

    Args:
        regiao: nome ou parte do nome da região (ex.: 'Bravo'). Opcional.
        periodo_dias: quantos dias para trás considerar (padrão 30).
        tipo: código do tipo de ocorrência (ex.: 'ROUBO', 'FURTO'). Opcional.
    """
    condicoes = ["o.data_hora >= NOW() - (%s || ' days')::interval"]
    params: list = [periodo_dias]

    if regiao:
        condicoes.append("r.nome ILIKE %s")
        params.append(f"%{regiao}%")
    if tipo:
        condicoes.append("t.codigo = %s")
        params.append(tipo.upper())

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
    sql_linha = " ".join(sql.split())
    print(f"SQL executado: {sql_linha}", file=sys.stderr)  # stderr, nunca stdout
    print(f"Parâmetros: {params}", file=sys.stderr)
    with open(LOG_SQL, "a", encoding="utf-8") as f:
        f.write(f"SQL executado: {sql_linha}\nParâmetros: {params}\n")
    return query(sql, tuple(params))


if __name__ == "__main__":
    mcp.run(transport="stdio")
