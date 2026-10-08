"""
ESQUELETO PARA IMPLEMENTAR AO VIVO (aula 7).
Implemente as etapas na ordem. Cada uma está marcada com um comentário e um
raise NotImplementedError: troque esse raise pelo código da etapa.
  ETAPA 1 -- Mostrar a resposta e a pergunta que importa
  ETAPA 2 -- O agente generalista: um Agent só
O texto abaixo descreve o exemplo pronto.

Exemplo 01 -- O AGENTE GENERALISTA.

Cenário da aula inteira: chega uma denúncia sobre uma contratação pública e o
sistema precisa produzir uma avaliação. Começamos como todo mundo começa: UM
agente, UMA instrução, que faz tudo.

    receber -> investigar -> interpretar (jurídico) -> avaliar risco -> recomendar
                 \_______________ tudo dentro de UM agente ______________/

O agente é o mesmo das Aulas 1 a 4:  Agent(name=..., instructions=...)  e roda com Runner.run_sync().

Rode e observe: funciona. O problema não está no resultado, está na ARQUITETURA:

  - uma instrução gigante mistura quatro responsabilidades muito diferentes;
  - não dá para ver (nem auditar) onde a investigação termina e o direito começa;
  - não dá para trocar, melhorar ou testar UMA das partes sem mexer nas outras;
  - não há onde inserir um humano: o agente entrega tudo ou nada.

Pergunta para a turma: e se investigação, análise jurídica e análise de risco
fossem responsabilidades tão diferentes que merecessem especialistas diferentes?
É o que fazemos no exemplo 02.

Rodar (LLM REAL: configure o .env; veja o README), a partir de aula7/:
    python exemplos\\01_agente_generalista\\main.py

Trocar de modelo SEM alterar este arquivo (PowerShell):
    $env:PROVEDOR = "openai"     # padrão; exige OPENAI_API_KEY (veja .env.example)
    $env:PROVEDOR = "ollama"     # local e grátis; exige `ollama serve` e o modelo baixado
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, Runner

import prompts
from caso import DENUNCIA_045
from provedor import configurar

configurar()  # LLM REAL: PROVEDOR no .env (openai ou ollama)

SOLICITACAO = DENUNCIA_045  # os FATOS vêm na denúncia (veja caso.py): o LLM não pode inventá-los


def agente_generalista(solicitacao: str) -> str:
    """UM agente, UMA instrução: investiga, interpreta, avalia risco e recomenda."""
    generalista = Agent(
        name="Agente Generalista",
        instructions=prompts.INSTR_TUDO
        ) 
    return Runner.run_sync(generalista, solicitacao)


if __name__ == "__main__":
    resposta = agente_generalista(    "Denúncia anônima sobre o Pregão 045/2026: o contrato, de R$ 2,8 milhões, teve o edital divulgado com apenas "
    "3 dias de antecedência da abertura das propostas. Houve um único proponente e um dos sócios da empresa "
    "vencedora é ex-servidor do órgão contratante.")
    print("\n\nRESPOSTA FINAL:\n", resposta.final_output)
