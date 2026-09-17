import asyncio
from agents import Agent, Runner, MaxTurnsExceeded, function_tool
from provedor import configurar

configurar()


@function_tool
async def consulta_lenta(cidade: str) -> str:
    """Simula uma consulta que demora (ex.: sistema externo fora do ar/lento)."""
    await asyncio.sleep(5)
    return "22°C, nublado"


agente = Agent(
    name="Agente Lento",
    instructions="Use a ferramenta quando perguntarem sobre o tempo.",
    tools=[consulta_lenta],
)


async def rodar_com_timeout(pergunta: str, segundos: float, max_turns: int = 10):
    try:
        resultado = await asyncio.wait_for(
            Runner.run(agente, pergunta, max_turns=max_turns),
            timeout=segundos,
        )
        print("Resposta:", resultado.final_output)
        return resultado
    except asyncio.TimeoutError:
        print(f"Estourou o prazo de {segundos}s — o sistema externo demorou demais.")
    except MaxTurnsExceeded:
        print(f"Estourou {max_turns} turnos — aqui o problema é o LOOP, não o tempo.")


asyncio.run(rodar_com_timeout("Como está o tempo em Brasília?", segundos=2))
# Rode de novo com segundos=10 pra ver o mesmo agente terminar normalmente.