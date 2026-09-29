"""
ModeloMock do exemplo 10 -- LLM de mentira, determinístico, sem internet e sem API Key.

Lê a linha "TAREFA: ..." do prompt. O comportamento foi desenhado para
exercitar o grafo inteiro:

  - classificar: texto longo -> "complexa"; curto -> "simples"
  - analisar   : na 1ª tentativa devolve uma análise INCOMPLETA (sem passos);
                 quando o prompt traz "Correção solicitada" (ciclo de revisão),
                 devolve a análise COMPLETA
  - validar    : reprova análise sem passos numerados ("ERRO: ...") e aprova a completa ("OK")
  - responder  : redige a resposta usando a análise, se houver
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from provedor import Modelo


class ModeloMock(Modelo):
    nome = "mock"

    def gerar(self, prompt: str) -> str:
        if "TAREFA: classificar" in prompt:
            solicitacao = prompt.split("Solicitação:", 1)[1]
            return "complexa" if len(solicitacao.split()) > 8 else "simples"

        if "TAREFA: analisar" in prompt:
            if "Correção solicitada" in prompt:
                return (
                    "Pedido de segunda via de documento. 1. Agendar o atendimento. "
                    "2. Levar documento com foto. 3. Pagar a taxa."
                )
            return "Trata-se de um pedido de segunda via de documento."

        if "TAREFA: validar" in prompt:
            analise = prompt.split("Análise:", 1)[1]
            if "3." in analise:
                return "OK"
            return "ERRO: a análise não traz passos numerados"

        if "TAREFA: responder" in prompt:
            if "Análise:" in prompt:
                return (
                    "Olá! Para solicitar a segunda via: agende o atendimento, leve um "
                    "documento com foto e pague a taxa. Posso ajudar em mais algo?"
                )
            return "Olá! O atendimento funciona de segunda a sexta, das 8h às 17h."

        return "Resposta simulada pelo modelo."
