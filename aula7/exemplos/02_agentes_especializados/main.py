"""
ESQUELETO PARA IMPLEMENTAR AO VIVO (aula 7).
Implemente as etapas na ordem. Cada uma está marcada com um comentário e um
raise NotImplementedError: troque esse raise pelo código da etapa.
  ETAPA 1 -- Os três especialistas
  ETAPA 2 -- Encadear na mão
  ETAPA 3 -- A função executar: roda um agente
O texto abaixo descreve o exemplo pronto.

Exemplo 02 -- AGENTES ESPECIALIZADOS.

No exemplo 01 um agente fazia tudo. Agora dividimos por PAPÉIS:

    SOLICITAÇÃO -> INVESTIGADOR -> JURÍDICO -> ANALISTA

Cada especialista é um Agent(name=..., instructions=...) com UMA responsabilidade, uma entrada e uma saída bem definidas.

Atenção: especializar NÃO exige modelos diferentes. Os três usam o MESMO LLM.
O que os diferencia é:  instruções . responsabilidade . contexto de
entrada . critério de saída  (e, em sistemas reais, ferramentas -- veja o exemplo 05).

Repare no incômodo deste exemplo: quem leva o resultado de um especialista ao
próximo somos NÓS, à mão, passando strings de uma chamada para outra. Com três
especialistas é tolerável; com dez, vira bagunça. O exemplo 03 resolve isso com
um ESTADO COMPARTILHADO.

Rodar (LLM REAL: configure o .env; veja o README), a partir de aula7/:
    python exemplos\\02_agentes_especializados\\main.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, Runner

import prompts
from caso import DENUNCIA_045
from provedor import configurar

MODELO = configurar()  # LLM REAL: PROVEDOR no .env (openai ou ollama)

SOLICITACAO = DENUNCIA_045


def executar(agente: Agent, contexto: str) -> str:
    """Roda UM agente com a entrada `contexto` e devolve o texto que ele respondeu."""
    # ETAPA 3 -- corpo de executar:
    #   imprima "[NOME]" (agente.name em maiúsculas) e devolva Runner.run_sync(agente, contexto).final_output
    raise NotImplementedError("ETAPA 3: função executar")


# ETAPA 1 -- crie investigador, juridico e analista com Agent(name=..., instructions=...)
#   cada um com UMA responsabilidade (use prompts.REGRA no fim das instruções)
raise NotImplementedError("ETAPA 1: três especialistas")

if __name__ == "__main__":
    # ETAPA 2 -- bloco principal:
    #   chame executar(investigador, ...), depois executar(juridico, fatos), depois executar(analista, fatos + enquadramento)
    #   imprima cada resultado e a observação sobre as variáveis soltas
    raise NotImplementedError("ETAPA 2: bloco principal")
