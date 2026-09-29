"""
Exemplo 14 -- MCP Server via HTTP (Streamable HTTP).

Até aqui todo MCP Server da aula rodava por stdio: o cliente SOBE o server
como subprocesso e conversa por stdin/stdout, então os dois precisam estar
na MESMA máquina. Aqui o server é um serviço de rede: fica de pé sozinho,
escutando uma porta, e qualquer cliente que alcance a URL conversa com ele.

O que muda em relação ao Exemplo 03 é UMA linha, a última. As tools, o schema
e a lógica são o mesmo tipo de código.

Este server não usa banco: os dados ficam no próprio arquivo, para que ele
rode em qualquer máquina só com `pip install mcp`.

Tools:
    listar_unidades(regiao)
    unidade_mais_proxima(latitude, longitude)

Rodar (deixe este terminal aberto; o server fica esperando conexões):
    python server.py

Variáveis de ambiente (todas opcionais):
    MCP_HOST   interface onde escutar. Padrão 127.0.0.1 (só esta máquina).
               Use 0.0.0.0 para aceitar conexões de OUTRAS máquinas.
    MCP_PORT   porta. Padrão 8000.

Endereço do server: http://127.0.0.1:8000/mcp
"""
import os
from math import asin, cos, radians, sin, sqrt

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("unidades-mcp")

# Subconjunto das unidades de dados/referencia.py (fictícias).
UNIDADES = [
    {"codigo": "DP-ALFA-01", "nome": "1ª Delegacia de Polícia - Alfa", "regiao": "ALFA", "latitude": -23.5100, "longitude": -46.5000},
    {"codigo": "BPM-ALFA-01", "nome": "1º Batalhão de Polícia Militar - Alfa", "regiao": "ALFA", "latitude": -23.5150, "longitude": -46.5050},
    {"codigo": "DP-BRAVO-01", "nome": "2ª Delegacia de Polícia - Bravo", "regiao": "BRAVO", "latitude": -23.4700, "longitude": -46.5200},
    {"codigo": "BPM-BRAVO-01", "nome": "2º Batalhão de Polícia Militar - Bravo", "regiao": "BRAVO", "latitude": -23.4650, "longitude": -46.5250},
    {"codigo": "DP-CHARLIE-01", "nome": "3ª Delegacia de Polícia - Charlie", "regiao": "CHARLIE", "latitude": -23.4500, "longitude": -46.4900},
    {"codigo": "DP-DELTA-01", "nome": "4ª Delegacia de Polícia - Delta", "regiao": "DELTA", "latitude": -23.5800, "longitude": -46.4800},
    {"codigo": "DP-FOXTROT-01", "nome": "6ª Delegacia de Polícia - Foxtrot", "regiao": "FOXTROT", "latitude": -23.5200, "longitude": -46.4300},
    {"codigo": "DP-HOTEL-01", "nome": "8ª Delegacia de Polícia - Hotel", "regiao": "HOTEL", "latitude": -23.6100, "longitude": -46.5500},
]

RAIO_TERRA_KM = 6371.0


def _distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return RAIO_TERRA_KM * 2 * asin(sqrt(a))


@mcp.tool()
def listar_unidades(regiao: str | None = None) -> list[dict]:
    """Lista as unidades policiais da CISP, com código, nome, região e coordenadas.

    Args:
        regiao: código da região para filtrar (ALFA, BRAVO, CHARLIE, DELTA,
            FOXTROT ou HOTEL). Sem valor, retorna todas as unidades.
    """
    if regiao is None:
        return UNIDADES
    return [u for u in UNIDADES if u["regiao"] == regiao.upper()]


@mcp.tool()
def unidade_mais_proxima(latitude: float, longitude: float) -> dict:
    """Encontra a unidade policial mais próxima de um ponto (em linha reta).

    Args:
        latitude: latitude do ponto de referência (ex.: local de uma ocorrência).
        longitude: longitude do ponto de referência.
    """
    unidade = min(UNIDADES, key=lambda u: _distancia_km(latitude, longitude, u["latitude"], u["longitude"]))
    distancia = _distancia_km(latitude, longitude, unidade["latitude"], unidade["longitude"])
    return {**unidade, "distancia_km": round(distancia, 2)}


if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    print(f"MCP Server escutando em http://{host}:{port}/mcp  (Ctrl+C para parar)")
    # No stdio seria: mcp.run(transport="stdio")
    mcp.run(transport="streamable-http", host=host, port=port)
