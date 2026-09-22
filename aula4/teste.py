from provedor import configurar
from agents import Agent, Runner

configurar()
agente = Agent(name="Teste", instructions="Responda em uma frase.")
print(Runner.run_sync(agente, "Diga 'ambiente ok'.").final_output)