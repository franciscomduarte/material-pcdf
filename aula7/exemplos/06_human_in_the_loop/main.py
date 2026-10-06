"""
ESQUELETO PARA IMPLEMENTAR AO VIVO (aula 7).
Implemente as etapas na ordem. Cada uma está marcada com um comentário e um
raise NotImplementedError: troque esse raise pelo código da etapa.
  ETAPA 1 -- Ligar o grafo com o humano no meio
  ETAPA 2 -- Iniciar e ler a pausa
  ETAPA 3 -- validacao_humana: o interrupt()
  ETAPA 4 -- Retomar com Command(resume=...)
  ETAPA 5 -- O roteador depois do humano
O texto abaixo descreve o exemplo pronto.

Exemplo 06 -- HUMAN-IN-THE-LOOP: interromper, pedir decisão humana, retomar.

No exemplo 05 a equipe rodava do começo ao fim, sem ninguém olhar o resultado.
Agora inserimos um HUMANO num ponto crítico: antes de a recomendação valer,
uma pessoa aprova ou rejeita.

    START -> orquestrador -> investigador -> juridico -> analista
                                                            |
                                                   validacao_humana   <- interrupt(): PAUSA aqui
                                                     /          \\
                                                  sim            não
                                                   |              |
                                               finalizar       rejeitada -> END

PARTE A (--simples): a versão ingênua, com input(). Funciona na demonstração, mas:
  - o estado só existe na memória do processo (fechou o terminal, perdeu tudo);
  - o programa fica BLOQUEADO esperando digitar (e se o humano só responder amanhã?);
  - não há identificação da execução nem como retomá-la depois, de forma robusta.

PARTE B (padrão): o mecanismo real do LangGraph, com 3 ingredientes:
  1. checkpointer  -> o estado de cada passo é salvo (SQLite);
  2. interrupt()   -> pausa DENTRO do nó e devolve ao chamador a pergunta ao humano;
  3. Command(resume=...) -> retoma do checkpoint, entregando a resposta ao interrupt().

    invoke() -> executa -> interrupt() -> checkpoint salvo -> invoke() RETORNA (com "__interrupt__")
    ...horas depois, até em outro processo...
    invoke(Command(resume="sim"), config) -> carrega o checkpoint -> continua

  ATENÇÃO: ao retomar, o nó que chamou interrupt() roda DE NOVO desde o início
  (por isso o nó de validação só decide; nada com efeito colateral vem antes do interrupt()).

BREAKPOINT: `interrupt_before=["no"]` (exemplo 04) é o breakpoint ESTÁTICO: para antes de um
nó, sempre. `interrupt()` é o DINÂMICO: para dentro do nó, com uma pergunta e uma resposta.

Rodar, a partir de aula7/ (LLM REAL: configure o .env; veja o README):
    python exemplos\\06_human_in_the_loop\\main.py --simples        # parte A (input)
    python exemplos\\06_human_in_the_loop\\main.py                  # parte B: roda até pausar e ENCERRA
    python exemplos\\06_human_in_the_loop\\main.py --retomar sim    # outro processo: retoma com a decisão
    python exemplos\\06_human_in_the_loop\\main.py --auto sim       # pausa e retoma no mesmo processo
"""
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Runner
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

import agentes
import prompts
from caso import DENUNCIA_045
from provedor import configurar

MODELO = configurar()  # LLM REAL: PROVEDOR no .env (openai ou ollama)

DB = Path(__file__).resolve().parent / "checkpoints.db"
CONFIG = {"configurable": {"thread_id": "denuncia-045"}}
SOLICITACAO = DENUNCIA_045


class Estado(TypedDict):
    solicitacao: str
    investigacao: str
    analise_juridica: str
    analise_risco: str
    recomendacao: str
    aprovado: bool


def orquestrador(estado: Estado) -> dict:
    print("[ORQUESTRADOR]")
    return {"investigacao": "", "analise_juridica": "", "analise_risco": "", "recomendacao": "", "aprovado": False}


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
    # A 1ª versão é um RASCUNHO curto (agentes.redator): um humano atento vai querer avaliá-la.
    recomendacao = Runner.run_sync(agentes.redator, prompts.entrada_recomendar(fatos, enquadramento, risco)).final_output
    return {"analise_risco": risco, "recomendacao": recomendacao}


def resumo_para_humano(estado: Estado) -> str:
    linha = "=" * 60
    return (
        f"{linha}\nANÁLISE PARA VALIDAÇÃO\n{linha}\n"
        f"Investigação    : {estado['investigacao']}\n"
        f"Análise jurídica: {estado['analise_juridica']}\n"
        f"Análise de risco: {estado['analise_risco']}\n"
        f"Recomendação    : {estado['recomendacao']}\n{linha}"
    )


def validacao_humana(estado: Estado) -> dict:
    # ETAPA 3 -- em validacao_humana: imprima "[HUMANO] aguardando validação..."
    #   resposta = interrupt({"pergunta": ..., "resumo": resumo_para_humano(estado)})
    #   devolva {"aprovado": ...} (True se a resposta for sim ou s)
    raise NotImplementedError("ETAPA 3: validacao_humana")


def finalizar(estado: Estado) -> dict:
    print("[FINALIZAR]    análise aprovada")
    return {}


def rejeitada(estado: Estado) -> dict:
    print("[REJEITADA]    o humano não aprovou (o exemplo 07 adiciona a REVISÃO)")
    return {}


def rotear_apos_humano(estado: Estado) -> str:
    # ETAPA 5 -- em rotear_apos_humano: devolva "sim" se estado["aprovado"], senão "nao"
    raise NotImplementedError("ETAPA 5: rotear_apos_humano")


def construir(checkpointer):
    # ETAPA 1 -- em construir(checkpointer): StateGraph(Estado) com os 7 nós
    #   arestas: START -> orquestrador -> investigador -> juridico -> analista -> validacao_humana
    #   add_conditional_edges("validacao_humana", rotear_apos_humano, {"sim": "finalizar", "nao": "rejeitada"})
    #   finalizar e rejeitada -> END; compile(checkpointer=checkpointer)
    raise NotImplementedError("ETAPA 1: construir")


def iniciar(app) -> None:
    # ETAPA 2 -- em iniciar: invoke com o estado inicial e CONFIG
    #   pausa = resultado["__interrupt__"][0].value
    #   imprima o próximo nó (app.get_state(CONFIG).next), o resumo e a pergunta
    raise NotImplementedError("ETAPA 2: iniciar")


def retomar(app, decisao: str) -> None:
    # ETAPA 4 -- em retomar: se não houver get_state(CONFIG).next, encerre com a mensagem
    #   app.invoke(Command(resume=decisao), CONFIG)
    #   imprima aprovado = ... lido de app.get_state(CONFIG).values
    raise NotImplementedError("ETAPA 4: retomar")


def parte_a_simples() -> None:
    """A versão ingênua: tudo em memória, bloqueando em input()."""
    print("== PARTE A: input() ==\n")
    estado = {"solicitacao": SOLICITACAO}
    estado.update(investigador(estado))
    estado.update(juridico(estado))
    estado.update(analista(estado))
    print(resumo_para_humano(estado))
    resposta = input("Aprovar análise? [sim/não] ")
    print("Aprovada." if resposta.strip().lower() in ("sim", "s") else "Rejeitada.")
    print("\nSe você fechar o terminal antes de responder, perde a execução. Sem id, sem retomada.")


if __name__ == "__main__":
    print(f"Modelo em uso: {MODELO}\n")
    argumentos = sys.argv[1:]
    if "--simples" in argumentos:
        parte_a_simples()
        raise SystemExit
    if "--retomar" not in argumentos:
        DB.unlink(missing_ok=True)

    with SqliteSaver.from_conn_string(str(DB)) as checkpointer:
        app = construir(checkpointer)
        if "--retomar" in argumentos:
            retomar(app, argumentos[argumentos.index("--retomar") + 1])
        else:
            iniciar(app)
            if "--auto" in argumentos:
                print()
                retomar(app, argumentos[argumentos.index("--auto") + 1])
            else:
                print("\nO processo vai terminar agora. O humano decide DEPOIS, em outro processo:")
                print("    python exemplos\\06_human_in_the_loop\\main.py --retomar sim")
