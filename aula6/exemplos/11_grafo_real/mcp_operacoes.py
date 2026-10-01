"""
MCP Server do exemplo 11 -- duas tools, nenhuma IA:

    listar_eventos(regiao, data_inicio, data_fim)   lê a planilha eventos.csv
    estimar_efetivo(publico_total, dias_feriado)    cálculo de dimensionamento

É o mesmo papel do MCP Eventos e do MCP Serviços da Aula 5, num único arquivo
para a Aula 6 não depender de banco. Quem sobe este processo é o nó do grafo
(via stdio); o grafo só conhece o NOME da tool e seus parâmetros.

Testar isolado:
    npx @modelcontextprotocol/inspector python mcp_operacoes.py
"""
import csv
from datetime import date
from math import ceil
from pathlib import Path

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("operacoes-mcp")

CSV = Path(__file__).resolve().parent / "eventos.csv"


@mcp.tool()
def listar_eventos(regiao: str, data_inicio: str, data_fim: str) -> list[dict]:
    """Lista os eventos (jogos, shows, feiras, manifestações) de uma região num período.

    Args:
        regiao: nome ou parte do nome da região (ex.: 'Bravo').
        data_inicio: data inicial, AAAA-MM-DD, inclusive.
        data_fim: data final, AAAA-MM-DD, inclusive.
    """
    try:
        inicio, fim = date.fromisoformat(data_inicio), date.fromisoformat(data_fim)
    except ValueError:
        return [{"erro": "Datas inválidas. Use o formato AAAA-MM-DD."}]

    eventos = []
    with open(CSV, encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            if regiao.strip().casefold() not in linha["regiao"].casefold():
                continue
            if not inicio <= date.fromisoformat(linha["data"]) <= fim:
                continue
            eventos.append({
                "data": linha["data"],
                "nome": linha["nome"],
                "tipo_evento": linha["tipo_evento"],
                "publico_estimado": int(linha["publico_estimado"] or 0),
            })
    return sorted(eventos, key=lambda e: e["data"])


@mcp.tool()
def estimar_efetivo(publico_total: int, dias_feriado: int = 0) -> dict:
    """Estima o efetivo e as viaturas necessários para um período.

    Regra didática (não é norma real): 1 policial para cada 500 pessoas de público
    estimado, mais 10 por dia de feriado; 1 viatura para cada 4 policiais.

    Args:
        publico_total: soma do público estimado dos eventos do período.
        dias_feriado: quantos dias do período são feriado.
    """
    efetivo = ceil(publico_total / 500) + 10 * dias_feriado
    return {"efetivo": efetivo, "viaturas": ceil(efetivo / 4)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
