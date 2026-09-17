import os

from agents import Agent, Runner
from provedor import configurar

configurar()

agente = Agent(
    name="Primeiro agente",
    instructions="Você é um agente de teste. Responda em poucas palavras e de forma objetiva. " \
    "Se não souber a resposta, diga que não sabe."   
)

def executar_agente(mensagem: str) -> str:
    resultado = Runner.run_sync(
        agente,
        mensagem
    )
    return resultado.final_output