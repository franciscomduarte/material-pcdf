"""
Exemplo 01 -- O AGENTE GENERALISTA.

Cenário da aula inteira: chega uma denúncia sobre uma contratação pública e o
sistema precisa produzir uma avaliação. Começamos como todo mundo começa: UM
agente, UM prompt, que faz tudo.

    receber -> investigar -> interpretar (jurídico) -> avaliar risco -> recomendar
                 \_______________ tudo dentro de UM agente ______________/

Rode e observe: funciona. O problema não está no resultado, está na ARQUITETURA:

  - um prompt gigante mistura quatro responsabilidades muito diferentes;
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

import prompts
from caso import DENUNCIA_045
from provedor import obter_modelo

modelo = obter_modelo()  # LLM REAL: PROVEDOR no .env (openai ou ollama)

SOLICITACAO = DENUNCIA_045  # os FATOS vêm na denúncia (veja caso.py): o LLM não pode inventá-los


def agente_generalista(solicitacao: str) -> str:
    """UM agente, UM prompt: investiga, interpreta, avalia risco e recomenda."""
    print("[AGENTE GENERALISTA] eu faço tudo...")
    return modelo.gerar(prompts.tudo(solicitacao))  # UM prompt com as quatro responsabilidades


if __name__ == "__main__":
    print(f"Modelo em uso: {modelo.nome}\n")
    print("Solicitação:", SOLICITACAO, "\n")
    resposta = agente_generalista(SOLICITACAO)
    print("\nResposta única:")
    print(resposta)
    print("\nOnde termina a investigação? Quem fez a análise jurídica? Não dá para saber.")
