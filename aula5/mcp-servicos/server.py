"""
MCP Server -- SERVIÇOS (CISP)

Este servidor NÃO tem banco de dados atrás dele. É só cálculo puro em
Python. É o exemplo que prova, na prática: MCP não é "MCP + banco" --
é uma camada de CAPACIDADES. Aqui a capacidade é geoespacial/analítica.

Tools:
    calcular_distancia(lat1, lon1, lat2, lon2)
    encontrar_unidades_proximas(latitude, longitude, unidades, limite)
    calcular_indice_operacional(total_ocorrencias, viaturas_disponiveis,
                                 total_viaturas, equipes_em_servico, total_equipes)

Rodar isolado com o MCP Inspector:
    npx @modelcontextprotocol/inspector python server.py
"""
import os
from math import asin, cos, radians, sin, sqrt

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("servicos-mcp")

RAIO_TERRA_KM = 6371.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return RAIO_TERRA_KM * 2 * asin(sqrt(a))


@mcp.tool()
def calcular_distancia(lat1: float, lon1: float, lat2: float, lon2: float) -> dict:
    """Calcula a distância aproximada (em linha reta) entre duas coordenadas geográficas.

    Usa a fórmula de haversine -- não considera ruas ou trânsito, é uma
    aproximação para fins de priorização, não de roteirização.

    Args:
        lat1, lon1: latitude/longitude do ponto de origem.
        lat2, lon2: latitude/longitude do ponto de destino.
    """
    distancia = _haversine_km(lat1, lon1, lat2, lon2)
    return {"distancia_km": round(distancia, 2)}


@mcp.tool()
def encontrar_unidades_proximas(
    latitude: float,
    longitude: float,
    unidades: list[dict],
    limite: int = 3,
) -> list[dict]:
    """Ordena uma lista de unidades pela distância até um ponto, da mais próxima
    para a mais distante.

    Esta ferramenta NÃO consulta nenhum banco -- ela recebe a lista de
    unidades como parâmetro (normalmente o resultado de uma chamada anterior
    ao MCP Operações, ex.: consultar_unidades) e só faz o cálculo geográfico.
    É o agente quem monta essa lista antes de chamar esta ferramenta.

    Args:
        latitude, longitude: coordenadas do ponto de referência (ex.: local da ocorrência).
        unidades: lista de dicts, cada um com pelo menos 'latitude' e 'longitude'
            (outros campos como 'codigo'/'nome' são preservados no retorno).
        limite: quantas unidades retornar (padrão 3, mais próximas primeiro).
    """
    resultado = []
    for unidade in unidades:
        dist = _haversine_km(latitude, longitude, float(unidade["latitude"]), float(unidade["longitude"]))
        resultado.append({**unidade, "distancia_km": round(dist, 2)})
    resultado.sort(key=lambda u: u["distancia_km"])
    return resultado[:limite]


@mcp.tool()
def calcular_indice_operacional(
    total_ocorrencias: int,
    viaturas_disponiveis: int,
    total_viaturas: int,
    equipes_em_servico: int,
    total_equipes: int,
) -> dict:
    """Calcula um índice operacional (0 a 100) que resume a pressão sobre uma região:
    mais ocorrências e menos recursos disponíveis => índice mais baixo (mais crítico).

    Fórmula didática (não é uma métrica oficial real):
        disponibilidade = média(% viaturas disponíveis, % equipes em serviço)
        pressao = ocorrências por viatura disponível (normalizada)
        índice = disponibilidade ajustada pela pressão, entre 0 e 100

    Args:
        total_ocorrencias: nº de ocorrências no período analisado, na região.
        viaturas_disponiveis: nº de viaturas com status DISPONIVEL na região.
        total_viaturas: nº total de viaturas na região.
        equipes_em_servico: nº de equipes com status EM_SERVICO na região.
        total_equipes: nº total de equipes na região.
    """
    pct_viaturas = (viaturas_disponiveis / total_viaturas * 100) if total_viaturas else 0.0
    pct_equipes = (equipes_em_servico / total_equipes * 100) if total_equipes else 0.0
    disponibilidade = (pct_viaturas + pct_equipes) / 2

    ocorrencias_por_viatura = (total_ocorrencias / viaturas_disponiveis) if viaturas_disponiveis else total_ocorrencias
    fator_pressao = max(0.3, 1 - min(ocorrencias_por_viatura / 50, 0.7))

    indice = round(disponibilidade * fator_pressao, 1)
    if indice >= 70:
        classificacao = "CONFORTAVEL"
    elif indice >= 40:
        classificacao = "ATENCAO"
    else:
        classificacao = "CRITICO"

    return {
        "indice_operacional": indice,
        "classificacao": classificacao,
        "percentual_viaturas_disponiveis": round(pct_viaturas, 1),
        "percentual_equipes_em_servico": round(pct_equipes, 1),
    }


if __name__ == "__main__":
    transporte = os.getenv("MCP_TRANSPORT", "stdio")
    if transporte == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "8003")),
        )
    else:
        mcp.run(transport="stdio")
