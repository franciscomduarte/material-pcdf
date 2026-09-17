from agents import Agent, Runner
from provedor import configurar

configurar()

agente_matematico = Agent(
    name="agente_matematico",
    instructions="Você é um especialista em matemática. Responda com precisão e clareza.",
    handoff_description=("Se a pergunta for sobre matemática, eu devo responder."),
)

agente_historiador = Agent(
    name="agente_historiador",
    instructions=" Vocé é um especialista em história. Responda com precisão e clareza.",
    handoff_description=("Se a pergunta for sobre história, eu devo responder."),
)

agente_triador = Agent(
    name="agente_triador",
    instructions=" Você é um agente triador. Sua função é direcionar perguntas para o agente mais adequado com base no conteúdo da pergunta. " \
    "Se a pergunta for sobre matemática, encaminhe para o agente_matematico. Se for sobre história, encaminhe para o agente_historiador. " \
    "Se não se enquadrar em nenhuma dessas categorias, responda que não sabe.",
    handoffs=[agente_matematico, agente_historiador],
)

def executar_agente_handoff(mensagem: str) -> str:
    resultado = Runner.run_sync(
        agente_triador,
        mensagem
    )
    return resultado.final_output