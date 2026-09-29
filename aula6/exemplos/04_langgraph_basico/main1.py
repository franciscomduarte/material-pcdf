"""
Exemplo 04 -- PRIMEIRO LANGGRAPH.

No exemplo 03 escrevemos à mão o "motor" que executava os nós sobre o estado:

    for no in [...]:
        estado.update(no(estado))

Agora o LangGraph faz isso por nós -- e, nos próximos exemplos, também decide
QUAL nó vem a seguir. Grafo mínimo:

    START -> receber -> classificar -> END

Rodar:
    python main.py
"""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


# 1) O ESTADO: mesmo TypedDict do exemplo 03, só com o necessário.
class Estado(TypedDict):
    solicitacao: str
    categoria: str
    resultado: str


# 2) OS NÓS: funções comuns. Recebem o estado, devolvem a atualização.
def receber(estado: Estado) -> dict:
    print("[receber]")
    return {"solicitacao": estado["solicitacao"].strip()}


def classificar(estado: Estado) -> dict:
    print("[classificar]")
    return {"categoria": "simples"}

def analisar(estado: Estado) -> dict:
    print("[analisar]")
    return {"resultado": f"análise de solicitação {estado['categoria']}"}


# 3) O GRAFO: declaramos o tipo do estado que ele vai carregar.
construtor = StateGraph(Estado)

# 4) add_node("nome", funcao): registra um nó. O nome é o "rótulo" usado nas arestas.
construtor.add_node("receber", receber)
construtor.add_node("classificar", classificar)
construtor.add_node("analisar", analisar)

# 5) add_edge(origem, destino): registra uma aresta.
#    START e END são nós especiais: entrada e saída do grafo.
construtor.add_edge(START, "receber")
construtor.add_edge("receber", "classificar")
construtor.add_edge("classificar", "analisar")
construtor.add_edge("analisar", END)

# 6) compile(): valida o grafo (nó inexistente, sem entrada...) e devolve o executável.
app = construtor.compile()

# 7) invoke(estado_inicial): executa START -> ... -> END e devolve o estado FINAL.
#    Campos que os nós ainda não preencheram podem ser omitidos na entrada.
resultado = app.invoke({"solicitacao": "  Preciso saber como solicitar uma segunda via.  "})

print("\nEstado final:", resultado)

# Bônus: o grafo pode se desenhar. Cole a saída em https://mermaid.live
print("\nDiagrama (Mermaid):")
print(app.get_graph().draw_mermaid())

# ---------------------------------------------------------------------------
# Observe: não escrevemos laço nenhum. Descrevemos NÓS e ARESTAS; o LangGraph
# executa. Nesta versão a ordem ainda é fixa (só add_edge); no exemplo 06
# a ordem passa a depender do estado.
# ---------------------------------------------------------------------------
