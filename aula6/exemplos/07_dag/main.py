"""
Exemplo 07 -- DAG (Directed Acyclic Graph).

No exemplo 06 o grafo ramificava e os caminhos se reencontravam só no fim.
Agora as duas etapas rodam a partir do mesmo nó e CONVERGEM em 'consolidar':

             classificar
                  ↓
          ┌───────┴────────┐
          ↓                ↓
       pesquisar         analisar
          ↓                ↓
          └───────┬────────┘
                  ↓
              consolidar
                  ↓
               responder

Por que é um DAG?
  - DIRECIONADO: toda aresta tem sentido (classificar -> pesquisar, nunca o inverso).
  - ACÍCLICO:    não existe caminho que saia de um nó e volte a ele.
  - BRANCH:      'classificar' tem duas saídas (pesquisar e analisar).
  - MERGE:       'consolidar' tem duas entradas e só roda quando AMBAS terminam.

Detalhe do LangGraph: add_edge(["pesquisar", "analisar"], "consolidar")
(com LISTA) significa "espere todas". Duas chamadas add_edge separadas
disparariam consolidar quando QUALQUER uma terminasse.

Rodar:
    python main.py
"""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class Estado(TypedDict):
    solicitacao: str
    categoria: str
    informacao: str
    analise: str
    consolidado: str
    resposta: str


def classificar(estado: Estado) -> dict:
    print("[classificar]")
    return {"categoria": "complexa"}


def pesquisar(estado: Estado) -> dict:
    print("[pesquisar]   (ramo A)")
    return {"informacao": "levar documento com foto e pagar a taxa"}


def analisar(estado: Estado) -> dict:
    print("[analisar]    (ramo B)")
    return {"analise": "pedido de segunda via de documento"}


def consolidar(estado: Estado) -> dict:
    # aqui os DOIS ramos já escreveram no estado
    print("[consolidar]  (junção dos ramos)")
    return {"consolidado": f"{estado['analise']} -> {estado['informacao']}"}


def responder(estado: Estado) -> dict:
    print("[responder]")
    return {"resposta": f"Para sua solicitação ({estado['consolidado']})."}


construtor = StateGraph(Estado)
for nome, funcao in [
    ("classificar", classificar),
    ("pesquisar", pesquisar),
    ("analisar", analisar),
    ("consolidar", consolidar),
    ("responder", responder),
]:
    construtor.add_node(nome, funcao)

construtor.add_edge(START, "classificar")

# ATENÇÃO: os dois ramos rodam no mesmo passo; a ordem dos logs entre eles não é garantida.
# BRANCH: duas arestas saindo do mesmo nó (sem condição: as DUAS são seguidas)
construtor.add_edge("classificar", "pesquisar")
construtor.add_edge("classificar", "analisar")

# MERGE: lista = "espere todas terminarem"
construtor.add_edge(["pesquisar", "analisar"], "consolidar")

construtor.add_edge("consolidar", "responder")
construtor.add_edge("responder", END)

app = construtor.compile()

resultado = app.invoke({"solicitacao": "Preciso de uma segunda via."})

print("\nEstado final:")
for campo, valor in resultado.items():
    print(f"  {campo:12} = {valor!r}")

# ---------------------------------------------------------------------------
# Diferença para o exemplo 06:
#   06: add_conditional_edges  -> UM caminho é escolhido (ou-exclusivo).
#   07: dois add_edge iguais   -> os DOIS caminhos executam (fan-out) e
#                                 depois convergem (fan-in).
# Regra prática: os ramos paralelos devem escrever CAMPOS DIFERENTES do
# estado (aqui: informacao e analise), senão um sobrescreve o outro.
# ---------------------------------------------------------------------------
