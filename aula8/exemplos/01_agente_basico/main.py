"""Exemplo 01 -- o agente mais simples possível: Agent -> Runner -> LLM -> resposta."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # para importar a pasta base/

from agents import Agent, Runner

from base.provedor import configurar

modelo = configurar()  # lê PROVIDER do .env (openai ou ollama)

assistente = Agent(name="Assistente", instructions="Você é um assistente claro e direto. Responda em português.")

resultado = Runner.run_sync(assistente, "Explique o que é um agente de IA em uma frase.")

print(f"[modelo] {modelo}")
print(f"[resposta] {resultado.final_output}")
