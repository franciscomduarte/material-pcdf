import os
import requests

from agents import Agent, Runner, function_tool
from provedor import configurar

configurar()

@function_tool
def get_temperatura(cidade: str) -> float:
    """Retorna a temperatura atual (°C) de uma cidade.

    Args:
        cidade: nome da cidade (ex.: 'Brasília').
    """
    # 1) cidade -> coordenadas (endpoint de geocoding)
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": cidade, "count": 1, "language": "pt", "format": "json"},
    ).json()

    # A API responde 200 mesmo sem achar a cidade; o "não achou" vem como
    # ausência da chave "results". Por isso checamos aqui.
    if not geo.get("results"):
        raise ValueError(f"Cidade não encontrada: {cidade}")

    local = geo["results"][0]  # pega o primeiro resultado (count=1)

    # 2) coordenadas -> temperatura atual (endpoint de forecast)
    prev = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": local["latitude"],
            "longitude": local["longitude"],
            "current": "temperature_2m",  # variável "temperatura a 2m do solo"
            "timezone": "auto",
        },
    ).json()

    return prev["current"]["temperature_2m"]


agente = Agent(
    name="Segundo agente",
    instructions="Você é um agente de clima. Ao receber uma cidade, " \
                 "responda com o clima dessa cidade.",
    tools=[get_temperatura],
)

def main():
    resultado = Runner.run_sync(
        agente,
        "Qual o clima em Brasília hoje?"
    )
    print(resultado.final_output)

main()