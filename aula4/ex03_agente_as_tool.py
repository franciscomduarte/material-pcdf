"""
Exercício 3 — Agente como ferramenta (agents-as-tools)
Outra forma de A2A síncrona: em vez de DELEGAR (handoff), o coordenador
CHAMA outros agentes como se fossem ferramentas e junta as respostas.

Diferença didática:
  - handoff: passa o bastão (quem responde é o outro agente).
  - as_tool: o coordenador continua no comando e usa os outros como consultores.

Rode: python ex03_agente_como_tool.py
"""
from agents import Agent, Runner
from provedor import configurar

configurar()

juridico = Agent(
    name="Juridico",
    instructions="Dê o enquadramento legal provável da ocorrência, em 1-2 linhas.",
)

investigador = Agent(
    name="Investigador",
    instructions="Liste 2 diligências investigativas iniciais para a ocorrência.",
)

coordenador = Agent(
    name="Coordenador",
    instructions=(
        "Você coordena o atendimento de uma ocorrência. "
        "Consulte o Jurídico e o Investigador e produza um resumo único "
        "com: enquadramento e próximos passos."
    ),
    tools=[
        juridico.as_tool(
            tool_name="consultar_juridico",
            tool_description="Obtém o enquadramento legal provável da ocorrência.",
        ),
        investigador.as_tool(
            tool_name="consultar_investigador",
            tool_description="Obtém diligências investigativas iniciais.",
        ),
    ],
)

if __name__ == "__main__":
    ocorrencia = "Arrombamento de residência no Lago Sul com subtração de eletrônicos."
    print(Runner.run_sync(coordenador, ocorrencia).final_output)