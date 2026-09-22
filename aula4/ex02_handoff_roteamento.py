"""
Exercício 2 — Roteamento entre múltiplos especialistas (síncrono)
A Triagem agora escolhe ENTRE dois destinos conforme o conteúdo.

Fluxo: Triagem -> Jurídico (se crime) OU Estatística (se apenas registro).
Rode: python ex02_handoff_roteamento.py
"""
from agents import Agent, Runner
from provedor import configurar

configurar()

juridico = Agent(
    name="Juridico",
    instructions="Avalie o enquadramento legal e cite o artigo provável, em 2 linhas.",
)

estatistica = Agent(
    name="Estatistica",
    instructions="Registre a ocorrência para fins estatísticos e diga a categoria, em 1 linha.",
)

triagem = Agent(
    name="Triagem",
    instructions=(
        "Você tria ocorrências. Se houver indício de crime, encaminhe ao Jurídico. "
        "Se for apenas um registro administrativo sem crime, encaminhe à Estatística."
    ),
    handoffs=[juridico, estatistica],
)

if __name__ == "__main__":
    casos = [
        "Roubo à mão armada em estabelecimento comercial em Ceilândia.",
        "Registro de achados e perdidos: bicicleta encontrada no Parque da Cidade.",
    ]
    for caso in casos:
        print(f"\n>>> {caso}")
        print(Runner.run_sync(triagem, caso).final_output)