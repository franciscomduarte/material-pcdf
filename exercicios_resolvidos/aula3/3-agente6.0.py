import asyncio
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner, function_tool

@function_tool
def get_temperatura_simples(cidade: str) -> str:
    """Retorna o clima atual de uma cidade."""
    dados = {"São Paulo": "22°C, nublado", "Brasília": "28°C, sol"}
    return dados.get(cidade, "Cidade não encontrada.")

agente = Agent(
    name="Assistente de Clima",
    instructions="Use a ferramenta quando perguntarem sobre o tempo.",
    tools=[get_temperatura_simples],
)

async def main():
    stream = Runner.run_streamed(agente, "Como está o tempo em Brasília?")
    turno = 0

    async for event in stream.stream_events():
        if event.type == "run_item_stream_event":       # ← tool_called/tool_output/handoff passam por aqui
            if event.name == "tool_called":
                turno += 1
                print(f"\n--- turno {turno}: ferramenta chamada ---")
            elif event.name == "tool_output":
                print(f"  ← resultado: {event.item.output}")
        elif (event.type == "raw_response_event"
                and isinstance(event.data, ResponseTextDeltaEvent)):
            print(event.data.delta, end="", flush=True)   # ← tokens da resposta final, um a um

    print(f"\n\nTotal de turnos observados via streaming: {turno}")

asyncio.run(main())