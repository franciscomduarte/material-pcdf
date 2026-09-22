import asyncio
from agents import Agent, Runner, function_tool


@function_tool(needs_approval=True)
async def cancelar_ocorrencia(id_ocorrencia: str) -> str:
    """Cancela uma ocorrência registrada, pelo id."""
    return f"Ocorrência {id_ocorrencia} cancelada."


agente = Agent(
    name="Agente de Registro",
    instructions="Cancele a ocorrência pedida pelo usuário, usando a ferramenta.",
    tools=[cancelar_ocorrencia],
)


async def rodar_streamado(pedido: str):
    # 1ª chamada: streamada desde o início
    stream = Runner.run_streamed(agente, pedido)

    async for event in stream.stream_events():
        # nesta versão só drenamos os eventos (é obrigatório esgotar o iterador
        # antes de checar .interruptions); em produção você imprimiria tokens aqui
        pass

    resultado = stream  # RunResultStreaming também expõe .interruptions, igual RunResult

    while resultado.interruptions:
        estado = resultado.to_state()

        for pendencia in resultado.interruptions:
            print(f"Aprovação pedida: {pendencia.tool_name}({pendencia.arguments})")
            resposta = input("Aprovar? [s/n]: ").strip().lower()
            if resposta == "s":
                estado.approve(pendencia)
            else:
                estado.reject(pendencia)

        # retoma com run_streamed, NÃO com run — senão a resposta final
        # deixa de ser streamada depois da aprovação
        stream = Runner.run_streamed(agente, estado)
        async for event in stream.stream_events():
            pass
        resultado = stream

    print(resultado.final_output)


asyncio.run(rodar_streamado("Cancele a ocorrência 9911."))