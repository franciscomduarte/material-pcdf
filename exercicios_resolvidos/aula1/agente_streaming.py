"""
7.1 — Streaming (resposta em tempo real, token a token).

Até agora esperávamos a resposta inteira ficar pronta. Com streaming, recebemos
"pedacinhos" (deltas) conforme o modelo gera — é o efeito "digitando" do ChatGPT.

Peças:
- `Runner.run_streamed(agente, msg)`: NÃO leva await; já devolve um objeto de stream.
- `stream.stream_events()`: gerador ASSÍNCRONO -> precisa de `async for` dentro de
  uma função `async def`, executada com `asyncio.run(...)`.
- Os eventos vêm de vários tipos. Aqui filtramos só os de TEXTO CRU do modelo
  (`raw_response_event` + `ResponseTextDeltaEvent`) e imprimimos `event.data.delta`.
- No fim, `stream.final_output` tem a resposta completa montada.
"""

import asyncio

from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent

from provedor import configurar
configurar()

agente = Agent(
    name="Contador de Histórias",
    instructions="Você conta histórias curtas e criativas, em português com pelo menos 3 paragrafos.",
)


async def main():
    # run_streamed NÃO leva await — ele já retorna o objeto de stream.
    stream = Runner.run_streamed(agente, "Conte uma micro-história sobre um robô.")
    async for event in stream.stream_events():
        # Filtramos só os eventos de texto "cru" vindos do modelo.
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            # end="" e flush=True: imprime na mesma linha, sem bufferizar,
            # para aparecer letra a letra no terminal.
            print(event.data.delta, end="", flush=True)
    print(f"\n\n[Resposta final completa]:\n{stream.final_output}")


asyncio.run(main())