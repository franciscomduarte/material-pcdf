"""
3.2 — Agents-as-tools (agentes como ferramentas).

Mesma dupla de especialistas do 3.1 (Matemática e História), mas com uma
diferença de CONTROLE fundamental:

- No handoff (3.1), o triador TRANSFERE a conversa e sai de cena. Quem responde
  é o especialista, e `last_agent` é o especialista.
- Aqui, o orquestrador NÃO transfere. Ele CHAMA os especialistas como se fossem
  ferramentas (function calling comum), recebe o texto de volta e continua no
  comando. Quem escreve a resposta final é o próprio orquestrador —
  `last_agent` é o orquestrador, nunca o especialista.

Consequência prática: como o orquestrador pode chamar MAIS DE UMA ferramenta
antes de responder, uma pergunta ambígua (ex.: "Pitágoras") pode acionar os
dois especialistas e ser sintetizada numa única resposta. É exatamente o
"Caso 2" que discutimos.
"""

from agents import Agent, Runner

from provedor import configurar
configurar()

# Os especialistas são agentes NORMAIS — idênticos aos do 3.1.
# Não precisam de `handoffs` nem de `handoff_description`: aqui eles não recebem
# a conversa, apenas são invocados e devolvem um texto.
agente_matematica = Agent(
    name="Especialista_Matematica",
    instructions="Você resolve problemas de matemática, mostrando o passo a passo.",
)

agente_historia = Agent(
    name="Especialista_Historia",
    instructions="Você responde perguntas de história de forma clara e contextualizada.",
)

# Orquestrador: diferente do triador, ele CONTINUA responsável pela resposta.
# Repare em dois pontos:
#   1) usa `tools=[...]` (não `handoffs=[...]`);
#   2) cada especialista vira ferramenta via `.as_tool(...)`.
#
# `tool_name` segue a mesma regra de nome de função (letras, dígitos e "_"):
# é ele que o orquestrador "vê" para decidir quando chamar. `tool_description`
# é a dica que orienta essa decisão — o equivalente ao `handoff_description`
# do 3.1, mas agora para uma ferramenta.
orquestrador = Agent(
    name="Orquestrador",
    instructions=(
        "Você é um tutor que responde ao usuário. Use as ferramentas de "
        "especialista para obter o conteúdo de cada área e então escreva UMA "
        "resposta final, integrando o que os especialistas devolverem. "
        "Se a pergunta tiver os dois lados (ex.: um personagem histórico que "
        "também é matemático), consulte os DOIS especialistas e junte as partes."
    ),
    tools=[
        agente_matematica.as_tool(
            tool_name="consultar_matematica",
            tool_description="Resolve cálculos, equações, geometria e problemas numéricos, com passo a passo.",
        ),
        agente_historia.as_tool(
            tool_name="consultar_historia",
            tool_description="Explica personagens, datas, eventos e contexto histórico.",
        ),
    ],
)


def executar_agente_handoff_as_tools(mensagem: str):
    return Runner.run_sync( orquestrador, mensagem )


if __name__ == "__main__":
    # "Quem foi Pitágoras?" é ambíguo: figura histórica E dá nome ao teorema.
    # No handoff, o triador era obrigado a escolher UM. Aqui, o orquestrador
    # pode chamar os dois especialistas e sintetizar.
    resultado = executar_agente_handoff_as_tools("Quem foi Pitágoras?")
    print(resultado.final_output)

    # Contraste com o 3.1: aqui `last_agent` é o PRÓPRIO orquestrador,
    # porque ele nunca abriu mão do controle.
    print("Respondido por:", resultado.last_agent.name)