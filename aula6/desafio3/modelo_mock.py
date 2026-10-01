"""
ModeloMock do desafio 3 -- o LLM de mentira dos TESTES (determinístico, sem internet e sem API Key).

Neste desafio o LLM só escreve a resposta final (nó `responder`). Quem DECIDE o caminho é o JEV.
O Mock lê a linha "TAREFA: responder" do prompt e responde conforme o que o prompt traz:
  - "Encaminhamento:"  -> avisa que o caso foi ao plantão
  - "SEM_BASE"         -> admite que não encontrou a informação (sem inventar)
  - "Informação:"      -> orienta com o procedimento da base
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from provedor import Modelo


class ModeloMock(Modelo):
    nome = "mock"

    def gerar(self, prompt: str) -> str:
        if "TAREFA: responder" in prompt:
            if "Encaminhamento:" in prompt:
                return "Sua solicitação foi marcada como URGENTE e encaminhada ao plantão 24h. Aguarde o contato da equipe."
            if "SEM_BASE" in prompt:
                return ("Não encontrei essa informação na base de atendimento, então não vou arriscar uma resposta. "
                        "Sua dúvida foi encaminhada a um atendente.")
            procedimento = prompt.split("Informação:", 1)[1].strip().splitlines()[0] if "Informação:" in prompt else ""
            return f"Olá! Segue a orientação: {procedimento} Posso ajudar em mais algo?"
        return "Resposta simulada pelo modelo."
