from agents import Agent, Runner, enable_verbose_stdout_logging
from provedor import configurar

enable_verbose_stdout_logging()  

configurar()

agente_matematico = Agent(
    name="agente_matematico",
    instructions="Você é um especialista em matemática. Responda com precisão e clareza.",
)

agente_historiador = Agent(
    name="agente_historiador",
    instructions=" Vocé é um especialista em história. Responda com precisão e clareza.",
)

agente_triador = Agent(
    name="agente_triador",
    instructions=(
        "Você é um agente triador. Direcione cada parte da pergunta para o especialista adequado. "
        "Se a pergunta tiver partes de matemática, use consultar_matematico. "
        "Se tiver partes de história, use consultar_historiador. "
        "Uma mesma pergunta pode exigir os dois — nesse caso, chame ambas as ferramentas "
        "antes de compor a resposta final. Se não se enquadrar em nenhuma categoria, diga que não sabe."
    ),
    tools=[
        agente_matematico.as_tool(
            tool_name="consultar_matematico",
            tool_description="Se a pergunta for sobre matemática, eu devo responder.",
        ),
        agente_historiador.as_tool(
            tool_name="consultar_historiador",
            tool_description="Se a pergunta for sobre história, eu devo responder.",
        )
    ]
)

def executar_agente_handoff2(mensagem: str) -> str:
    resultado = Runner.run_sync(
        agente_triador,
        mensagem
    )
    return resultado.final_output