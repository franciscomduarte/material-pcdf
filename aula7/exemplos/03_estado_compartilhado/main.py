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
    solicitacao: str
    analise_juridica: str
    investigacao: str
    analise_risco: str
    recomendacao: str


def investigador(estado: Estado) -> dict:
    print("[INVESTIGADOR]")
    fatos = Runner.run_sync(agentes.investigador, estado["solicitacao"]).final_output
    return {"investigacao": fatos}


def juridico(estado: Estado) -> dict:
    print("[JURÍDICO]")
    texto = Runner.run_sync(agentes.juridico, estado["investigacao"]).final_output
    return {"analise_juridica": texto}


def analista(estado: Estado) -> dict:
    print("[ANALISTA]")
    analise = Runner.run_sync(agentes.risco, estado["analise_juridica"]).final_output
    return {"analise_risco": analise, "recomendacao": analise}


ESPECIALISTAS = [investigador, juridico, analista]

# MEMÓRIA: vive fora de qualquer execução (aqui, uma lista em memória do processo;
# em um sistema real seria um banco, arquivo ou serviço).
memoria: list[dict] = []


def executar(solicitacao: str) -> Estado:
    
    estado: Estado = {
        "solicitacao": solicitacao,
        "investigacao": "",
        "analise_juridica": "",
        "analise_risco": "",
        "recomendacao": "",
    }

    for especialista in ESPECIALISTAS:
        estado.update(especialista(estado))

    print("\n --- segunda execução: adicionando à MEMÓRIA ---")
    memoria.append({"solicitacao": solicitacao, "risco": estado["analise_risco"]})

    return estado


if __name__ == "__main__":
    print(f"Modelo em uso: {MODELO}\n")

    estado = executar(DENUNCIA_045)
    print("\nESTADO FINAL:")
    for campo, valor in estado.items():
        print(f"  {campo:17}: {valor}")

    print("\n--- segunda execução: o ESTADO recomeça vazio; a MEMÓRIA continua ---")
    executar(DENUNCIA_051)
    print("\nMEMÓRIA (histórico de análises):")
    for i, item in enumerate(memoria, start=1):
        print(f"  {i}. {item['solicitacao']} -> {item['risco']}")