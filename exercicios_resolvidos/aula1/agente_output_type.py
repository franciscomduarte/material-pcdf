"""
4.1 — Saída estruturada (output_type).

Problema que isso resolve: até agora `final_output` era texto livre. Difícil de
usar em programa (parsear data, contar pessoas...). Com `output_type` você
declara um MODELO Pydantic e o SDK obriga o modelo a devolver exatamente
aquele formato, já convertido em objeto Python.

O que observar:
- `Evento` é uma classe Pydantic: cada campo tem um tipo.
- `participantes: int` -> o SDK garante que volta um inteiro de verdade,
  não a string "12".
- `resultado.final_output` deixa de ser str e passa a ser um objeto `Evento`,
  com autocompletar e validação.
"""


from agents import Agent, Runner
from pydantic import BaseModel

from provedor import configurar
configurar()


# Define o formato EXATO da resposta. É o "contrato" de saída do agente.
class Evento(BaseModel):
    nome: str
    data: str
    local: str
    participantes: int


agente = Agent(
    name="Extrator de Eventos",
    instructions="Extraia as informações do evento a partir do texto do usuário.",
    output_type=Evento,  # força a saída nesse formato (schema enviado ao modelo)
)

def executar_agente_output_type(mensagem: str):
    return Runner.run_sync( agente, mensagem )

def main_evento_extraction():
    texto = "A reunião de planejamento será dia 15/10 na Enap, em Brasília, com 12 pessoas."
    resultado = Runner.run_sync(agente, texto)
    evento = resultado.final_output  # já é um objeto Evento (não precisa de json.loads)
    print(evento.nome)
    print(evento.data)
    # Prova de que a tipagem foi respeitada: type() é <class 'int'>.
    print(evento.participantes, "-", type(evento.participantes))


if __name__ == "__main__":
    main_evento_extraction()