"""
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
"""
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

import prompts
from caso import DENUNCIA_045
from provedor import obter_modelo

modelo = obter_modelo()  # LLM REAL: PROVEDOR no .env (openai ou ollama)

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
    return {"investigacao": modelo.gerar(prompts.investigar(estado["solicitacao"]))}


def juridico(estado: Estado) -> dict:
    print("[JURÍDICO]")
    return {"analise_juridica": modelo.gerar(prompts.juridico(estado["investigacao"]))}


def analista(estado: Estado) -> dict:
    print("[ANALISTA]")
    fatos, enquadramento = estado["investigacao"], estado["analise_juridica"]
    risco = modelo.gerar(prompts.risco(fatos, enquadramento))
    return {"analise_risco": risco, "recomendacao": modelo.gerar(prompts.recomendar(fatos, enquadramento, risco))}


def construir(checkpointer):
    construtor = StateGraph(Estado)
    construtor.add_node("investigador", investigador)
    construtor.add_node("juridico", juridico)
    construtor.add_node("analista", analista)
    construtor.add_edge(START, "investigador")
    construtor.add_edge("investigador", "juridico")
    construtor.add_edge("juridico", "analista")
    construtor.add_edge("analista", END)
    # checkpointer = onde salvar; interrupt_before = onde parar (breakpoint)
    return construtor.compile(checkpointer=checkpointer, interrupt_before=["analista"])


def mostrar_estado(app, titulo: str) -> None:
    foto = app.get_state(CONFIG)
    print(f"\n{titulo}")
    print(f"  próximo nó a executar: {foto.next or '(nenhum: execução concluída)'}")
    for campo, valor in foto.values.items():
        print(f"  {campo:17}: {valor or '-'}")


def iniciar(app) -> None:
    print(f"== 1) EXECUÇÃO NOVA (thread_id={THREAD_ID}) ==")
    app.invoke({"solicitacao": DENUNCIA_045,
                "investigacao": "", "analise_juridica": "", "analise_risco": "", "recomendacao": ""}, CONFIG)
    mostrar_estado(app, "Execução INTERROMPIDA pelo breakpoint. Estado salvo em checkpoints.db:")


def retomar(app) -> None:
    foto = app.get_state(CONFIG)
    if not foto.next:
        raise SystemExit("Nada a retomar: rode primeiro `python main.py` (sem argumentos).")
    print(f"== 2) RETOMADA (thread_id={THREAD_ID}) a partir do checkpoint ==")
    app.invoke(None, CONFIG)  # None = "não há entrada nova: continue de onde parou"
    mostrar_estado(app, "Execução CONCLUÍDA:")


def historico(app) -> None:
    print(f"== Checkpoints da execução {THREAD_ID} (do mais recente ao mais antigo) ==")
    for foto in app.get_state_history(CONFIG):
        preenchidos = [c for c, v in foto.values.items() if v]
        print(f"  passo {foto.metadata.get('step'):>2} | próximo: {str(foto.next):18} | campos preenchidos: {preenchidos}")


if __name__ == "__main__":
    print(f"Modelo em uso: {modelo.nome}\n")
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
