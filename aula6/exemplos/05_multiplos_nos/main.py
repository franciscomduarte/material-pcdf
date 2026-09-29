"""
Exemplo 05 -- MÚLTIPLOS NÓS e ATUALIZAÇÃO DE ESTADO.

No exemplo anterior tínhamos 2 nós. Agora o grafo completo, ainda linear:

    START -> receber -> classificar -> analisar -> responder -> END

O ponto novo é conceitual: o que um nó DEVOLVE.

    return estado                      # devolve o estado inteiro
    return {"categoria": "simples"}    # devolve só a ATUALIZAÇÃO

O LangGraph mescla o dicionário devolvido no estado (como o .update() do
exemplo 03). Campos não citados ficam como estavam. Por isso a forma
recomendada é devolver apenas o que o nó mudou: fica claro quem é
responsável por cada campo.

Rodar:
    python main.py
"""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class Estado(TypedDict):
    solicitacao: str
    categoria: str
    resultado: str
    resposta: str


def receber(estado: Estado) -> dict:
    print("[receber]     escreve: solicitacao")
    return {"solicitacao": estado["solicitacao"].strip()}


def classificar(estado: Estado) -> dict:
    print("[classificar] escreve: categoria")
    return {"categoria": "simples"}


def analisar(estado: Estado) -> dict:
    print("[analisar]    lê: categoria | escreve: resultado")
    return {"resultado": f"análise de solicitação {estado['categoria']}"}


def responder(estado: Estado) -> dict:
    print("[responder]   lê: resultado  | escreve: resposta")
    return {"resposta": f"Resposta baseada em: {estado['resultado']}"}


construtor = StateGraph(Estado)
construtor.add_node("receber", receber)
construtor.add_node("classificar", classificar)
construtor.add_node("analisar", analisar)
construtor.add_node("responder", responder)

construtor.add_edge(START, "receber")
construtor.add_edge("receber", "classificar")
construtor.add_edge("classificar", "analisar")
construtor.add_edge("analisar", "responder")
construtor.add_edge("responder", END)

app = construtor.compile()

resultado = app.invoke({"solicitacao": "  Preciso saber como solicitar uma segunda via.  "})

print("\nEstado final:")
for campo, valor in resultado.items():
    print(f"  {campo:12} = {valor!r}")

# ---------------------------------------------------------------------------
# Acompanhando o estado a cada nó: app.stream(..., stream_mode="updates")
# devolve, PASSO A PASSO, exatamente o que cada nó retornou -- a atualização,
# não o estado inteiro. É a melhor forma de ver a diferença.
# ---------------------------------------------------------------------------
print("\n=== Atualizações emitidas por cada nó (stream_mode='updates') ===")
for passo in app.stream(
    {"solicitacao": "Preciso saber como solicitar uma segunda via."},
    stream_mode="updates",
):
    for no, atualizacao in passo.items():
        print(f"  {no:12} -> {atualizacao}")

# ---------------------------------------------------------------------------
# Experimento (2 min): troque `return {"categoria": "simples"}` em classificar
# por `return {}` e rode. O que acontece com 'analisar'? Por quê?
# (Dica: o campo nunca foi escrito -> KeyError em estado["categoria"].)
# ---------------------------------------------------------------------------
