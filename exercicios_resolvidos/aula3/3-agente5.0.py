import asyncio
from agents import Agent, Runner, function_tool

@function_tool(needs_approval=True)          # ← sempre pausa, não importa o argumento
async def cancelar_ocorrencia(id_ocorrencia: str) -> str:
    """Cancela uma ocorrência registrada, pelo id."""
    return f"Ocorrência {id_ocorrencia} cancelada."

agente = Agent(
    name="Agente de Registro",
    instructions="Cancele a ocorrência pedida pelo usuário, usando a ferramenta.",
    tools=[cancelar_ocorrencia],
)

async def main():
    resultado = await Runner.run(agente, "Cancele a ocorrência 4821.")

    while resultado.interruptions:                   # ← enquanto houver aprovação pendente
        estado = resultado.to_state()                 # ← congela o run pausado num RunState
        for pendencia in resultado.interruptions:
            print(f"Aprovação pedida: {pendencia.tool_name}({pendencia.arguments})")
            resposta = input("Aprovar? [s/n]: ").strip().lower()
            if resposta == "s":
                estado.approve(pendencia)              # ← aprova essa chamada específica
            else:
                estado.reject(pendencia)               # ← rejeita essa chamada específica
        resultado = await Runner.run(agente, estado)   # ← retoma de onde parou, passando o ESTADO, não o texto

    print(resultado.final_output)

asyncio.run(main())