"""
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

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

import prompts
from caso import DENUNCIA_045
from provedor import obter_modelo

modelo = obter_modelo()  # LLM REAL: PROVEDOR no .env (openai ou ollama)

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
    return {"investigacao": modelo.gerar(prompts.investigar(estado["solicitacao"]))}


def juridico(estado: Estado) -> dict:
    print("[JURÍDICO]")
    return {"analise_juridica": modelo.gerar(prompts.juridico(estado["investigacao"]))}


def analista(estado: Estado) -> dict:
    print("[ANALISTA]")
    fatos, enquadramento = estado["investigacao"], estado["analise_juridica"]
    risco = modelo.gerar(prompts.risco(fatos, enquadramento))
    # A 1ª versão é um RASCUNHO curto (prompts.recomendar): um humano atento vai querer avaliá-la.
    recomendacao = modelo.gerar(prompts.recomendar(fatos, enquadramento, risco))
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
    print("[HUMANO]       aguardando validação...")
    # interrupt(): o grafo PARA aqui. O valor passado (o resumo) sai no retorno do invoke().
    # Quando alguém retomar com Command(resume=X), interrupt() devolve X e o nó segue.
    resposta = interrupt({"pergunta": "Aprovar análise? [sim/não]", "resumo": resumo_para_humano(estado)})
    return {"aprovado": str(resposta).strip().lower() in ("sim", "s")}


def finalizar(estado: Estado) -> dict:
    print("[FINALIZAR]    análise aprovada")
    return {}


def rejeitada(estado: Estado) -> dict:
    print("[REJEITADA]    o humano não aprovou (o exemplo 07 adiciona a REVISÃO)")
    return {}


def rotear_apos_humano(estado: Estado) -> str:
    return "sim" if estado["aprovado"] else "nao"


def construir(checkpointer):
    construtor = StateGraph(Estado)
    for nome, funcao in [
        ("orquestrador", orquestrador), ("investigador", investigador), ("juridico", juridico),
        ("analista", analista), ("validacao_humana", validacao_humana),
        ("finalizar", finalizar), ("rejeitada", rejeitada),
    ]:
        construtor.add_node(nome, funcao)
    construtor.add_edge(START, "orquestrador")
    construtor.add_edge("orquestrador", "investigador")
    construtor.add_edge("investigador", "juridico")
    construtor.add_edge("juridico", "analista")
    construtor.add_edge("analista", "validacao_humana")
    construtor.add_conditional_edges("validacao_humana", rotear_apos_humano, {"sim": "finalizar", "nao": "rejeitada"})
    construtor.add_edge("finalizar", END)
    construtor.add_edge("rejeitada", END)
    return construtor.compile(checkpointer=checkpointer)


def iniciar(app) -> None:
    print("== 1) EXECUÇÃO ATÉ A PAUSA ==")
    resultado = app.invoke({"solicitacao": SOLICITACAO, "investigacao": "", "analise_juridica": "",
                            "analise_risco": "", "recomendacao": "", "aprovado": False}, CONFIG)
    pausa = resultado["__interrupt__"][0].value  # o que o nó passou ao interrupt()
    print("\ninvoke() RETORNOU, mas a execução NÃO terminou. Está pausada; o estado está no SQLite.")
    print(f"próximo nó: {app.get_state(CONFIG).next}\n")
    print(pausa["resumo"])
    print(pausa["pergunta"])


def retomar(app, decisao: str) -> None:
    if not app.get_state(CONFIG).next:
        raise SystemExit("Não há execução pausada: rode primeiro `python main.py` (sem argumentos).")
    print(f"== 2) RETOMADA com a decisão humana: {decisao!r} ==")
    app.invoke(Command(resume=decisao), CONFIG)
    estado = app.get_state(CONFIG).values
    print(f"\naprovado = {estado['aprovado']}")


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
    print(f"Modelo em uso: {modelo.nome}\n")
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
