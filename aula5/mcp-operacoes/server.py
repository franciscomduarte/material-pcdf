"""
MCP Server -- OPERAÇÕES (CISP)

Versão FINAL deste servidor (acompanha a evolução em exemplos/06, 08).
Expõe 5 capacidades sobre o SQL Server de operações:

    consultar_unidades(regiao)
    consultar_viaturas(unidade, status)
    consultar_viaturas_disponiveis(unidade, regiao)
    consultar_equipes(unidade, especialidade)
    consultar_disponibilidade(regiao)

Transporte: controlado por MCP_TRANSPORT (stdio | streamable-http), igual
ao MCP Ocorrências.

Rodar isolado com o MCP Inspector:
    npx @modelcontextprotocol/inspector python server.py
"""
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from mcp.server.mcpserver import MCPServer

from database import query

mcp = MCPServer("operacoes-mcp")


def _sanitizar(valor: Any) -> Any:
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return valor


def _sanitizar_linhas(linhas: list[dict]) -> list[dict]:
    return [{k: _sanitizar(v) for k, v in linha.items()} for linha in linhas]


@mcp.tool()
def consultar_unidades(regiao: str | None = None) -> list[dict]:
    """Lista as unidades operacionais (delegacias, batalhões, bases) da CISP.

    Args:
        regiao: filtra por nome da região (ex.: 'Bravo'). Opcional -- sem
            filtro, retorna todas as unidades.
    """
    if regiao:
        sql = "SELECT codigo, nome, regiao, tipo, latitude, longitude FROM unidades WHERE regiao LIKE %s ORDER BY nome;"
        return _sanitizar_linhas(query(sql, (f"%{regiao}%",)))
    sql = "SELECT codigo, nome, regiao, tipo, latitude, longitude FROM unidades ORDER BY nome;"
    return _sanitizar_linhas(query(sql))


@mcp.tool()
def consultar_viaturas(unidade: str | None = None, status: str | None = None) -> list[dict]:
    """Consulta viaturas, com filtros opcionais por unidade e status.

    Args:
        unidade: código ou nome (parcial) da unidade (ex.: 'DP-BRAVO-01'). Opcional.
        status: DISPONIVEL, EM_ATENDIMENTO, EM_DESLOCAMENTO, MANUTENCAO ou
            INDISPONIVEL. Opcional.
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
        SELECT v.prefixo, v.tipo, v.status, u.codigo AS unidade, u.nome AS unidade_nome,
               v.latitude, v.longitude, v.ultima_atualizacao
        FROM viaturas v
        JOIN unidades u ON u.id = v.unidade_id
        {where}
        ORDER BY v.prefixo;
    """
    return _sanitizar_linhas(query(sql, tuple(params)))


@mcp.tool()
def consultar_viaturas_disponiveis(unidade: str | None = None, regiao: str | None = None) -> list[dict]:
    """Consulta apenas viaturas com status DISPONIVEL, opcionalmente filtradas
    por unidade ou por região.

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
        SELECT v.prefixo, v.tipo, u.codigo AS unidade, u.nome AS unidade_nome, u.regiao,
               v.latitude, v.longitude, v.ultima_atualizacao
        FROM viaturas v
        JOIN unidades u ON u.id = v.unidade_id
        WHERE {' AND '.join(condicoes)}
        ORDER BY u.regiao, v.prefixo;
    """
    return _sanitizar_linhas(query(sql, tuple(params)))


@mcp.tool()
def consultar_equipes(unidade: str | None = None, especialidade: str | None = None) -> list[dict]:
    """Consulta equipes cadastradas, com filtros opcionais por unidade e especialidade.

    Args:
        unidade: código ou nome (parcial) da unidade. Opcional.
        especialidade: PATRULHAMENTO, INVESTIGACAO, TATICO ou TRANSITO. Opcional.
    """
    condicoes = []
    params: list = []
    if unidade:
        condicoes.append("(u.codigo = %s OR u.nome LIKE %s)")
        params.extend([unidade, f"%{unidade}%"])
    if especialidade:
        condicoes.append("e.especialidade = %s")
        params.append(especialidade.upper())
    where = ("WHERE " + " AND ".join(condicoes)) if condicoes else ""

    sql = f"""
        SELECT u.codigo AS unidade, u.nome AS unidade_nome, e.turno,
               e.quantidade_agentes, e.especialidade, e.status
        FROM equipes e
        JOIN unidades u ON u.id = e.unidade_id
        {where}
        ORDER BY u.codigo, e.turno;
    """
    return _sanitizar_linhas(query(sql, tuple(params)))


@mcp.tool()
def consultar_disponibilidade(regiao: str | None = None) -> list[dict]:
    """Resumo de disponibilidade operacional por região: total de viaturas,
    quantas estão disponíveis, total de equipes e quantas estão em serviço.

    Args:
        regiao: filtra por nome (parcial) da região. Opcional -- sem filtro,
            retorna o resumo de todas as regiões.
    """
    filtro = "WHERE u.regiao LIKE %s" if regiao else ""
    params = (f"%{regiao}%",) if regiao else ()

    # COUNT(DISTINCT ...) em tudo -- não SUM(CASE ...) -- porque o LEFT JOIN
    # simultâneo com viaturas E equipes produz um produto cartesiano parcial
    # por unidade (n_viaturas x n_equipes linhas); SUM contaria cada viatura
    # uma vez por equipe da mesma unidade, inflando o resultado.
    sql = f"""
        SELECT u.regiao,
               COUNT(DISTINCT v.id) AS total_viaturas,
               COUNT(DISTINCT CASE WHEN v.status = 'DISPONIVEL' THEN v.id END) AS viaturas_disponiveis,
               COUNT(DISTINCT e.id) AS total_equipes,
               COUNT(DISTINCT CASE WHEN e.status = 'EM_SERVICO' THEN e.id END) AS equipes_em_servico
        FROM unidades u
        LEFT JOIN viaturas v ON v.unidade_id = u.id
        LEFT JOIN equipes e ON e.unidade_id = u.id
        {filtro}
        GROUP BY u.regiao
        ORDER BY u.regiao;
    """
    linhas = _sanitizar_linhas(query(sql, params))
    for linha in linhas:
        total = linha["total_viaturas"] or 0
        disp = linha["viaturas_disponiveis"] or 0
        linha["percentual_disponivel"] = round(disp / total * 100, 1) if total else 0.0
    return linhas


if __name__ == "__main__":
    transporte = os.getenv("MCP_TRANSPORT", "stdio")
    if transporte == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "8002")),
        )
    else:
        mcp.run(transport="stdio")
