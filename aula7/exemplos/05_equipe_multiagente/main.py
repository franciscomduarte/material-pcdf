"""
Exemplo 05 -- EQUIPE MULTIAGENTE: especialistas como NÓS de um grafo (LangGraph).

Juntamos o que vimos: especialistas (ex. 02) + estado compartilhado (ex. 03) +
grafo da Aula 6. Cada especialista é um nó; o estado é o que circula entre eles:

    START -> orquestrador -> investigador -> juridico -> analista -> END
                 |               |              |            |
              prepara o       fatos        enquadramento   risco +
              estado                          legal      recomendação

Quem é o ORQUESTRADOR? Quem decide a ORDEM e as condições de passagem entre os
especialistas. Aqui ele é o próprio grafo (mais um nó de entrada que prepara o
estado): a ordem é explícita e inspecionável. (Outra forma é um LLM que escolhe
o próximo especialista; troca-se controle por flexibilidade. Nesta aula o
controle é do grafo.)

Cada especialista poderia ter FERRAMENTAS diferentes -- conexão com a Aula 5:

    INVESTIGADOR -> MCP -> dados da contratação        JURÍDICO -> MCP -> base normativa

Aqui os nós só chamam o LLM, para o código caber na tela; trocar por chamadas
MCP é o que fizemos no exemplo 11 da Aula 6.

Rodar (LLM REAL: configure o .env; veja o README), a partir de aula7/:
    python exemplos\\05_equipe_multiagente\\main.py
    $env:PROVEDOR = "claude"   # mesmo grafo, outro modelo (exige ANTHROPIC_API_KEY)
"""
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from langgraph.graph import END, START, StateGraph

import prompts
from caso import DENUNCIA_045
from provedor import obter_modelo

modelo = obter_modelo()  # LLM REAL: PROVEDOR no .env (openai ou ollama)


class Estado(TypedDict):
    solicitacao: str
    investigacao: str
    analise_juridica: str
    analise_risco: str
    recomendacao: str


def orquestrador(estado: Estado) -> dict:
    print("[ORQUESTRADOR] plano: investigador -> jurídico -> analista")
    return {"solicitacao": estado["solicitacao"].strip(),
            "investigacao": "", "analise_juridica": "", "analise_risco": "", "recomendacao": ""}


def investigador(estado: Estado) -> dict:
    print("[INVESTIGADOR] levantando os fatos")
    return {"investigacao": modelo.gerar(prompts.investigar(estado["solicitacao"]))}


def juridico(estado: Estado) -> dict:
    print("[JURÍDICO]     enquadrando na lei")
    return {"analise_juridica": modelo.gerar(prompts.juridico(estado["investigacao"]))}


def analista(estado: Estado) -> dict:
    print("[ANALISTA]     avaliando risco e recomendando")
    fatos, enquadramento = estado["investigacao"], estado["analise_juridica"]
    risco = modelo.gerar(prompts.risco(fatos, enquadramento))
    recomendacao = modelo.gerar(prompts.recomendar(fatos, enquadramento, risco))
    return {"analise_risco": risco, "recomendacao": recomendacao}


construtor = StateGraph(Estado)
for nome, funcao in [
    ("orquestrador", orquestrador),
    ("investigador", investigador),
    ("juridico", juridico),
    ("analista", analista),
]:
    construtor.add_node(nome, funcao)

construtor.add_edge(START, "orquestrador")
construtor.add_edge("orquestrador", "investigador")
construtor.add_edge("investigador", "juridico")
construtor.add_edge("juridico", "analista")
construtor.add_edge("analista", END)

app = construtor.compile()

if __name__ == "__main__":
    print(f"Modelo em uso: {modelo.nome}\n")
    estado: dict = {"solicitacao": DENUNCIA_045}
    caminho = []
    for passo in app.stream(estado, stream_mode="updates"):
        for no, atualizacao in passo.items():
            caminho.append(no)
            estado.update(atualizacao)

    print("\nCaminho:", " -> ".join(caminho))
    print("\nEstado final:")
    for campo, valor in estado.items():
        print(f"  {campo:17}: {valor}")
    print("\nTudo automático, do começo ao fim. E se a recomendação for ruim? Ninguém a revisou.")
    print("Próximo exemplo: colocar um HUMANO no meio do fluxo.")
