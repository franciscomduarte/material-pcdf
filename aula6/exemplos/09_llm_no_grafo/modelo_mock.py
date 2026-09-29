"""
ModeloMock do exemplo 09 -- LLM de mentira, determinístico.

Não usa internet nem API Key. Ele lê a linha "TAREFA: ..." do prompt e devolve
uma resposta pronta e coerente. Serve para você ver o FLUXO do grafo sem
depender de nenhum provedor.
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
            return (
                "Trata-se de um pedido de segunda via de documento. "
                "1. Agendar o atendimento. 2. Levar documento com foto. 3. Pagar a taxa."
            )

        if "TAREFA: responder" in prompt:
            return (
                "Olá! Para solicitar a segunda via: agende o atendimento, leve um "
                "documento com foto e pague a taxa. Posso ajudar em mais algo?"
            )

        return "Resposta simulada pelo modelo."
