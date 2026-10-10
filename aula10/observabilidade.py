"""
ETAPA 10 -- Observabilidade (15 min): onde o tempo foi gasto e quanto custou, por nó do grafo.

ESQUELETO:
  ETAPA 10.2 -- medido(): embrulha um nó, mede o tempo e grava uma linha em saidas/metricas.jsonl
  ETAPA 10.3 -- resumo(): nós percorridos, tempo total, nó mais lento e tokens totais de uma execução
  (ETAPA 10.1 fica em governanca.py: o hook do 🆕 B ganha um segundo papel, registrar)

Até você fazer a 10.2, medido() devolve o nó sem mudar nada: o grafo funciona igual.

REFERÊNCIAS NAS AULAS
  aula5/exemplos/11_observabilidade/agente_observavel.py        ler o que aconteceu numa execução (result.new_items)
  aula3/agente_hook2.py, aula3/agente_hook3.py                  RunHooks para enxergar o loop do agente
  aula8/exemplos/03_observabilidade/1_codigo_pronto/passo1_trace.py   trace e spans (o Langfuse do passo 2 é opcional)

Rodar:
    python observabilidade.py <thread_id>     # imprime o resumo de uma execução já feita
"""
import functools
import json
import sys
import time

from dados_rh import SAIDAS

ARQUIVO_METRICAS = SAIDAS / "metricas.jsonl"


def medido(nome: str, no):
    # ETAPA 10.2 -- devolva uma função que:
    #   1. mede o tempo de no(estado) com time.perf_counter();
    #   2. grava em ARQUIVO_METRICAS uma linha JSON com: thread_id (estado.get("thread_id")), no, segundos,
    #      e, se o nó devolveu, "tokens" e "fonte_feriados";
    #   3. devolve o MESMO dicionário que o nó devolveu.
    #   Use @functools.wraps(no) para o nome do nó continuar o mesmo.
    return no  # pass-through: troque pelo wrapper


def resumo(thread_id: str) -> dict:
    # ETAPA 10.3 -- leia ARQUIVO_METRICAS, filtre pelo thread_id e devolva
    #   {"nos": [...], "segundos_total": ..., "mais_lento": (no, segundos), "tokens_total": ...}
    raise NotImplementedError("ETAPA 10.3: resumo")


if __name__ == "__main__":
    print(json.dumps(resumo(sys.argv[1]), ensure_ascii=False, indent=2))
