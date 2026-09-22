"""
3.1 — Handoff (transferência entre agentes).

Conceito: em vez de UM agente gigante que sabe tudo, montamos vários agentes
especialistas e um agente "triador" que só decide para quem passar a conversa.

Como funciona:
- O triador tem `handoffs=[...]` em vez de `tools=[...]`.
- Cada item de `handoffs` vira, internamente, uma "ferramenta de transferência".
- Quando o triador decide transferir, o Runner troca o agente ativo e o
  especialista escolhido é quem produz a resposta final.
- A decisão é feita SÓ pela linguagem natural (nome + instruções dos agentes).
  Não há if/else de roteamento escrito por nós.

`resultado.last_agent` diz qual agente efetivamente respondeu no fim.
"""


from agents import Agent, Runner

from provedor import configurar
configurar()

# Nota sobre o NOME dos agentes (explicar para a turma):
# Cada agente em `handoffs` vira, internamente, uma ferramenta de function calling
# chamada "transfer_to_<name>". Nomes de função na API só aceitam letras, dígitos
# e "_". Se o `name` tiver espaço ou acento (ex.: "Especialista em Matemática"),
# o SDK emite um WARNING e converte para algo imprevisível, tipo
# "transfer_to_especialista_em_matem_tica". Continua funcionando, mas para evitar
# o aviso e nomes estranhos, usamos aqui nomes já normalizados: sem espaço, sem acento.
agente_matematica = Agent(
    name="Especialista_Matematica",
    instructions="Você resolve problemas de matemática, mostrando o passo a passo.",
    handoff_description=(
        "Se a pergunta for de matemática, transfira para mim. "
        "Se a pergunta for de história, transfira para o especialista de história."
    ),
)

agente_historia = Agent(
    name="Especialista_Historia",
    instructions="Você responde perguntas de história de forma clara e contextualizada.",
        handoff_description=(
        "Se a pergunta for de matemática, transfira para o especialista de matemática. "
        "Se a pergunta for de historia, transfira para mim."
    ),
)

# Agente triador: não responde direto, ele encaminha.
triador = Agent(
    name="Triador",
    instructions=(
        "Você analisa a pergunta do usuário e a encaminha para o especialista certo. "
        "Não responda você mesmo — apenas escolha para quem passar."
    ),
    handoffs=[agente_matematica, agente_historia],
)

def executar_agente_handoff(mensagem: str):
    return Runner.run_sync( triador, mensagem )

if __name__ == "__main__":
    resultado = executar_agente_handoff( "Quem foi Pitágoras?" )
    print(resultado.final_output)