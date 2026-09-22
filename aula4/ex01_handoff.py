"""
Exercício 1 — Handoff básico (síncrono, in-process)
A2A no jeito mais simples: um agente delega a outro via `handoffs`.

Fluxo: Triagem classifica a ocorrência e, se houver crime, encaminha ao Jurídico.
Rode: python ex01_handoff.py
"""
from agents import Agent, Runner
from provedor import configurar

configurar()  # aplica OpenAI ou Ollama conforme o .env

juridico = Agent(
    name="Juridico",
    instructions="Avalie o enquadramento legal da ocorrência e cite o artigo provável.",
)

triagem = Agent(
    name="Triagem",
    instructions=(
        "Classifique a ocorrência (tipo e gravidade). "
        "Se houver indício de crime, encaminhe ao agente Jurídico."
    ),
    handoffs=[juridico],  # pode delegar ao Jurídico
)

if __name__ == "__main__":
    ocorrencia = "Objeto perdido (guarda-chuva) devolvido ao balcão."
    resultado = Runner.run_sync(triagem, ocorrencia)
    print(resultado.final_output)