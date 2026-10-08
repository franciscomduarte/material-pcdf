"""Exemplo 05 (ponto de partida) -- um agente que DEVERIA responder só com JSON, para outro sistema consumir.
Funciona, mas ninguém confere se a resposta realmente está no formato prometido."""
import json
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
    return f"{graus}" if graus is not None else "cidade desconhecida"


agente = Agent(
    name="Meteorologista JSON",
    instructions=(
        'Responda SOMENTE com um JSON no formato {"cidade": "<nome>", "temperatura": <número>}. '
        "Use a ferramenta para obter a temperatura. Não escreva mais nada."
    ),
    tools=[consultar_temperatura],
)

PERGUNTAS = ["Temperatura em Brasília?", "E em São Paulo?", "Temperatura em Gotham City?", "Quanto é 2 + 2?"]

modelo = configurar()
print(f"[modelo] {modelo}\n")
for pergunta in PERGUNTAS:
    resposta = Runner.run_sync(agente, pergunta).final_output
    try:  # o sistema que recebe a resposta faz exatamente isto
        dados = json.loads(resposta)
        print(f"[usuário] {pergunta}\n[resposta] {resposta}\n[outro sistema] leu o JSON: {dados}\n")
    except json.JSONDecodeError:
        print(f"[usuário] {pergunta}\n[resposta] {resposta!r}\n[outro sistema] QUEBROU: não é JSON válido\n")
