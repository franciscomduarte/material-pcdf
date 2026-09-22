"""
Ex 10 (TODO) — Ferramenta de verdade (function_tool).
Cenário novo: um Perito usa uma ferramenta Python para consultar o protocolo
de coleta de um vestígio (tabela fictícia), em vez de decorar isso na
instructions. Rode: python todo/ex10_function_tool.py
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents import Agent, Runner, function_tool
from provedor import configurar

configurar()

# Tabela fictícia, só para a aula.
_PROTOCOLOS = {
    "sangue": ("kit hemostático", "refrigerar a 4°C"),
    "digital": ("pó magnético", "lacrar em envelope de papel"),
    "arma": ("luvas + swab", "fotografar antes de tocar"),
}


@function_tool
def consultar_protocolo(tipo_vestigio: str) -> str:
    """Consulta o protocolo de coleta (tabela fictícia) para um tipo de vestígio.

    Args:
        tipo_vestigio: nome do vestígio em minúsculas, ex.: "sangue", "digital", "arma".
    """
    # TODO 1: busque tipo_vestigio.lower() em _PROTOCOLOS (com um default para
    #         "desconhecido") e devolva um JSON (json.dumps) com as chaves
    #         "material" e "cuidado".
    ...


perito = Agent(
    name="Perito",
    instructions=(
        "Identifique o(s) vestígio(s) citados na cena e USE a ferramenta "
        "consultar_protocolo para cada um antes de responder."
    ),
    # TODO 2: registre a ferramenta em tools=[...]
    tools=[],
)

if __name__ == "__main__":
    cena = "Cena com manchas de sangue no chão e uma impressão digital na maçaneta."
    print(Runner.run_sync(perito, cena).final_output)
