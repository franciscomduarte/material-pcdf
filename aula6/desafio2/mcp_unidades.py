"""
MCP Server do desafio 2 -- consulta de unidades com viatura disponível.

    unidades_proximas(latitude, longitude, raio_km, limite)

Lê unidades.csv, descarta as unidades SEM viatura disponível e devolve as que
estão dentro do raio, da mais próxima para a mais distante (com distancia_km).

Testar isolado:
    npx @modelcontextprotocol/inspector python mcp_unidades.py
"""
import csv
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("unidades-mcp")

CSV = Path(__file__).resolve().parent / "unidades.csv"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * asin(sqrt(a))


@mcp.tool()
def unidades_proximas(latitude: float, longitude: float, raio_km: float = 20, limite: int = 2) -> list[dict]:
    """Unidades COM viatura disponível num raio, da mais próxima para a mais distante.

    Args:
        latitude, longitude: coordenadas da ocorrência.
        raio_km: distância máxima em linha reta (padrão 20 km).
        limite: quantas unidades devolver (padrão 2).
    """
    achadas = []
    with open(CSV, encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            if int(linha["viaturas_disponiveis"]) == 0:
                continue
            distancia = _haversine_km(latitude, longitude, float(linha["latitude"]), float(linha["longitude"]))
            if distancia <= raio_km:
                achadas.append({
                    "codigo": linha["codigo"],
                    "nome": linha["nome"],
                    "distancia_km": round(distancia, 1),
                    "viaturas_disponiveis": int(linha["viaturas_disponiveis"]),
                })
    return sorted(achadas, key=lambda u: u["distancia_km"])[:limite]


if __name__ == "__main__":
    mcp.run(transport="stdio")
