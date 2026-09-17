import os

from agents import Agent, Runner
from provedor import configurar

configurar()

agente = Agent(
    name="Primeiro agente",
    instructions="Você é um agente de teste. Responda em poucas palavras e de forma objetiva. " \
    "Se não souber a resposta, diga que não sabe."   
)

def main():
    resultado = Runner.run_sync(
        agente,
        "Quem é o presidente da Argentina atualmente?"
    )
    # .final_output aqui é uma string (não definimos output_type — isso vem no 4.x).
    print(resultado.final_output)

main()