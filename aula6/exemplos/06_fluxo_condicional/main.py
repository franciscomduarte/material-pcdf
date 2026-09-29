"""
Exemplo 06 -- FLUXO CONDICIONAL.

No exemplo 05 o grafo era uma linha reta. Agora 'classificar' DECIDE o caminho:

                 classificar
                      |
              ┌───────┴───────┐
              ↓               ↓
           simples         complexa
              ↓               ↓
          responder       pesquisar
                              ↓
                           analisar
                              ↓
                           responder

Ferramenta nova: add_conditional_edges(origem, roteador, mapa)

  - QUEM DECIDE?      uma função de roteamento (roteador), que LÊ o estado.
  - O QUE RETORNA?    uma string: o rótulo do caminho escolhido.
  - COMO O LANGGRAPH  procura esse rótulo no 'mapa' e segue para o nó indicado.
    ESCOLHE?
  - POR QUE NÃO SÓ    porque só UM caminho executa. Chamar todas as funções
    CHAMAR TUDO?      e filtrar depois desperdiça trabalho (e, com LLM/tools,
                      dinheiro e efeitos colaterais).

Rodar:
    python main.py
"""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class Estado(TypedDict):
    solicitacao: str
    categoria: str
    informacao: str
    resultado: str
    resposta: str


def receber(estado: Estado) -> dict:
    print("[receber]")
    return {"solicitacao": estado["solicitacao"].strip()}


def classificar(estado: Estado) -> dict:
    """Aqui a regra é simples (tamanho do texto). Nos exemplos 09/10 será um LLM."""
    print("[classificar]")
    complexa = len(estado["solicitacao"].split()) > 8
    return {"categoria": "complexa" if complexa else "simples"}


def pesquisar(estado: Estado) -> dict:
    print("[pesquisar]")
    return {"informacao": "Procedimento: agendar, levar documento com foto, pagar taxa."}


def analisar(estado: Estado) -> dict:
    print("[analisar]")
    return {"resultado": f"análise com base em: {estado['informacao']}"}


def responder(estado: Estado) -> dict:
    print("[responder]")
    base = estado.get("resultado") or "resposta direta"
    return {"resposta": f"Resposta ({estado['categoria']}): {base}"}


# --- O ROTEADOR -----------------------------------------------------------
# NÃO é um nó: não altera o estado. Só lê e devolve o rótulo do próximo passo.
def rotear_apos_classificar(estado: Estado) -> str:
    return estado["categoria"]  # "simples" ou "complexa"


construtor = StateGraph(Estado)
construtor.add_node("receber", receber)
construtor.add_node("classificar", classificar)
construtor.add_node("pesquisar", pesquisar)
construtor.add_node("analisar", analisar)
construtor.add_node("responder", responder)

construtor.add_edge(START, "receber")
construtor.add_edge("receber", "classificar")

# rótulo devolvido pelo roteador  ->  nó de destino
construtor.add_conditional_edges(
    "classificar",
    rotear_apos_classificar,
    {"simples": "responder", "complexa": "pesquisar"},
)

construtor.add_edge("pesquisar", "analisar")
construtor.add_edge("analisar", "responder")
construtor.add_edge("responder", END)

app = construtor.compile()

casos = [
    "Preciso de uma segunda via.",
    "Preciso saber quais são os procedimentos, prazos e taxas para solicitar "
    "uma segunda via de um documento perdido.",
]

for solicitacao in casos:
    print("=" * 60)
    print("Solicitação:", solicitacao)
    resultado = app.invoke({"solicitacao": solicitacao})
    print("Categoria  :", resultado["categoria"])
    print("Resposta   :", resultado["resposta"], "\n")

# ---------------------------------------------------------------------------
# Repare no log: na solicitação simples NÃO aparecem [pesquisar] nem [analisar].
# O grafo pulou essas etapas -- a decisão é parte da estrutura, não de um if
# escondido dentro de uma função.
# ---------------------------------------------------------------------------
