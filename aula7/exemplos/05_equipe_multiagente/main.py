"""
ESQUELETO PARA IMPLEMENTAR AO VIVO (aula 7).
Implemente as etapas na ordem. Cada uma está marcada com um comentário e um
raise NotImplementedError: troque esse raise pelo código da etapa.
  ETAPA 1 -- Ligar o grafo
  ETAPA 2 -- Executar e mostrar o caminho
  ETAPA 3 -- O orquestrador prepara o estado
O texto abaixo descreve o exemplo pronto.

Exemplo 05 -- EQUIPE MULTIAGENTE: especialistas como NÓS de um grafo (LangGraph).

Juntamos o que vimos: especialistas (ex. 02) + estado compartilhado (ex. 03) +
grafo da Aula 6. Cada especialista é um nó (que roda um Agent); o estado é o que circula entre eles:

    START -> orquestrador -> investigador -> juridico -> analista -> END
                 |               |              |            |
              prepara o       fatos        enquadramento   risco +
              estado                          legal      recomendação

Quem é o ORQUESTRADOR? Quem decide a ORDEM e as condições de passagem entre os
especialistas. Aqui ele é o próprio grafo (mais um nó de entrada que prepara o
estado): a ordem é explícita e inspecionável. (Outra forma é um agente que escolhe
o próximo especialista, com handoffs, como na Aula 4; troca-se controle por flexibilidade.
Nesta aula o controle é do grafo.)

Cada especialista poderia ter FERRAMENTAS diferentes -- conexão com a Aula 5:

    INVESTIGADOR -> MCP -> dados da contratação        JURÍDICO -> MCP -> base normativa

Aqui os agentes só conversam com o LLM, para o código caber na tela; trocar por chamadas
MCP é o que fizemos no exemplo 11 da Aula 6.

Rodar (LLM REAL: configure o .env; veja o README), a partir de aula7/:
    python exemplos\\05_equipe_multiagente\\main.py
    $env:PROVEDOR = "ollama"   # mesmo grafo, outro modelo (exige `ollama serve`)
"""
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Runner
from langgraph.graph import END, START, StateGraph

import agentes
import prompts
from caso import DENUNCIA_045
from provedor import configurar

MODELO = configurar()  # LLM REAL: PROVEDOR no .env (openai ou ollama)


class Estado(TypedDict):
    solicitacao: str
    investigacao: str
    analise_juridica: str
    analise_risco: str
    recomendacao: str


def orquestrador(estado: Estado) -> dict:
    # ETAPA 3 -- em orquestrador: imprima o plano
    #   devolva solicitacao (strip) e os demais campos vazios
    raise NotImplementedError("ETAPA 3: orquestrador")


def investigador(estado: Estado) -> dict:
    print("[INVESTIGADOR] levantando os fatos")
    return {"investigacao": Runner.run_sync(agentes.investigador, estado["solicitacao"]).final_output}


def juridico(estado: Estado) -> dict:
    print("[JURÍDICO]     enquadrando na lei")
    return {"analise_juridica": Runner.run_sync(agentes.juridico, estado["investigacao"]).final_output}


def analista(estado: Estado) -> dict:
    print("[ANALISTA]     avaliando risco e recomendando")
    fatos, enquadramento = estado["investigacao"], estado["analise_juridica"]
    risco = Runner.run_sync(agentes.risco, prompts.entrada_risco(fatos, enquadramento)).final_output
    recomendacao = Runner.run_sync(agentes.redator, prompts.entrada_recomendar(fatos, enquadramento, risco)).final_output
    return {"analise_risco": risco, "recomendacao": recomendacao}


# ETAPA 1 -- crie o StateGraph(Estado), adicione os 4 nós (add_node)
#   add_edge: START -> orquestrador -> investigador -> juridico -> analista -> END
#   app = construtor.compile()
raise NotImplementedError("ETAPA 1: montagem do grafo")

if __name__ == "__main__":
    print(f"Modelo em uso: {MODELO}\n")
    # ETAPA 2 -- bloco principal: estado inicial com a DENUNCIA_045
    #   percorra app.stream(estado, stream_mode="updates"), junte o caminho e aplique cada atualização
    #   imprima o caminho e o estado final
    raise NotImplementedError("ETAPA 2: execução do grafo")
    print("\nTudo automático, do começo ao fim. E se a recomendação for ruim? Ninguém a revisou.")
    print("Próximo exemplo: colocar um HUMANO no meio do fluxo.")
