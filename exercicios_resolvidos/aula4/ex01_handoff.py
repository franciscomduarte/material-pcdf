"""
Ex 1 (TODO) — Handoff básico. Complete os pontos marcados com # TODO.
Rode: python todo/ex01_handoff.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # acha provedor.py
from agents import Agent, Runner
from provedor import configurar

configurar()

# TODO 1: crie o agente Jurídico (name + instructions de enquadramento legal)
juridico = ...

# TODO 2: crie o agente Triagem que classifica e, se houver crime, delega ao Jurídico.
#         Dica: use handoffs=[juridico]
triagem = ...

if __name__ == "__main__":
    ocorrencia = (
        "Depredação de patrimônio público em escola no Guará: pichação e "
        "vidros quebrados, sem testemunhas identificadas."
    )
    # TODO 3: rode a Triagem com Runner.run_sync(...) e imprima o final_output
    ...