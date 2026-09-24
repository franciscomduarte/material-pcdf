"""
Exemplo 01 (agente) -- o agente usa consultar_ocorrencias() como function_tool,
exatamente como na Aula 4 (ex10_function_tool.py).

Rode:
    python agente_com_tool_local.py

O que este exemplo estabelece (ponto de partida da aula):
  - a tool É uma função Python, no mesmo processo do agente;
  - o "schema" que o LLM enxerga vem da assinatura Python (docstring/tipos);
  - QUALQUER outro agente que precisar dessa mesma capacidade vai ter que
    IMPORTAR este módulo Python -- ou duplicar a função.

Pergunta para a turma, antes de seguir para o Exemplo 02:
  "Se tivermos 20 sistemas (Ocorrências, Operações, RH, Frota, Viaturas...)
   e 50 agentes diferentes (um por delegacia, um por batalhão...), como
   isso evolui? Quantas vezes essa função (ou uma parecida) vai ser
   reescrita, em quantas linguagens, com quantos bugs sutis diferentes?"
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # aula5/ (provedor.py)

from agents import Agent, Runner, function_tool
from provedor import configurar

from consultar_ocorrencias import consultar_ocorrencias as _consultar_ocorrencias

configurar()


@function_tool
def consultar_ocorrencias() -> list[dict]:
    """Retorna as ocorrências mais recentes registradas na CISP (dados fictícios)."""
    return _consultar_ocorrencias()


agente = Agent(
    name="Assistente CISP",
    instructions=(
        "Você ajuda operadores da CISP a entender as ocorrências recentes. "
        "Use a ferramenta consultar_ocorrencias quando precisar de dados reais."
    ),
    tools=[consultar_ocorrencias],
)

if __name__ == "__main__":
    pergunta = "Quais ocorrências estão registradas agora? Resuma por tipo e região."
    resultado = Runner.run_sync(agente, pergunta)
    print(resultado.final_output)
