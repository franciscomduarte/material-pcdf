"""
Exemplo 08 -- FLUXO CÍCLICO e CONDIÇÃO DE PARADA.

No exemplo 07 o grafo era um DAG: sempre avança. Agora adicionamos a VOLTA:

   analisar
      ↓
   validar
      ↓
 ┌────┴───────────┐
 ↓                ↓
OK               ERRO
 ↓                ↓
responder       revisar
                  ↓
                  └────→ analisar        <- CICLO

Estado novo:  tentativas: int   e   validada: bool

UM CICLO EM UM SISTEMA DE AGENTES PRECISA TER CONDIÇÃO DE PARADA.
Sem ela, o sistema executa  A -> B -> A -> B -> A -> ...  para sempre
(ou até gastar todo o orçamento de chamadas ao LLM).

Aqui a parada é dupla e o roteador a impõe:
    - validada == True          -> responder   (sucesso)
    - tentativas >= MAX         -> responder   (desistimos: melhor resposta possível)
    - caso contrário            -> revisar -> analisar (volta)

PARTE 2 do arquivo: o mesmo grafo SEM a condição de parada, para você ver o
LangGraph derrubar a execução com GraphRecursionError (rede de segurança).

Rodar:
    python main.py
"""
from typing import TypedDict

from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph

MAX_TENTATIVAS = 3


class Estado(TypedDict):
    solicitacao: str
    analise: str
    validada: bool
    tentativas: int
    resposta: str


def analisar(estado: Estado) -> dict:
    tentativa = estado["tentativas"] + 1
    print(f"[analisar]  tentativa {tentativa}")
    # simulação: a análise só fica completa a partir da 2ª tentativa
    if tentativa < 2:
        analise = "análise incompleta"
    else:
        analise = "análise completa: agendar, levar documento com foto, pagar taxa"
    return {"analise": analise, "tentativas": tentativa}


def validar(estado: Estado) -> dict:
    ok = "completa:" in estado["analise"]
    print(f"[validar]   {'OK' if ok else 'ERRO'}")
    return {"validada": ok}


def validar_sempre_reprova(estado: Estado) -> dict:
    """Validador rigoroso demais, usado só para forçar o pior caso."""
    print("[validar]   ERRO (este validador reprova sempre)")
    return {"validada": False}


def revisar(estado: Estado) -> dict:
    print("[revisar]   pedindo análise mais detalhada")
    return {}  # não altera campos; só existe para fazer a volta (no LLM, ajustaria o prompt)


def responder(estado: Estado) -> dict:
    print("[responder]")
    prefixo = "" if estado["validada"] else "(sem validação) "
    return {"resposta": prefixo + estado["analise"]}


# --- O ROTEADOR DO CICLO: aqui mora a condição de parada ---------------------
def rotear_apos_validar(estado: Estado) -> str:
    if estado["validada"]:
        return "ok"
    if estado["tentativas"] >= MAX_TENTATIVAS:
        return "desistir"  # PARADA: esgotou as tentativas
    return "revisar"


def montar(com_parada: bool, no_validar=validar):
    construtor = StateGraph(Estado)
    construtor.add_node("analisar", analisar)
    construtor.add_node("validar", no_validar)
    construtor.add_node("revisar", revisar)
    construtor.add_node("responder", responder)

    construtor.add_edge(START, "analisar")
    construtor.add_edge("analisar", "validar")

    if com_parada:
        construtor.add_conditional_edges(
            "validar",
            rotear_apos_validar,
            {"ok": "responder", "desistir": "responder", "revisar": "revisar"},
        )
    else:
        # SEM condição de parada: se não valida, SEMPRE revisa. (Perigoso!)
        construtor.add_conditional_edges(
            "validar",
            lambda e: "ok" if e["validada"] else "revisar",
            {"ok": "responder", "revisar": "revisar"},
        )

    construtor.add_edge("revisar", "analisar")  # <- a aresta que forma o CICLO
    construtor.add_edge("responder", END)
    return construtor.compile()


inicial = {"solicitacao": "Como pedir segunda via?", "tentativas": 0, "validada": False}

print("=" * 60)
print("CASO 1: ciclo com validação que passa na 2ª tentativa")
print("=" * 60)
resultado = montar(com_parada=True).invoke(inicial)
print(f"\nResposta: {resultado['resposta']}  (tentativas: {resultado['tentativas']})")

print("\n" + "=" * 60)
print(f"CASO 2: validação NUNCA passa -> para em {MAX_TENTATIVAS} tentativas")
print("=" * 60)
resultado = montar(com_parada=True, no_validar=validar_sempre_reprova).invoke(inicial)
print(f"\nResposta: {resultado['resposta']}  (tentativas: {resultado['tentativas']})")

print("\n" + "=" * 60)
print("CASO 3: MESMO CICLO SEM CONDIÇÃO DE PARADA (só a rede de segurança)")
print("=" * 60)
try:
    # recursion_limit = número máximo de passos (nós executados) antes de abortar
    montar(com_parada=False, no_validar=validar_sempre_reprova).invoke(inicial, {"recursion_limit": 12})
except GraphRecursionError:
    print("\n>>> GraphRecursionError: o grafo excedeu 12 passos.")
    print(">>> Sem condição de parada, o ciclo A -> B -> A -> B ... nunca termina.")

# ---------------------------------------------------------------------------
# Lições:
#  1. O ciclo é só uma aresta que volta ('revisar' -> 'analisar').
#  2. Quem impede o loop infinito é o ROTEADOR, lendo 'tentativas' no estado.
#     Por isso o contador de tentativas faz parte do ESTADO.
#  3. recursion_limit é o último recurso do LangGraph, não a sua lógica de parada.
#     Nunca dependa dele para encerrar o fluxo normalmente.
# ---------------------------------------------------------------------------
