import asyncio
from agents import Agent, Runner, function_tool


@function_tool(needs_approval=True)
async def cancelar_ocorrencia(id_ocorrencia: str) -> str:
    """Cancela uma ocorrência registrada, pelo id."""
    return f"Ocorrência {id_ocorrencia} cancelada."


agente = Agent(
    name="Agente de Registro",
    instructions="Cancele TODAS as ocorrências pedidas pelo usuário, uma chamada de ferramenta por id.",
    tools=[cancelar_ocorrencia],
)


async def main():
    resultado = await Runner.run(agente, "Cancele as ocorrências 4821, 4822 e 4823.")

    ja_decidiu_para_sempre = False   # controla se já demos a decisão "sticky" nesta execução

    while resultado.interruptions:
        estado = resultado.to_state()

        for pendencia in resultado.interruptions:
            print(f"Aprovação pedida: {pendencia.tool_name}({pendencia.arguments})")

            if not ja_decidiu_para_sempre:
                resposta = input(
                    "Aprovar esta E todas as próximas chamadas deste tipo, nesta execução? [s/n]: "
                ).strip().lower()
                if resposta == "s":
                    # always_approve=True grava a decisão no RunState: qualquer chamada FUTURA
                    # à MESMA ferramenta, no resto deste run, passa direto, sem pausar de novo.
                    estado.approve(pendencia, always_approve=True)
                    ja_decidiu_para_sempre = True
                else:
                    estado.reject(pendencia)
            else:
                # Se a decisão "sticky" realmente funcionou, o código nunca deveria
                # entrar aqui de novo — isso serve de prova visual em aula.
                print("  (inesperado: isso não deveria pausar de novo com always_approve=True)")
                estado.approve(pendencia)

        resultado = await Runner.run(agente, estado)

    print(resultado.final_output)


asyncio.run(main())