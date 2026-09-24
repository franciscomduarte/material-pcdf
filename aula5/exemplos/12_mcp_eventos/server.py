"""
Exemplo 13 -- MCP EVENTOS: uma fonte que NÃO é banco de dados.

Os eventos da cidade (jogos, shows, feiras, manifestações) vivem numa planilha
do Google Sheets, mantida por outra área. Este server a expõe como tool.
Para o agente, planilha, banco ou API são a mesma coisa: uma tool com schema.

    npx @modelcontextprotocol/inspector python server.py
"""
import sys
from datetime import date

from mcp.server.mcpserver import MCPServer

from planilha import carregar_eventos

mcp = MCPServer("eventos-mcp")


def _parse_data(valor: str | None, nome: str) -> tuple[date | None, str | None]:
    """Converte 'AAAA-MM-DD'. Devolve (data, erro)."""
    if not valor:
        return None, None
    try:
        return date.fromisoformat(valor.strip()), None
    except ValueError:
        return None, f"{nome} inválida: {valor!r}. Use o formato AAAA-MM-DD (ex.: 2026-09-13)."


@mcp.tool()
def listar_eventos(
    regiao: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    tipo_evento: str | None = None,
) -> list[dict]:
    """Lista eventos da cidade (jogos, shows, feiras, manifestações) registrados
    na planilha de eventos, em ordem de data. Serve para explicar picos de
    ocorrências ou antecipar necessidade de efetivo.

    Args:
        regiao: nome ou parte do nome da região (ex.: 'Bravo'). Opcional.
        data_inicio: data inicial, no formato AAAA-MM-DD, inclusive. Opcional.
        data_fim: data final, no formato AAAA-MM-DD, inclusive. Opcional.
        tipo_evento: JOGO, SHOW, FESTA, FEIRA, CORRIDA, MANIFESTACAO, RELIGIOSO
            ou REUNIAO. Opcional.
    """
    inicio, erro_i = _parse_data(data_inicio, "data_inicio")
    fim, erro_f = _parse_data(data_fim, "data_fim")
    if erro_i or erro_f:
        return [{"erro": erro_i or erro_f}]
    if inicio and fim and inicio > fim:
        return [{"erro": "data_inicio é posterior a data_fim."}]

    eventos, fonte = carregar_eventos()
    resultado = []
    for e in eventos:
        d = date.fromisoformat(e["data"])
        if inicio and d < inicio:
            continue
        if fim and d > fim:
            continue
        if regiao and regiao.strip().casefold() not in e["regiao"].casefold():
            continue
        if tipo_evento and tipo_evento.strip().upper() != e["tipo_evento"]:
            continue
        resultado.append(e)

    resultado.sort(key=lambda e: e["data"])
    print(f"[eventos] fonte={fonte} | filtros: regiao={regiao} {data_inicio}..{data_fim} "
          f"tipo={tipo_evento} | {len(resultado)} evento(s)", file=sys.stderr)
    return resultado[:50]


if __name__ == "__main__":
    mcp.run(transport="stdio")
