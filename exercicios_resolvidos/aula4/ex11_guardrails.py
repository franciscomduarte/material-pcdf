"""
Ex 11 (TODO) — Guardrails (entrada e saída).
Cenário novo: um Perito classifica um vestígio em JSON. Bloqueamos RG real na
entrada (LGPD) e exigimos JSON válido na saída.
Rode: python todo/ex11_guardrails.py
"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pydantic import BaseModel
from agents import (
    Agent, GuardrailFunctionOutput, InputGuardrailTripwireTriggered, Runner,
    RunContextWrapper, input_guardrail, output_guardrail,
)
from provedor import configurar

configurar()

_RE_RG = re.compile(r"\d{1,2}\.?\d{3}\.?\d{3}-?[0-9Xx]")


@input_guardrail
def barrar_dado_pessoal_real(ctx: RunContextWrapper, agent: Agent, entrada) -> GuardrailFunctionOutput:
    texto = entrada if isinstance(entrada, str) else str(entrada)
    # TODO 1: procure _RE_RG em `texto` e devolva um GuardrailFunctionOutput
    #         com tripwire_triggered=True se achou (use output_info à vontade).
    ...


class Vestigio(BaseModel):
    tipo: str
    prioridade: str
    contaminado: bool


def _sem_cercas_markdown(texto: str) -> str:
    """O modelo às vezes responde com ```json ... ``` mesmo mandando 'só o JSON'."""
    texto = texto.strip()
    if texto.startswith("```"):
        texto = texto.strip("`")
        texto = texto.removeprefix("json").strip()
    return texto


@output_guardrail
def exigir_json_valido(ctx: RunContextWrapper, agent: Agent, saida) -> GuardrailFunctionOutput:
    # TODO 2: tente fazer json.loads(_sem_cercas_markdown(saida)) (se for string)
    #         e validar com Vestigio.model_validate(...); em caso de erro,
    #         tripwire_triggered=True.
    ...


perito = Agent(
    name="Perito",
    instructions=(
        'Classifique o vestígio. Responda em JSON com as chaves '
        '"tipo", "prioridade" e "contaminado" (true/false). Só o JSON.'
    ),
    # TODO 3: ligue os dois guardrails no agente (input_guardrails / output_guardrails)
    input_guardrails=[],
    output_guardrails=[],
)

if __name__ == "__main__":
    print(Runner.run_sync(perito, "Vestígio de sangue na cena, coletado sem luvas.").final_output)

    try:
        Runner.run_sync(perito, "Perito RG 12.345.678-9 coletou o vestígio.")
    except InputGuardrailTripwireTriggered:
        print("\n[guardrail] entrada recusada: dado pessoal real detectado.")
