"""
ModeloMock do desafio -- LLM de mentira, determinístico, sem internet e sem API Key.

Lê a linha "TAREFA: ..." do prompt (mesmo padrão dos exemplos 09 e 10):

  - classificar_urgencia: devolve "urgente" se a solicitação tem sinal de urgência
                          (agora, urgente, passando mal, risco, emergência...); senão "normal"
  - analisar            : 1ª tentativa INCOMPLETA (sem passos); com "Correção solicitada"
                          no prompt, devolve a análise COMPLETA (3 passos numerados)
  - validar             : aprova ("OK") só análise com o passo "3."; senão "ERRO: ..."
  - responder           : redige conforme o que o prompt traz (encaminhamento, análise
                          ou aviso de que não há informação na base)

ModeloMock(sempre_reprova=True) faz o validador reprovar SEMPRE: serve para
testar a condição de parada do ciclo (Caso 4).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from provedor import Modelo

SINAIS_URGENCIA = ("urgente", "urgência", "agora", "passando mal", "risco", "emergência", "imediat")


class ModeloMock(Modelo):
    nome = "mock"

    def __init__(self, sempre_reprova: bool = False):
        self.sempre_reprova = sempre_reprova

    def gerar(self, prompt: str) -> str:
        if "TAREFA: classificar_urgencia" in prompt:
            solicitacao = prompt.split("Solicitação:", 1)[1].lower()
            return "urgente" if any(s in solicitacao for s in SINAIS_URGENCIA) else "normal"

        if "TAREFA: analisar" in prompt:
            if "Correção solicitada" in prompt:
                return (
                    "Pedido de segunda via de documento. 1. Agendar o atendimento. "
                    "2. Levar documento com foto. 3. Pagar a taxa."
                )
            return "Trata-se de um pedido de segunda via de documento."

        if "TAREFA: validar" in prompt:
            analise = prompt.split("Análise:", 1)[1]
            if not self.sempre_reprova and "3." in analise:
                return "OK"
            return "ERRO: a análise não traz passos numerados"

        if "TAREFA: responder" in prompt:
            if "Encaminhamento:" in prompt:
                return (
                    "Sua solicitação foi marcada como URGENTE e encaminhada ao plantão 24h. "
                    "Aguarde o contato da equipe."
                )
            if "SEM_BASE" in prompt:
                return (
                    "Não encontrei essa informação na base de atendimento, então não vou "
                    "arriscar uma resposta. Sua dúvida foi encaminhada a um atendente."
                )
            if "não validada" in prompt:
                return (
                    "Segue a orientação, mas atenção: ela não passou pela validação. "
                    "Confirme com um atendente antes de agir."
                )
            return (
                "Olá! Para solicitar a segunda via: agende o atendimento, leve um "
                "documento com foto e pague a taxa. Posso ajudar em mais algo?"
            )

        return "Resposta simulada pelo modelo."
