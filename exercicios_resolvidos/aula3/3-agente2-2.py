import requests
from agents import Agent, Runner, RunHooks, function_tool
from provedor import configurar

configurar()


@function_tool
def get_clima(cidade: str) -> dict:
    """Retorna temperatura (°C) e velocidade do vento (km/h) atuais de uma cidade.

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
            "current": "temperature_2m,wind_speed_10m",
            "timezone": "auto",
        },
    ).json()

    return {
        "temperatura_celsius": prev["current"]["temperature_2m"],
        "vento_kmh": prev["current"]["wind_speed_10m"],
    }


@function_tool
def converter_para_fahrenheit(celsius: float) -> float:
    """Converte temperatura de Celsius para Fahrenheit."""
    return round(celsius * 9 / 5 + 32, 1)


@function_tool
def converter_para_mph(kmh: float) -> float:
    """Converte velocidade do vento de km/h para mph."""
    return round(kmh * 0.621371, 1)


class ContadorDeTurnos(RunHooks):
    turno = 0

    async def on_llm_start(self, ctx, agent, system_prompt, input_items):
        self.turno += 1
        print(f"\n--- turno {self.turno} ---")

    async def on_tool_start(self, ctx, agent, tool):
        print(f"  → chamou: {tool.name}")

    async def on_tool_end(self, ctx, agent, tool, result):
        print(f"  ← {tool.name} devolveu: {result}")


agente = Agent(
    name="Agente de Clima Completo",
    instructions=(
        "Você é um agente de clima. Consulte temperatura e vento com get_clima. "
        "Regra 1 (fixa, sem exceção): a temperatura SEMPRE é convertida e reportada em Fahrenheit. "
        "Regra 2 (flexível): o vento é reportado em km/h por padrão; converta para mph SOMENTE "
        "se o usuário pedir essa unidade explicitamente."
    ),
    tools=[get_clima, converter_para_fahrenheit, converter_para_mph],
)


def rodar(pergunta: str):
    hooks = ContadorDeTurnos()
    resultado = Runner.run_sync(agente, pergunta, hooks=hooks)
    print(f"\nResposta: {resultado.final_output}")
    print(f"Turnos: {hooks.turno}")
    print("=" * 50)


rodar("Qual o clima em Brasília?")
rodar("Qual o clima em Brasília, com o vento em mph?")
rodar("Qual o clima em Brasília, tudo em Celsius e km/h?")