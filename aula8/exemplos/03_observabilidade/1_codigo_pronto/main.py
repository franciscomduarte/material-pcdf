"""Exemplo 03 (ponto de partida) -- agente com tool que responde várias perguntas.
Funciona, mas é uma caixa-preta: não sabemos quanto cada pergunta demorou, quantos tokens gastou,
nem se a tool foi chamada. Durante a aula vamos DAR VISIBILIDADE a isso."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agents import Agent, Runner, function_tool

from base.provedor import configurar

TEMPERATURAS = {"brasília": 25, "são paulo": 22, "rio de janeiro": 28}  # dados fictícios


@function_tool
def consultar_temperatura(cidade: str) -> str:
    """Devolve a temperatura atual, em graus Celsius, de uma cidade."""
    graus = TEMPERATURAS.get(cidade.lower())
    return f"{graus}°C" if graus is not None else "ERRO: cidade desconhecida"


modelo = configurar()

agente = Agent(
    name="Meteorologista",
    instructions="Responda em português, em uma frase. Para temperatura de cidade, use a ferramenta.",
    tools=[consultar_temperatura],
)

PERGUNTAS = [
    "Quanto está fazendo em Brasília agora?",
    "E em São Paulo?",
    "Qual a temperatura em Gotham City?",  # a tool vai devolver ERRO
    "Quanto é 2 + 2?",                      # não precisa de tool
]

for pergunta in PERGUNTAS:
    resultado = Runner.run_sync(agente, pergunta)
    print(f"[usuário] {pergunta}\n[resposta] {resultado.final_output}\n")
