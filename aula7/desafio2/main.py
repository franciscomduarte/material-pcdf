"""
Desafio 2 da Aula 7 -- esqueleto. Implemente construir_grafo(); o resto já vem pronto.

Rodar, a partir de aula7/:
    python desafio2/main.py
    python -m unittest desafio2.test_desafio2 -v
"""
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents import Runner  # noqa: F401  (roda os agentes: Runner.run_sync(agente, entrada).final_output)
from langgraph.graph import END, START, StateGraph  # noqa: F401
from langgraph.types import Command, interrupt  # noqa: F401

import agentes  # noqa: F401  (os agentes prontos: investigador, juridico, risco, classificador, redator, ...)
import prompts  # noqa: F401  (entradas dos agentes e nivel_de)
from caso import DENUNCIA_045, DENUNCIA_BAIXO_VALOR

MAX_TENTATIVAS = 3
FEEDBACK_PADRAO = "Faltam ações numeradas, responsáveis e prazos."


class Estado(TypedDict):
    solicitacao: str
    investigacao: str
    analise_juridica: str
    analise_risco: str
    nivel_risco: str      # "alto" | "baixo"
    parecer: str
    aprovado: bool
    feedback_humano: str
    tentativas: int
    status: str           # "aprovada" | "limite_de_revisoes" | "negada_pelo_diretor"


def construir_grafo(checkpointer):
    """TODO: monte o grafo (nós, roteadores e arestas) e devolva g.compile(checkpointer=checkpointer).

    Nós (nomes exatos): receber, investigar, juridico, risco, consolidar, aprovacao_gestor, revisar,
    aprovacao_diretor, finalizar, encerrar, negar.

    O grafo a montar:

        START → receber → investigar ─┬─> juridico ─┐    (PARALELO: dois add_edge saindo de investigar;
                                      └─> risco ────┴─>   consolidar ESPERA os dois: add_edge([..], ..))
                                                     consolidar   (tentativas + 1; lê feedback_humano) <──┐
                                                          │                                               │
                                                          v                                               │
                                                 aprovacao_gestor   <- interrupt()                        │
                                                          │                                               │
                                                          ├── "revisar"  ──> revisar ─────────────────────┘
                                                          ├── "desistir" ──> encerrar ──> END
                                                          ├── "finalizar" (risco baixo) ──> finalizar ──> END
                                                          └── "diretor"   (risco alto)  ──> aprovacao_diretor   <- interrupt()
                                                                                              ├── "finalizar" ──> finalizar ──> END
                                                                                              └── "negar"     ──> negar ──> END

    Roteadores (só LEEM o estado):
        após aprovacao_gestor  -> "diretor" | "finalizar" | "revisar" | "desistir"
        após aprovacao_diretor -> "finalizar" | "negar"

    Status final: "aprovada" | "limite_de_revisoes" | "negada_pelo_diretor".

    Como chamar os agentes (REAIS; já estão prontos em agentes.py, e as entradas em prompts.py):
        investigar -> Runner.run_sync(agentes.investigador, estado["solicitacao"]).final_output
        juridico   -> Runner.run_sync(agentes.juridico, estado["investigacao"]).final_output
        risco      -> parecer = Runner.run_sync(agentes.risco, prompts.entrada_risco(estado["investigacao"])).final_output
                      # vai em analise_risco
                      entrada = prompts.entrada_classificar(estado["solicitacao"], estado["investigacao"])
                      classe = Runner.run_sync(agentes.classificador, entrada).final_output
                      nivel_risco = prompts.nivel_de(classe)   # "alto" | "baixo": é ele que DECIDE o caminho
        consolidar -> entrada = prompts.entrada_recomendar(investigacao, analise_juridica, analise_risco, feedback_humano)
                      Runner.run_sync(agentes.redator, entrada).final_output

    Veja o enunciado em README.md e os exemplos 07 e 08 da aula.
    """
    raise NotImplementedError("Implemente construir_grafo()")


def executar(app, solicitacao: str, decisoes: list[str] | None = None, thread_id: str = "caso") -> tuple[dict, list[str]]:
    """Roda o grafo; cada pausa consome a próxima decisão ("sim"/"nao"), na ordem em que as pausas ocorrem.
    Devolve (estado_final, caminho). ATENÇÃO: a ordem de juridico/risco no caminho NÃO é garantida."""
    config = {"configurable": {"thread_id": thread_id}}
    decisoes = list(decisoes or [])
    caminho: list[str] = []
    entrada = {"solicitacao": solicitacao, "investigacao": "", "analise_juridica": "", "analise_risco": "",
               "nivel_risco": "", "parecer": "", "aprovado": False, "feedback_humano": "", "tentativas": 0,
               "status": ""}
    while True:
        pausou = False
        for parte in app.stream(entrada, config, stream_mode="updates"):
            for no in parte:
                if no == "__interrupt__":
                    pausou = True
                else:
                    caminho.append(no)
        if not pausou:
            return app.get_state(config).values, caminho
        aprovado = (decisoes.pop(0) if decisoes else "nao") == "sim"
        entrada = Command(resume={"aprovado": aprovado, "feedback": "" if aprovado else FEEDBACK_PADRAO})


CASOS = [
    ("Caso 1: baixo risco, só o gestor", DENUNCIA_BAIXO_VALOR, ["sim"]),
    ("Caso 2: alto risco, gestor e diretor aprovam", DENUNCIA_045, ["sim", "sim"]),
    ("Caso 3: gestor rejeita 1x, depois os dois aprovam", DENUNCIA_045, ["nao", "sim", "sim"]),
    ("Caso 4: diretor nega", DENUNCIA_045, ["sim", "nao"]),
    ("Caso 5: gestor rejeita sempre", DENUNCIA_045, ["nao", "nao", "nao"]),
]

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from langgraph.checkpoint.memory import MemorySaver
    from provedor import configurar

    print(f"Modelo em uso: {configurar()}\n")  # LLM REAL: PROVEDOR no .env (openai ou ollama)
    for i, (titulo, texto, decisoes) in enumerate(CASOS):
        estado, caminho = executar(construir_grafo(MemorySaver()), texto, decisoes, f"caso-{i}")
        print(f"{titulo}\n  caminho: {' -> '.join(caminho)}\n  status={estado['status']} versões={estado['tentativas']}\n")
