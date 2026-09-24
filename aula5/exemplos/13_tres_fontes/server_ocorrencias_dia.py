"""
Exemplo 14 -- MCP OCORRÊNCIAS, versão série diária (PostgreSQL).

Para cruzar ocorrências com eventos o agente precisa saber QUANTAS ocorrências
houve em cada DIA de uma região. Esta tool devolve exatamente essa série, e já
marca os dias de pico (>= 1,2 x a média do período).

    npx @modelcontextprotocol/inspector python server_ocorrencias_dia.py
"""
from datetime import date

from mcp.server.mcpserver import MCPServer

from database import query

mcp = MCPServer("ocorrencias-dia-mcp")

FATOR_PICO = 1.2


@mcp.tool()
def ocorrencias_por_dia(regiao: str, data_inicio: str, data_fim: str) -> list[dict]:
    """Total de ocorrências por dia em UMA região, com os dias de pico marcados.
    Use para descobrir em que datas a região teve mais ocorrências que o normal.

    Args:
        regiao: nome ou parte do nome da região (ex.: 'Bravo').
        data_inicio: data inicial, AAAA-MM-DD, inclusive.
        data_fim: data final, AAAA-MM-DD, inclusive.
    """
    if not regiao or not regiao.strip():
        return [{"erro": "Informe a região (ex.: 'Bravo'). Para saber quais regiões têm mais "
                         "ocorrências, use ranking_regioes."}]
    try:
        inicio = date.fromisoformat(data_inicio.strip())
        fim = date.fromisoformat(data_fim.strip())
    except ValueError:
        return [{"erro": "Datas inválidas. Use o formato AAAA-MM-DD (ex.: 2026-09-13)."}]
    if inicio > fim:
        return [{"erro": "data_inicio é posterior a data_fim."}]
    if (fim - inicio).days > 92:
        return [{"erro": "Período longo demais: use no máximo 92 dias por consulta."}]

    sql = """
        SELECT o.data_hora::date::text AS dia, COUNT(*) AS total
        FROM ocorrencias o
        JOIN regioes r ON r.id = o.regiao_id
        WHERE r.nome ILIKE %s
          AND o.data_hora >= %s::date
          AND o.data_hora <  %s::date + 1
        GROUP BY o.data_hora::date
        ORDER BY o.data_hora::date;
    """
    linhas = query(sql, (f"%{regiao}%", inicio.isoformat(), fim.isoformat()))
    if not linhas:
        return []

    media = sum(l["total"] for l in linhas) / len(linhas)
    return [
        {
            "dia": l["dia"],
            "total": l["total"],
            "media_periodo": round(media, 1),
            "pico": l["total"] >= FATOR_PICO * media,
        }
        for l in linhas
    ]


@mcp.tool()
def ranking_regioes(data_inicio: str, data_fim: str, limite: int = 5) -> list[dict]:
    """Ranking das regiões com MAIS ocorrências no período (a região com mais vem primeiro).
    Use para descobrir quais regiões analisar antes de chamar ocorrencias_por_dia.

    Args:
        data_inicio: data inicial, AAAA-MM-DD, inclusive.
        data_fim: data final, AAAA-MM-DD, inclusive.
        limite: quantas regiões devolver (1 a 12; padrão 5).
    """
    try:
        inicio = date.fromisoformat(data_inicio.strip())
        fim = date.fromisoformat(data_fim.strip())
    except ValueError:
        return [{"erro": "Datas inválidas. Use o formato AAAA-MM-DD (ex.: 2026-09-13)."}]
    if inicio > fim:
        return [{"erro": "data_inicio é posterior a data_fim."}]
    if not 1 <= limite <= 12:
        return [{"erro": "limite deve estar entre 1 e 12."}]

    sql = """
        SELECT r.nome AS regiao, COUNT(*) AS total_ocorrencias
        FROM ocorrencias o
        JOIN regioes r ON r.id = o.regiao_id
        WHERE o.data_hora >= %s::date AND o.data_hora < %s::date + 1
        GROUP BY r.nome
        ORDER BY total_ocorrencias DESC
        LIMIT %s;
    """
    return query(sql, (inicio.isoformat(), fim.isoformat(), limite))


if __name__ == "__main__":
    mcp.run(transport="stdio")
