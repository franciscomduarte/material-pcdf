"""
Ex 3 (TODO) — Agente como ferramenta (as_tool).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents import Agent, Runner
from provedor import configurar

configurar()

juridico = Agent(name="Jurídico", instructions="Enquadramento legal provável, 1-2 linhas.")
investigador = Agent(name="Investigador", instructions="2 diligências investigativas iniciais.")

# TODO: crie o Coordenador que USA juridico e investigador como ferramentas.
#       Dica: tools=[juridico.as_tool(tool_name=..., tool_description=...), ...]
coordenador = ...

if __name__ == "__main__":
    ocorrencia = (
        "Sequestro relâmpago com uso de arma branca; vítima liberada após "
        "saque em caixa eletrônico, região do Gama."
    )
    print(Runner.run_sync(coordenador, ocorrencia).final_output)