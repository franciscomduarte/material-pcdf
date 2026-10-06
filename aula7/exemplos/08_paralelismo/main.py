"""
ESQUELETO PARA IMPLEMENTAR AO VIVO (aula 7).
Implemente as etapas na ordem. Cada uma está marcada com um comentário e um
raise NotImplementedError: troque esse raise pelo código da etapa.
  ETAPA 1 -- O grafo sequencial, para comparar
  ETAPA 2 -- Medir o relógio
  ETAPA 3 -- Fan-out e fan-in: o grafo paralelo
O texto abaixo descreve o exemplo pronto.

Exemplo 08 -- PARALELISMO: especialistas independentes rodam AO MESMO TEMPO.

No exemplo 05 a equipe era uma fila: investigador -> jurídico -> analista. Mas o
enquadramento jurídico e a avaliação de risco dependem SÓ dos fatos, não um do outro.
Então podem rodar em paralelo (fan-out) e ser reunidos depois (fan-in), como o DAG da Aula 6:

                              ┌──> juridico ──┐
    START -> investigador ────┤               ├──> consolidar -> END
                              └──> risco ─────┘

  fan-out : dois add_edge saindo de "investigador"  -> os dois nós rodam no mesmo passo
  fan-in  : add_edge(["juridico", "risco"], "consolidar") -> "consolidar" ESPERA os dois

REGRA DE OURO DO PARALELISMO: ramos paralelos escrevem em campos DIFERENTES do estado.
(juridico -> analise_juridica; risco -> analise_risco.) Se os dois escrevessem no mesmo
campo, o LangGraph levantaria InvalidUpdateError, a menos que o campo tenha um "reducer".

O GANHO aparece no relógio, porque cada nó roda um Agent com chamada REAL ao LLM: em sequência o tempo é a
SOMA das duas chamadas; em paralelo, ~a MAIOR delas.
  - Com OpenAI o ganho é claro (as duas requisições correm juntas).
  - Com Ollama local, o servidor pode atender UMA requisição por vez (depende da memória/configuração,
    OLLAMA_NUM_PARALLEL): nesse caso os dois tempos ficam parecidos. Não é bug do grafo.

A ORDEM dos logs entre juridico e risco NÃO é garantida (é o esperado, não um bug).

Rodar, a partir de aula7/ (LLM REAL: configure o .env; veja o README):
    python exemplos\\08_paralelismo\\main.py
"""
import sys
import time
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


def investigador(estado: Estado) -> dict:
    print("[INVESTIGADOR]")
    return {"investigacao": Runner.run_sync(agentes.investigador, estado["solicitacao"]).final_output}


def juridico(estado: Estado) -> dict:
    print("[JURÍDICO]     início")
    parecer = Runner.run_sync(agentes.juridico, estado["investigacao"]).final_output
    print("[JURÍDICO]     fim")
    return {"analise_juridica": parecer}


def risco(estado: Estado) -> dict:
    print("[RISCO]        início")
    # só os FATOS: não depende do jurídico
    parecer = Runner.run_sync(agentes.risco, prompts.entrada_risco(estado["investigacao"])).final_output
    print("[RISCO]        fim")
    return {"analise_risco": parecer}


def consolidar(estado: Estado) -> dict:
    print("[CONSOLIDAR]   recebeu os DOIS pareceres")
    entrada = prompts.entrada_recomendar(estado["investigacao"], estado["analise_juridica"], estado["analise_risco"])
    return {"recomendacao": Runner.run_sync(agentes.redator, entrada).final_output}


def construir_paralelo():
    # ETAPA 3 -- em construir_paralelo: g = StateGraph(Estado) com os 4 nós
    #   START -> investigador; investigador -> juridico e investigador -> risco (fan-out)
    #   g.add_edge(["juridico", "risco"], "consolidar") (fan-in); consolidar -> END; return g.compile()
    raise NotImplementedError("ETAPA 3: construir_paralelo")


def construir_sequencial():
    # ETAPA 1 -- em construir_sequencial: os mesmos 4 nós em fila
    #   investigador -> juridico -> risco -> consolidar -> END
    raise NotImplementedError("ETAPA 1: construir_sequencial")


def medir(titulo: str, app) -> float:
    # ETAPA 2 -- em medir: imprima o título, marque o tempo com time.perf_counter()
    #   app.invoke com o estado inicial e devolva a duração
    raise NotImplementedError("ETAPA 2: medir")


if __name__ == "__main__":
    print(f"Modelo em uso: {MODELO}\n")
    seq = medir("SEQUENCIAL: juridico -> risco", construir_sequencial())
    par = medir("PARALELO: juridico e risco juntos", construir_paralelo())
    print(f"Sequencial {seq:.1f} s x paralelo {par:.1f} s.")
    print("Paralelismo só cabe onde os especialistas são INDEPENDENTES (aqui: ambos dependem só dos fatos).")
    print("Se o risco precisasse do parecer jurídico, a fila voltaria a ser obrigatória.")
