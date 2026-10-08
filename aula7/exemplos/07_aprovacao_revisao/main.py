"""
Exemplo 07 -- APROVAÇÃO E REVISÃO: o exemplo que consolida a aula.

No exemplo 06 o humano só aprovava ou rejeitava, e rejeitar encerrava tudo.
Agora a REJEIÇÃO tem consequência: o humano diz o que está errado (feedback), o
Analista refaz a recomendação levando o feedback em conta, e o humano avalia de novo.

                             START
                               |
                          orquestrador
                               |
                          investigador
                               |
                            juridico
                               |
                 ┌──────> analista  (tentativas + 1; lê feedback_humano)
                 |             |
                 |      validacao_humana   <- interrupt(): PAUSA para o humano
                 |             |
                 |    ┌────────┼─────────────┐
                 |  aprova   rejeita     rejeita e
                 |    |     (restam      tentativas >= MAX_TENTATIVAS
                 |    |     tentativas)        |
              revisar |        |               |
                 └────┼────────┘               |
                      ↓                        ↓
                  finalizar          encerrar_sem_aprovacao
                      ↓                        ↓
                     END                      END

CONDIÇÃO DE PARADA: o ciclo analista -> humano -> revisar -> analista é limitado por
`tentativas` (lida do ESTADO), como na Aula 6. Nunca confie que o humano vai aprovar.

ERRO TÉCNICO x REJEIÇÃO HUMANA (não são a mesma coisa):
    Erro técnico : a API do jurídico caiu. É falha do SISTEMA. O estado até o último passo bem-
                   sucedido está no checkpoint; basta RETOMAR (invoke(None, config)). Não conta tentativa.
    Rejeição     : um humano avaliou o CONTEÚDO e pediu revisão. É decisão do PROCESSO, faz parte do fluxo,
                   tem feedback e conta como tentativa.

Rodar, a partir de aula7/ (LLM REAL: configure o .env; veja o README):
    python exemplos\\07_aprovacao_revisao\\solucao\\main.py                       # interativo: VOCÊ é o humano
    python exemplos\\07_aprovacao_revisao\\solucao\\main.py --auto sim            # aprova de primeira
    python exemplos\\07_aprovacao_revisao\\solucao\\main.py --auto nao,sim        # rejeita 1x, depois aprova
    python exemplos\\07_aprovacao_revisao\\solucao\\main.py --auto nao,nao,nao    # rejeita até o limite
    python exemplos\\07_aprovacao_revisao\\solucao\\main.py --falha-tecnica       # simula erro técnico e para
    python exemplos\\07_aprovacao_revisao\\solucao\\main.py --retomar --auto sim  # retoma depois do erro técnico
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

MAX_TENTATIVAS = 3
DB = Path(__file__).resolve().parent / "checkpoints.db"
CONFIG = {"configurable": {"thread_id": "denuncia-045"}}
SOLICITACAO = DENUNCIA_045
FEEDBACK_PADRAO = "Faltam ações numeradas, responsáveis e prazos."  # usado no modo --auto

FALHA_TECNICA = "--falha-tecnica" in sys.argv  # simula a API do jurídico fora do ar


class Estado(TypedDict):
    solicitacao: str
    investigacao: str
    analise_juridica: str
    analise_risco: str
    recomendacao: str
    aprovado: bool
    feedback_humano: str
    tentativas: int
    status: str  # "aprovada" | "limite_de_revisoes"


def orquestrador(estado: Estado) -> dict:
    print("[ORQUESTRADOR]")
    return {"investigacao": "", "analise_juridica": "", "analise_risco": "", "recomendacao": "",
            "aprovado": False, "feedback_humano": "", "tentativas": 0, "status": ""}


def investigador(estado: Estado) -> dict:
    print("[INVESTIGADOR]")
    return {"investigacao": Runner.run_sync(agentes.investigador, estado["solicitacao"]).final_output}


def juridico(estado: Estado) -> dict:
    if FALHA_TECNICA:
        print("[JURÍDICO]     ERRO TÉCNICO: serviço de base normativa indisponível")
        raise ConnectionError("serviço de base normativa indisponível")
    print("[JURÍDICO]")
    return {"analise_juridica": Runner.run_sync(agentes.juridico, estado["investigacao"]).final_output}


def analista(estado: Estado) -> dict:
    tentativa = estado["tentativas"] + 1
    print(f"[ANALISTA]     tentativa {tentativa}")
    fatos, enquadramento = estado["investigacao"], estado["analise_juridica"]
    risco = Runner.run_sync(agentes.risco, prompts.entrada_risco(fatos, enquadramento)).final_output
    # com feedback do revisor, o redator escreve a versão COMPLETA (ações numeradas, responsável e prazo)
    entrada = prompts.entrada_recomendar(fatos, enquadramento, risco, estado["feedback_humano"])
    recomendacao = Runner.run_sync(agentes.redator, entrada).final_output
    return {"analise_risco": risco, "recomendacao": recomendacao, "tentativas": tentativa}


def resumo_para_humano(estado: Estado) -> str:
    linha = "=" * 60
    return (
        f"{linha}\nANÁLISE PARA VALIDAÇÃO (versão {estado['tentativas']} de no máximo {MAX_TENTATIVAS})\n{linha}\n"
        f"Investigação    : {estado['investigacao']}\n"
        f"Análise jurídica: {estado['analise_juridica']}\n"
        f"Análise de risco: {estado['analise_risco']}\n"
        f"Recomendação    : {estado['recomendacao']}\n{linha}"
    )


def validacao_humana(estado: Estado) -> dict:
    print("[HUMANO]       aguardando validação...")
    # Este nó roda de novo na retomada; por isso só decide, sem efeito colateral antes do interrupt().
    resposta = interrupt({"resumo": resumo_para_humano(estado), "pergunta": "Aprovar análise? [sim/não]"})
    return {"aprovado": resposta["aprovado"], "feedback_humano": resposta.get("feedback", "")}


def revisar(estado: Estado) -> dict:
    print(f"[REVISÃO]      rejeitada. Feedback: {estado['feedback_humano']!r}. Voltando ao analista")
    return {}


def finalizar(estado: Estado) -> dict:
    print("[FINALIZAR]    análise APROVADA")
    return {"status": "aprovada"}


def encerrar_sem_aprovacao(estado: Estado) -> dict:
    print(f"[ENCERRAR]     limite de {MAX_TENTATIVAS} versões atingido sem aprovação: encaminhar a um responsável")
    return {"status": "limite_de_revisoes"}


def rotear_apos_humano(estado: Estado) -> str:
    if estado["aprovado"]:
        return "aprovada"
    if estado["tentativas"] >= MAX_TENTATIVAS:  # CONDIÇÃO DE PARADA, lida do estado
        return "desistir"
    return "revisar"


def construir(checkpointer):
    construtor = StateGraph(Estado)
    for nome, funcao in [
        ("orquestrador", orquestrador), ("investigador", investigador), ("juridico", juridico),
        ("analista", analista), ("validacao_humana", validacao_humana), ("revisar", revisar),
        ("finalizar", finalizar), ("encerrar_sem_aprovacao", encerrar_sem_aprovacao),
    ]:
        construtor.add_node(nome, funcao)
    construtor.add_edge(START, "orquestrador")
    construtor.add_edge("orquestrador", "investigador")
    construtor.add_edge("investigador", "juridico")
    construtor.add_edge("juridico", "analista")
    construtor.add_edge("analista", "validacao_humana")
    construtor.add_conditional_edges(
        "validacao_humana", rotear_apos_humano,
        {"aprovada": "finalizar", "revisar": "revisar", "desistir": "encerrar_sem_aprovacao"},
    )
    construtor.add_edge("revisar", "analista")  # o ciclo
    construtor.add_edge("finalizar", END)
    construtor.add_edge("encerrar_sem_aprovacao", END)
    return construtor.compile(checkpointer=checkpointer)


def humano_interativo(pausa: dict) -> dict:
    print("\n" + pausa["resumo"])
    aprovado = input(pausa["pergunta"] + " ").strip().lower() in ("sim", "s")
    feedback = "" if aprovado else input("O que precisa melhorar? ").strip()
    return {"aprovado": aprovado, "feedback": feedback}


def conduzir(app, entrada, decisoes: list[str] | None = None) -> dict:
    """Roda o grafo; a cada pausa pede a decisão do humano e retoma, até terminar.
    `entrada` é o estado inicial (execução nova) ou None (retomar um checkpoint).
    `decisoes` (opcional) substitui o input(): ex. ["nao", "sim"]."""
    resultado = app.invoke(entrada, CONFIG)
    while "__interrupt__" in resultado:
        pausa = resultado["__interrupt__"][0].value
        if decisoes is None:
            resposta = humano_interativo(pausa)
        else:
            aprovado = (decisoes.pop(0) if decisoes else "nao") == "sim"
            print("\n" + pausa["resumo"])
            print(f"(humano simulado) aprovado = {aprovado}")
            resposta = {"aprovado": aprovado, "feedback": "" if aprovado else FEEDBACK_PADRAO}
        resultado = app.invoke(Command(resume=resposta), CONFIG)  # retomada a partir do checkpoint
    return resultado


if __name__ == "__main__":
    print(f"Modelo em uso: {MODELO}\n")
    argumentos = sys.argv[1:]
    decisoes = None
    if "--auto" in argumentos:
        decisoes = argumentos[argumentos.index("--auto") + 1].split(",")
    retomando = "--retomar" in argumentos
    if not retomando:
        DB.unlink(missing_ok=True)

    with SqliteSaver.from_conn_string(str(DB)) as checkpointer:
        app = construir(checkpointer)
        entrada = None if retomando else {"solicitacao": SOLICITACAO, "investigacao": "", "analise_juridica": "",
                                          "analise_risco": "", "recomendacao": "", "aprovado": False,
                                          "feedback_humano": "", "tentativas": 0, "status": ""}
        if retomando and not app.get_state(CONFIG).next:
            raise SystemExit("Não há execução pendente para retomar.")
        try:
            conduzir(app, entrada, decisoes)
        except ConnectionError as erro:
            foto = app.get_state(CONFIG)
            print(f"\nERRO TÉCNICO ({erro}). Isto NÃO é uma rejeição humana.")
            print(f"O checkpoint guardou o que já foi feito; próximo nó pendente: {foto.next}")
            print("Retome quando o serviço voltar:")
            print("    python exemplos\\07_aprovacao_revisao\\solucao\\main.py --retomar --auto sim")
            raise SystemExit(1)

        final = app.get_state(CONFIG).values
        print(f"\nRESULTADO: status={final['status']} | versões geradas={final['tentativas']} | aprovado={final['aprovado']}")
        if final["status"] == "aprovada":
            print("Recomendação final:", final["recomendacao"])