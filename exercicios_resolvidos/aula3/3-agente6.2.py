import asyncio
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner, function_tool


@function_tool
def consultar_clima(cidade: str) -> str:
    """Retorna o clima atual de uma cidade."""
    dados = {"São Paulo": "22°C, nublado", "Brasília": "28°C, sol"}
    return dados.get(cidade, "Cidade não encontrada.")


especialista_clima = Agent(
    name="Especialista_Clima",
    instructions="Responda perguntas sobre clima usando a ferramenta consultar_clima.",
    tools=[consultar_clima],
)

especialista_geral = Agent(
    name="Especialista_Geral",
    instructions="Responda qualquer outra pergunta de forma direta, sem ferramentas.",
)

triador = Agent(
    name="Triador",
    instructions="Encaminhe para o especialista certo. Não responda você mesmo.",
    handoffs=[especialista_clima, especialista_geral],
)


async def rodar_triagem(pergunta: str):
    stream = Runner.run_streamed(triador, pergunta)

    async for event in stream.stream_events():
        # 1) troca de agente ativo (handoff) — dispara assim que o triador transfere
        if event.type == "agent_updated_stream_event":
            print(f"\n[handoff] agora quem responde é: {event.new_agent.name}")

        # 2) eventos de item do loop — chamada de ferramenta e resultado
        elif event.type == "run_item_stream_event":
            if event.name == "tool_called":
                print("  → uma ferramenta foi chamada")
            elif event.name == "tool_output":
                print(f"  ← resultado: {event.item.output}")

        # 3) tokens crus da resposta final, um a um
        elif (event.type == "raw_response_event"
                and isinstance(event.data, ResponseTextDeltaEvent)):
            print(event.data.delta, end="", flush=True)

    # last_agent confirma quem de fato respondeu, depois de qualquer handoff
    print(f"\n\nQuem respondeu de fato: {stream.last_agent.name}")


async def main():
    await rodar_triagem("Como está o tempo hoje em Brasília?")
    print("\n" + "=" * 50)
    await rodar_triagem("Quem foi Pitágoras?")


asyncio.run(main())