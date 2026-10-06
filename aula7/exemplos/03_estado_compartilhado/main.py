"""
ESQUELETO PARA IMPLEMENTAR AO VIVO (aula 7).
Implemente as etapas na ordem. Cada uma está marcada com um comentário e um
raise NotImplementedError: troque esse raise pelo código da etapa.
  ETAPA 1 -- O Estado compartilhado
  ETAPA 2 -- O motor: três linhas
  ETAPA 3 -- Investigador e Jurídico: estado -> atualização
  ETAPA 4 -- Analista: lê dois campos, escreve dois
  ETAPA 5 -- Memória: o que sobrevive entre execuções
O texto abaixo descreve o exemplo pronto.

Exemplo 03 -- ESTADO COMPARTILHADO (e a diferença entre ESTADO e MEMÓRIA).

No exemplo 02 passávamos o resultado de um especialista para o outro na mão.
Agora existe UM dicionário tipado, o Estado, que todos leem e no qual cada um
escreve APENAS o que é sua responsabilidade (exatamente como na Aula 6):

                    ESTADO
                       |
                 INVESTIGADOR  -> escreve  investigacao
                       |
                   JURÍDICO    -> escreve  analise_juridica
                       |
                   ANALISTA    -> escreve  analise_risco, recomendacao
                       |
                 ESTADO FINAL

Cada especialista é uma função  estado -> atualização do estado, e por dentro roda um Agent
(os agentes já vêm prontos em agentes.py). Nenhum especialista chama outro; ninguém passa
strings "à mão". Ainda é Python puro: o "motor" que junta as atualizações são 3 linhas (veja executar()).

ESTADO x MEMÓRIA  (não são sinônimos)

    ESTADO   o que a execução ATUAL precisa: solicitacao, investigacao, ...
             nasce com a execução e é o "caderno de rascunho" dos especialistas.
    MEMÓRIA  o que sobrevive à execução e pode ser reaproveitado depois:
             histórico de análises, decisões anteriores, preferências.

Ao final deste exemplo rodamos DUAS solicitações: o estado é recriado do zero
a cada execução; a memória (uma lista) continua crescendo.

Rodar (LLM REAL: configure o .env; veja o README), a partir de aula7/:
    python exemplos\\03_estado_compartilhado\\main.py
"""
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Runner

import agentes
import prompts
from caso import DENUNCIA_045, DENUNCIA_051
from provedor import configurar

MODELO = configurar()  # LLM REAL: PROVEDOR no .env (openai ou ollama)


class Estado(TypedDict):
    # ETAPA 1 -- declare os campos de Estado (todos str):
    #   solicitacao, investigacao, analise_juridica, analise_risco, recomendacao
    raise NotImplementedError("ETAPA 1: campos do Estado")


def investigador(estado: Estado) -> dict:
    # ETAPA 3 -- investigador: imprima o log, gere os fatos com Runner.run_sync(agentes.investigador, ...).final_output
    #   e devolva {"investigacao": ...}
    #   juridico: rode agentes.juridico com estado["investigacao"] e devolva {"analise_juridica": ...}
    raise NotImplementedError("ETAPA 3: investigador e juridico (investigador)")


def juridico(estado: Estado) -> dict:
    # ETAPA 3 -- investigador: imprima o log, gere os fatos com Runner.run_sync(agentes.investigador, ...).final_output
    #   e devolva {"investigacao": ...}
    #   juridico: rode agentes.juridico com estado["investigacao"] e devolva {"analise_juridica": ...}
    raise NotImplementedError("ETAPA 3: investigador e juridico (juridico)")


def analista(estado: Estado) -> dict:
    # ETAPA 4 -- analista: leia investigacao e analise_juridica, gere o risco (agentes.risco, entrada prompts.entrada_risco)
    #   e a recomendacao (agentes.redator, entrada prompts.entrada_recomendar)
    #   devolva {"analise_risco": ..., "recomendacao": ...}
    raise NotImplementedError("ETAPA 4: analista")


ESPECIALISTAS = [investigador, juridico, analista]

# MEMÓRIA: vive fora de qualquer execução (aqui, uma lista em memória do processo;
# em um sistema real seria um banco, arquivo ou serviço).
memoria: list[dict] = []


def executar(solicitacao: str) -> Estado:
    # ETAPA 2 -- em executar: crie o estado inicial (todos os campos, os demais "")
    #   para cada especialista em ESPECIALISTAS, faça estado.update(especialista(estado))
    raise NotImplementedError("ETAPA 2: motor de executar")
    # ETAPA 5 -- guarde na MEMÓRIA: memoria.append({"solicitacao": ..., "risco": ...})
    return estado


if __name__ == "__main__":
    print(f"Modelo em uso: {MODELO}\n")

    estado = executar(DENUNCIA_045)
    print("\nESTADO FINAL:")
    for campo, valor in estado.items():
        print(f"  {campo:17}: {valor}")

    # ETAPA 5 -- rode a segunda denúncia (DENUNCIA_051) e imprima a MEMÓRIA (histórico de análises)
