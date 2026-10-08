"""Exemplo 02 -- agente com uma tool. O AGENTE decide quando chamar; nós só mostramos o caminho."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, Runner, function_tool

from base.provedor import configurar

TEMPERATURAS = {"brasília": 25, "são paulo": 22, "rio de janeiro": 28}  # dados fictícios


@function_tool
def consultar_temperatura(cidade: str) -> str:
    """Devolve a temperatura atual, em graus Celsius, de uma cidade."""
    graus = TEMPERATURAS.get(cidade.lower())
    return f"{graus}°C" if graus is not None else "cidade desconhecida"


modelo = configurar()

agente = Agent(
    name="Meteorologista",
    instructions="Responda em português, em uma frase. Para temperatura de cidade, use a ferramenta.",
    tools=[consultar_temperatura],
)

for pergunta in ["Quanto está fazendo em Brasília agora?", "Quanto é 2 + 2?"]:
    resultado = Runner.run_sync(agente, pergunta)
    print(f"\n[usuário] {pergunta}")
    for item in resultado.new_items:  # o caminho percorrido: chamada da tool -> resultado -> resposta
        if item.type == "tool_call_item":
            print(f"  -> agente chamou: {item.raw_item.name}({item.raw_item.arguments})")
        elif item.type == "tool_call_output_item":
            print(f"  -> tool devolveu: {item.output}")
    print(f"[resposta] {resultado.final_output}")
