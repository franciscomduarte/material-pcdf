"""
6.1 — Guardrails de entrada (input guardrail).

Conceito: um guardrail é uma "trava de segurança" que roda ANTES (input) ou
DEPOIS (output) do agente principal. Se ele detecta algo proibido, dispara um
"tripwire" (estopim) e a execução para com uma exceção — o agente principal
nem chega a responder.

Aqui a checagem é Python puro (lista de palavras proibidas). No 6.2 veremos um
guardrail que usa outro LLM para julgar; no 6.3, um de SAÍDA com regex.

Peças do SDK:
- @input_guardrail: decora a função que faz a checagem.
- GuardrailFunctionOutput(output_info=..., tripwire_triggered=bool): o retorno.
  `tripwire_triggered=True` => bloqueia.
- InputGuardrailTripwireTriggered: exceção lançada quando o estopim dispara.
"""

import sys

# O console do Windows (cp1252) não imprime emoji e quebra com UnicodeEncodeError.
# Esta linha força a saída em UTF-8. (Inofensiva no Linux/Mac.)
sys.stdout.reconfigure(encoding="utf-8")

from agents import (
    Agent, Runner, RunContextWrapper,
    GuardrailFunctionOutput, InputGuardrailTripwireTriggered,
    input_guardrail, TResponseInputItem,
)

from provedor import configurar
configurar()


@input_guardrail
async def bloquear_off_topic(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Barra perguntas fora do tema de programação."""
    # `input` pode ser uma string (1º turno) ou uma lista de itens (com histórico).
    # Normalizamos para texto antes de checar.
    texto = input if isinstance(input, str) else str(input)
    proibidos = ["receita", "futebol", "fofoca"]
    violou = any(p in texto.lower() for p in proibidos)

    return GuardrailFunctionOutput(
        output_info={"motivo": "fora de escopo" if violou else "ok"},
        tripwire_triggered=violou,  # True = dispara o "estopim" e interrompe tudo
    )


agente = Agent(
    name="Tutor de Programação",
    instructions="Você só ajuda com dúvidas de programação.",
    input_guardrails=[bloquear_off_topic],  # pode haver vários; todos rodam
)


def main():
    for pergunta in ["Como faço um loop em Python?", "Me dá uma receita de bolo?"]:
        try:
            r = Runner.run_sync(agente, pergunta)
            print("OK:", r.final_output)
        except InputGuardrailTripwireTriggered:
            # A 2ª pergunta cai aqui: contém "receita" -> tripwire disparado.
            print("BLOQUEADO: pergunta fora do escopo.")


# O guardrail é `async`, mas `run_sync` cuida do loop de eventos por baixo —
# não precisamos de asyncio.run() aqui.
main()