"""
ESQUELETO PARA IMPLEMENTAR AO VIVO (aula 7).
Implemente as etapas na ordem. Cada uma está marcada com um comentário e um
raise NotImplementedError: troque esse raise pelo código da etapa.
  ETAPA 1 -- O grafo com checkpointer e breakpoint
  ETAPA 2 -- Iniciar: rodar até o breakpoint
  ETAPA 3 -- Ler o estado salvo
  ETAPA 4 -- Retomar em outro processo
  ETAPA 5 -- O histórico de checkpoints
O texto abaixo descreve o exemplo pronto.

Exemplo 04 -- PERSISTÊNCIA: checkpoint e recuperação (agora com LangGraph).

No exemplo 03 o estado vivia numa variável: se o processo morresse, tudo se perdia.
Agora o LangGraph salva um CHECKPOINT (uma "foto" do estado) a cada passo, num
banco SQLite. Cada execução tem uma identidade, o thread_id.

    START -> investigador -> juridico -> [BREAKPOINT] -> analista -> END
                                              |
                                  execução INTERROMPIDA aqui;
                                  o estado fica salvo no SQLite

BREAKPOINT ESTÁTICO: compile(..., interrupt_before=["analista"]) manda o grafo
parar ANTES de executar aquele nó. (No exemplo 06 veremos o interrupt() dinâmico,
que pausa DENTRO de um nó e devolve uma pergunta ao humano.)

Como o estado está no arquivo .db, dá para retomar em OUTRO processo:

    python exemplos\\04_persistencia\\main.py               # roda até o breakpoint e ENCERRA
    python exemplos\\04_persistencia\\main.py --retomar     # outro processo: lê o checkpoint e continua
    python exemplos\\04_persistencia\\main.py --historico   # lista os checkpoints da execução
    python exemplos\\04_persistencia\\main.py --auto        # tudo no mesmo processo (demonstração rápida)

O foco NÃO é banco de dados: é  estado -> checkpoint -> persistência -> retomada.
Os nós rodam os agentes de agentes.py (Agent + Runner), como no exemplo 03.
"""
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Runner
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

import agentes
import prompts
from caso import DENUNCIA_045
from provedor import configurar

MODELO = configurar()  # LLM REAL: PROVEDOR no .env (openai ou ollama)

DB = Path(__file__).resolve().parent / "checkpoints.db"
THREAD_ID = "denuncia-045"
CONFIG = {"configurable": {"thread_id": THREAD_ID}}  # identifica ESTA execução


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
    print("[JURÍDICO]")
    return {"analise_juridica": Runner.run_sync(agentes.juridico, estado["investigacao"]).final_output}


def analista(estado: Estado) -> dict:
    print("[ANALISTA]")
    fatos, enquadramento = estado["investigacao"], estado["analise_juridica"]
    risco = Runner.run_sync(agentes.risco, prompts.entrada_risco(fatos, enquadramento)).final_output
    recomendacao = Runner.run_sync(agentes.redator, prompts.entrada_recomendar(fatos, enquadramento, risco)).final_output
    return {"analise_risco": risco, "recomendacao": recomendacao}


def construir(checkpointer):
    construtor = StateGraph(Estado)
    construtor.add_node("investigador", investigador)
    construtor.add_node("juridico", juridico)
    construtor.add_node("analista", analista)

    construtor.add_edge(START, "investigador")
    construtor.add_edge("investigador", "juridico")
    construtor.add_edge("juridico", "analista")

    return construtor.compile(checkpointer=checkpointer, interrupt_before=["analista"])


def mostrar_estado(app, titulo: str) -> None:
    print(f"\n{titulo}")
    print(f"Thread: {THREAD_ID}")
    print(f" Próximo nó: {app.next_node}")
    foto = app.get_state(CONFIG)
    for campo, valor in foto.items():
        print(f" {campo}: {valor}")



def iniciar(app) -> None:
    app.invoke({
        "solicitacao": DENUNCIA_045,
        "investigacao": "",
        "analise_juridica": "",
        "analise_risco": "",
        "recomendacao": "",
    }, CONFIG)

    mostrar_estado(app, "Execução INTERROPIDA no BREAKPOINT (antes de analista)")


def retomar(app) -> None:
    foto = app.get_state(CONFIG)
    if not foto.next:
        raise SystemExit("Não há checkpoint salvo: rode sem --retomar primeiro.")
    app.invoke(None, CONFIG)
    mostrar_estado(app, "Execução RETOMADA e FINALIZADA")


def historico(app) -> None:
    print(f"\nHistórico de checkpoints da thread {THREAD_ID}:")
    for foto in app.get_state_history(CONFIG):
        print(f"  {foto.metadata.get('step'):>2} -> {foto.next}")


if __name__ == "__main__":
    print(f"Modelo em uso: {MODELO}\n")
    argumentos = sys.argv[1:]
    if not argumentos or "--auto" in argumentos:
        DB.unlink(missing_ok=True)  # demonstração limpa: recomeça o banco

    with SqliteSaver.from_conn_string(str(DB)) as checkpointer:
        app = construir(checkpointer)
        if "--retomar" in argumentos:
            retomar(app)
        elif "--historico" in argumentos:
            historico(app)
        else:
            iniciar(app)
            if "--auto" in argumentos:
                print()
                retomar(app)
            else:
                print("\nO processo vai terminar agora. Retome em OUTRO processo com:")
                print("    python exemplos\\04_persistencia\\main.py --retomar")
