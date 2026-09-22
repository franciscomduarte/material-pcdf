"""
Ex 2 (TODO) — Roteamento entre Jurídico e Estatística.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents import Agent, Runner
from provedor import configurar

configurar()

# TODO 1: agente Jurídico (2 linhas de parecer)
juridico = ...
# TODO 2: agente Estatística (1 linha, categoria)
estatistica = ...

# TODO 3: Triagem com handoffs=[juridico, estatistica] e instruções de quando usar cada um
triagem = ...

if __name__ == "__main__":
    casos = [
        "Estelionato: vítima relata transferência feita mediante golpe do "
        "falso motoboy, em Taguatinga.",
        "Solicitação de cópia de boletim de ocorrência antigo para fins de "
        "seguro, sem novo fato a registrar.",
    ]
    for caso in casos:
        print(f"\n>>> {caso}")
        # TODO 4: rode e imprima
        ...