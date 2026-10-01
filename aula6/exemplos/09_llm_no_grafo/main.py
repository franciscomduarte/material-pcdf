"""
Exemplo 09 -- LLM COMO NÓ.

No exemplo 08 dominamos o controle de fluxo (decisão, ciclo, parada), mas os
nós eram funções "de mentira". Agora colocamos um LLM DENTRO de nós:

    START -> receber -> classificar(LLM) -> analisar(LLM) -> responder(LLM) -> END

O que importa neste exemplo NÃO é o grafo (é linear de propósito). É isto:

                 ┌──────────────┐
                 │     LLM      │   <- o nó chama modelo.gerar(prompt)
                 └──────┬───────┘
                        ↓
                    resultado      <- texto devolvido
                        ↓
                    próximo nó     <- o texto vira campo do ESTADO

O grafo só conhece a abstração `Modelo` (método gerar). Quem é o modelo --
Mock, OpenAI, Ollama ou Claude -- é decidido pela variável PROVEDOR, lida em
provedor.py (mesmo padrão da Aula 5). NENHUMA chamada a SDK aparece no grafo.

Rodar (LLM REAL por padrão: OpenAI, como nas Aulas 4 e 5; Ollama com PROVEDOR=ollama):
    python main.py

Trocar de modelo SEM alterar este arquivo (PowerShell):
    $env:PROVEDOR = "ollama"     # ou "openai" / "claude" (veja ../../.env.example)
    $env:PROVEDOR = "mock"       # LLM de mentira: sem chave e sem internet (mostra o ciclo de revisão sempre)

Sem OPENAI_API_KEY (ou com o Ollama fora do ar), o exemplo AVISA e roda com o Mock.
    python main.py
"""
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from langgraph.graph import END, START, StateGraph

from modelo_mock import ModeloMock
from provedor import obter_modelo

# Único ponto do arquivo que sabe qual modelo está em uso.
modelo = obter_modelo(ModeloMock(), padrao="openai")  # LLM real por padrão; sem chave, cai no Mock com aviso


class Estado(TypedDict):
    solicitacao: str
    categoria: str
    analise: str
    resposta: str


def receber(estado: Estado) -> dict:
    print("[receber]")
    return {"solicitacao": estado["solicitacao"].strip()}


def classificar(estado: Estado) -> dict:
    print("[classificar] chamando o LLM...")
    prompt = (
        "TAREFA: classificar\n"
        "Classifique a solicitação como 'simples' ou 'complexa'.\n"
        "- simples: pergunta objetiva com resposta de uma frase "
        "(ex.: 'Qual o horário de atendimento?', 'Qual o endereço?').\n"
        "- complexa: pede procedimento com vários passos, prazos ou documentos "
        "(ex.: 'Como abrir uma empresa?', 'Quais documentos preciso para o passaporte?').\n"
        "Responda com UMA palavra: simples ou complexa.\n"
        f"Solicitação: {estado['solicitacao']}"
    )
    texto = modelo.gerar(prompt)
    # o LLM devolve texto livre: normalizamos para um valor que o grafo entende
    categoria = "complexa" if "complexa" in texto.lower() else "simples"
    return {"categoria": categoria}


def analisar(estado: Estado) -> dict:
    print("[analisar] chamando o LLM...")
    prompt = (
        "TAREFA: analisar\n"
        "Analise a solicitação e indique os passos numerados (1., 2., 3.) para atendê-la.\n"
        f"Solicitação: {estado['solicitacao']}"
    )
    return {"analise": modelo.gerar(prompt)}


def responder(estado: Estado) -> dict:
    print("[responder] chamando o LLM...")
    prompt = (
        "TAREFA: responder\n"
        "Escreva uma resposta curta e cordial ao usuário, com base na análise.\n"
        f"Solicitação: {estado['solicitacao']}\n"
        f"Análise: {estado['analise']}"
    )
    return {"resposta": modelo.gerar(prompt)}


construtor = StateGraph(Estado)
construtor.add_node("receber", receber)
construtor.add_node("classificar", classificar)
construtor.add_node("analisar", analisar)
construtor.add_node("responder", responder)

construtor.add_edge(START, "receber")
construtor.add_edge("receber", "classificar")
construtor.add_edge("classificar", "analisar")
construtor.add_edge("analisar", "responder")
construtor.add_edge("responder", END)

app = construtor.compile()

print(f"Modelo em uso: {modelo.nome}\n")

resultado = app.invoke(
    {"solicitacao": "Preciso saber quais são os procedimentos para solicitar uma segunda via de um documento."}
)

print("\nCategoria:", resultado["categoria"])
print("Análise  :", resultado["analise"])
print("Resposta :", resultado["resposta"])

# ---------------------------------------------------------------------------
# Repare no que NÃO mudou entre Mock, Ollama, OpenAI e Claude: o grafo, os nós
# e o estado. Só o objeto `modelo`. LangGraph controla o FLUXO; o LLM é apenas
# uma capacidade chamada dentro de um nó -- como uma tool ou um MCP seria.
# ---------------------------------------------------------------------------
