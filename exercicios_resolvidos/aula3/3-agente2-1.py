import os
import requests

from agents import Agent, Runner, RunHooks, function_tool
from provedor import configurar

configurar()


@function_tool
def get_temperatura(cidade: str) -> float:
    """Retorna a temperatura atual (°C) de uma cidade.

    Args:
        cidade: nome da cidade (ex.: 'Brasília').
    """
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": cidade, "count": 1, "language": "pt", "format": "json"},
    ).json()

    if not geo.get("results"):
        raise ValueError(f"Cidade não encontrada: {cidade}")

    local = geo["results"][0]

    prev = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": local["latitude"],
            "longitude": local["longitude"],
            "current": "temperature_2m",
            "timezone": "auto",
        },
    ).json()

    return prev["current"]["temperature_2m"]


@function_tool
def converter_para_fahrenheit(celsius: float) -> float:
    """Converte uma temperatura de Celsius para Fahrenheit.

    Args:
        celsius: temperatura em graus Celsius.
    """
    return round(celsius * 9 / 5 + 32, 1)


class ContadorDeTurnos(RunHooks):
    """on_llm_start dispara uma vez por CHAMADA ao modelo — isso sim é um turno."""
    turno = 0

    async def on_llm_start(self, ctx, agent, system_prompt, input_items):
        self.turno += 1
        print(f"\n--- turno {self.turno}: chamando o modelo ---")

    async def on_tool_start(self, ctx, agent, tool):
        print(f"  → decidiu chamar: {tool.name}")

    async def on_tool_end(self, ctx, agent, tool, result):
        print(f"  ← {tool.name} devolveu: {result}")


agente = Agent(
    name="Agente de Clima em Fahrenheit",
    instructions=(
        "Você é um agente de clima. Ao receber uma cidade, primeiro consulte a "
        "temperatura atual em Celsius e depois converta o resultado para Fahrenheit "
        "antes de responder."
    ),
    tools=[get_temperatura, converter_para_fahrenheit],
)


def main():
    hooks = ContadorDeTurnos()
    resultado = Runner.run_sync(
        agente,
        "Qual o clima em Brasília em Celsius?",
        hooks=hooks,
    )
    print(f"\nResposta final: {resultado.final_output}")
    print(f"Total de turnos usados: {hooks.turno}")


main()