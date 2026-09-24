"""
MCP Server -- OCORRÊNCIAS (CISP)

Versão FINAL deste servidor (acompanha a evolução em exemplos/02, 03, 05).
Expõe 5 capacidades sobre o PostgreSQL de ocorrências:

    listar_tipos_ocorrencia()
    consultar_ocorrencias(regiao, tipo, periodo_dias, limite)
    consultar_ocorrencias_por_regiao(periodo_dias, limite)
    estatisticas_ocorrencias(periodo_dias, agrupar_por)
    comparar_periodos(regiao, tipo, dias_periodo)

Transporte: controlado por MCP_TRANSPORT (stdio | streamable-http).
  - stdio (padrão): usado nos Exemplos 02-11, o agente sobe o processo.
  - streamable-http: usado quando este server roda em container Docker
    próprio (Bloco 5), com o agente conectando por rede.

Rodar isolado com o MCP Inspector:
    npx @modelcontextprotocol/inspector python server.py
"""
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from mcp.server.mcpserver import MCPServer

from database import query

mcp = MCPServer("ocorrencias-mcp")


def _sanitizar(valor: Any) -> Any:
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return valor


def _sanitizar_linhas(linhas: list[dict]) -> list[dict]:
    return [{k: _sanitizar(v) for k, v in linha.items()} for linha in linhas]


@mcp.tool()
def listar_tipos_ocorrencia() -> list[dict]:
    """Lista os tipos de ocorrência cadastrados (código, nome, categoria, gravidade típica).

    Use esta ferramenta ANTES de filtrar consultar_ocorrencias por tipo, para
    descobrir quais códigos de tipo existem (ex.: 'ROUBO', 'FURTO').
    """
    linhas = query(
        "SELECT codigo, nome, categoria, gravidade_base FROM tipos_ocorrencia ORDER BY nome;"
    )
    return _sanitizar_linhas(linhas)


@mcp.tool()
def consultar_ocorrencias(
    regiao: str | None = None,
    tipo: str | None = None,
    periodo_dias: int = 30,
    limite: int = 50,
) -> list[dict]:
    """Consulta ocorrências recentes, com filtros opcionais.

    Args:
        regiao: nome ou parte do nome da região (ex.: 'Bravo'). Opcional.
        tipo: código do tipo de ocorrência (ex.: 'ROUBO'). Use listar_tipos_ocorrencia
            para descobrir os códigos válidos. Opcional.
        periodo_dias: quantos dias para trás considerar (padrão 30).
        limite: número máximo de ocorrências retornadas (padrão 50, máx. 200).
    """
    limite = min(max(limite, 1), 200)
    condicoes = ["o.data_hora >= NOW() - (%s || ' days')::interval"]
    params: list = [periodo_dias]

    if regiao:
        condicoes.append("r.nome ILIKE %s")
        params.append(f"%{regiao}%")
    if tipo:
        condicoes.append("t.codigo = %s")
        params.append(tipo.upper())

    sql = f"""
        SELECT o.id, o.data_hora, t.codigo AS tipo, r.nome AS regiao,
               o.gravidade, o.status, u.nome AS unidade_responsavel,
               o.latitude, o.longitude
        FROM ocorrencias o
        JOIN tipos_ocorrencia t ON t.id = o.tipo_ocorrencia_id
        JOIN regioes r ON r.id = o.regiao_id
        JOIN unidades u ON u.id = o.unidade_responsavel_id
        WHERE {' AND '.join(condicoes)}
        ORDER BY o.data_hora DESC
        LIMIT %s;
    """
    params.append(limite)
    return _sanitizar_linhas(query(sql, tuple(params)))


@mcp.tool()
def consultar_ocorrencias_por_regiao(periodo_dias: int = 30, limite: int = 12) -> list[dict]:
    """Ranking de regiões por volume de ocorrências no período (mais ocorrências primeiro).

    Útil para responder perguntas do tipo "quais regiões têm mais ocorrências".
    """
    sql = """
        SELECT r.nome AS regiao, COUNT(*) AS total_ocorrencias
        FROM ocorrencias o
        JOIN regioes r ON r.id = o.regiao_id
        WHERE o.data_hora >= NOW() - (%s || ' days')::interval
        GROUP BY r.nome
        ORDER BY total_ocorrencias DESC
        LIMIT %s;
    """
    return _sanitizar_linhas(query(sql, (periodo_dias, limite)))


@mcp.tool()
def estatisticas_ocorrencias(periodo_dias: int = 30, agrupar_por: str = "tipo") -> list[dict]:
    """Estatísticas agregadas de ocorrências no período.

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
    return _sanitizar_linhas(query(sql, (periodo_dias,)))


@mcp.tool()
def comparar_periodos(
    regiao: str | None = None,
    tipo: str | None = None,
    dias_periodo: int = 30,
) -> dict:
    """Compara o volume de ocorrências entre dois períodos consecutivos (crescimento/queda).

    Compara os últimos `dias_periodo` dias contra os `dias_periodo` dias
    anteriores a esse. Use para identificar tendências (ex.: "regiões com
    maior crescimento de roubos nos últimos 30 dias").

    Args:
        regiao: nome ou parte do nome da região. Opcional (sem filtro = todas).
        tipo: código do tipo de ocorrência. Opcional (sem filtro = todos).
        dias_periodo: tamanho de cada período em dias (padrão 30).
    """
    condicoes = []
    params_base: list = []
    if regiao:
        condicoes.append("r.nome ILIKE %s")
        params_base.append(f"%{regiao}%")
    if tipo:
        condicoes.append("t.codigo = %s")
        params_base.append(tipo.upper())
    filtro_extra = (" AND " + " AND ".join(condicoes)) if condicoes else ""

    sql = f"""
        SELECT
            COUNT(*) FILTER (
                WHERE o.data_hora >= NOW() - (%s || ' days')::interval
            ) AS periodo_recente,
            COUNT(*) FILTER (
                WHERE o.data_hora >= NOW() - (%s || ' days')::interval
                  AND o.data_hora <  NOW() - (%s || ' days')::interval
            ) AS periodo_anterior
        FROM ocorrencias o
        JOIN tipos_ocorrencia t ON t.id = o.tipo_ocorrencia_id
        JOIN regioes r ON r.id = o.regiao_id
        WHERE 1=1 {filtro_extra};
    """
    params = [dias_periodo, dias_periodo * 2, dias_periodo, *params_base]
    linhas = query(sql, tuple(params))
    recente = linhas[0]["periodo_recente"] or 0
    anterior = linhas[0]["periodo_anterior"] or 0
    variacao_pct = ((recente - anterior) / anterior * 100) if anterior else None

    return {
        "regiao": regiao,
        "tipo": tipo,
        "dias_periodo": dias_periodo,
        "periodo_recente": recente,
        "periodo_anterior": anterior,
        "variacao_pct": round(variacao_pct, 1) if variacao_pct is not None else None,
    }


if __name__ == "__main__":
    transporte = os.getenv("MCP_TRANSPORT", "stdio")
    if transporte == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "8001")),
        )
    else:
        mcp.run(transport="stdio")
