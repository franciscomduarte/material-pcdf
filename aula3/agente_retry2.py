import time
import requests
from agents import Agent, Runner, function_tool
from provedor import configurar

configurar()

@function_tool
def get_temperatura_resiliente(cidade: str, max_tentativas: int = 4) -> float:
    """Retorna a temperatura atual (°C) de uma cidade, com retry e backoff exponencial."""
    espera_base = 0.5  # segundos

    for tentativa in range(1, max_tentativas + 1):
        try:
            geo = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": cidade, "count": 1, "language": "pt", "format": "json"},
                timeout=3,
            )
            geo.raise_for_status()
            dados_geo = geo.json()
            if not dados_geo.get("results"):
                raise ValueError(f"Cidade não encontrada: {cidade}")   # ← erro de NEGÓCIO: por que não deveria tentar de novo?
            local = dados_geo["results"][0]

            prev = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": local["latitude"], "longitude": local["longitude"],
                        "current": "temperature_2m", "timezone": "auto"},
                timeout=3,
            )
            prev.raise_for_status()
            return prev.json()["current"]["temperature_2m"]

        except ValueError:
            raise   # erro de negócio: propaga direto, sem tentar de novo

        except requests.exceptions.RequestException as erro:              # ← qual classe cobre timeout, conexão recusada, erro HTTP 5xx?
            if tentativa == max_tentativas:
                raise RuntimeError(f"Falhou após {max_tentativas} tentativas: {erro}")
            espera = espera_base * (2 ** (tentativa - 1))                 # ← qual expoente dá 0.5s, 1s, 2s, 4s nas tentativas 1,2,3,4?
            print(f"  tentativa {tentativa} falhou ({erro}); tentando de novo em {espera}s...")
            time.sleep(espera)

agente = Agent(
    name="Agente de Clima Resiliente",
    instructions="Use a ferramenta quando perguntarem sobre o tempo.",
    tools=[get_temperatura_resiliente],
)
r = Runner.run_sync(agente, "Qual a temperatura em Brasília?")
print("\nResposta final:", r.final_output)