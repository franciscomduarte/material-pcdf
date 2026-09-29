"""
DESAFIO -- Análise de solicitação de atendimento, como grafo.  (esqueleto)

Leia o enunciado em README.md. Aqui está o que já vem pronto e o que é seu.

JÁ PRONTO:  Estado, base de conhecimento, as duas TOOLS (pesquisar e encaminhar),
            os roteadores-modelo e a função executar() (devolve o caminho percorrido).
SEU:        os NÓS e a MONTAGEM DO GRAFO dentro de construir_grafo().

Como conferir seu trabalho (na pasta aula6/):
    python desafio\\main.py                     # roda os 4 casos e mostra o caminho
    python -m unittest desafio.test_desafio -v  # os mesmos 4 casos, com o caminho esperado

Trocar o modelo sem alterar o grafo:  $env:PROVEDOR = "ollama"   (ou openai / claude)
"""
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # provedor.py
sys.path.insert(0, str(Path(__file__).resolve().parent))      # modelo_mock.py

from langgraph.graph import END, START, StateGraph  # noqa: F401  (você vai usar)

from modelo_mock import ModeloMock
from provedor import obter_modelo

MAX_TENTATIVAS = 3


class Estado(TypedDict):
    solicitacao: str      # entrada
    urgencia: str         # classificar_urgencia: "urgente" | "normal"
    informacao: str       # pesquisar: texto da base ("" se não achou)
    encaminhamento: str   # encaminhar: confirmação do plantão (só no caminho urgente)
    analise: str          # analisar
    valida: bool          # validar
    tentativas: int       # analisar (condição de parada do ciclo)
    feedback: str         # validar -> revisar -> analisar
    resposta: str         # responder


# ---------------------------------------------------------------- ferramentas
BASE_CONHECIMENTO = {
    "segunda via": "Agendar atendimento; levar documento com foto; pagar a taxa de emissão.",
    "passaporte": "Preencher o formulário online; agendar a Polícia Federal; pagar a GRU.",
    "horário": "Atendimento de segunda a sexta, das 8h às 17h.",
}


def buscar_procedimentos(solicitacao: str) -> str:
    """TOOL comum (nenhuma IA aqui). Devolve '' quando o assunto NÃO está na base."""
    for assunto, texto in BASE_CONHECIMENTO.items():
        if assunto in solicitacao.lower():
            return texto
    return ""


def encaminhar_plantao(solicitacao: str) -> str:
    """TOOL comum: simula o envio de um caso urgente ao plantão."""
    return "Caso encaminhado ao plantão 24h (prioridade máxima)."


# ------------------------------------------------------------------ o grafo
def construir_grafo(modelo):
    """Monte e devolva o grafo COMPILADO. Recebe o `modelo` (abstração Modelo: modelo.gerar(prompt)).

    Nós que você precisa escrever (o que cada um LÊ e ESCREVE está no README):
        receber, classificar_urgencia (LLM), encaminhar (tool), pesquisar (tool),
        analisar (LLM), validar (LLM), revisar, responder (LLM)

    Roteadores (funções que só LEEM o estado e devolvem um rótulo):
        rotear_apos_classificar -> "urgente" | "normal"
        rotear_apos_pesquisar   -> "com_base" | "sem_base"
        rotear_apos_validar     -> "ok" | "erro" | "desistir"

    Dica: comece pelo caminho URGENTE (o mais curto), rode, e vá crescendo o grafo.
    Dica: os prompts do LLM começam com uma linha "TAREFA: <nome>" (o Mock lê essa linha).
          Veja os exemplos 09 e 10 e o modelo_mock.py.
    """
    # TODO 1: defina os nós (funções estado -> dict com SÓ o que o nó atualiza)
    # TODO 2: defina os roteadores
    # TODO 3: StateGraph(Estado), add_node, add_edge, add_conditional_edges
    # TODO 4: return construtor.compile()
    raise NotImplementedError("Implemente construir_grafo() -- veja o README do desafio.")


# ------------------------------------------------------------------ execução
def executar(app, solicitacao: str):
    """Roda o grafo e devolve (estado_final, caminho). O caminho vem do stream de atualizações."""
    estado: dict = {"solicitacao": solicitacao}
    caminho = []
    for passo in app.stream(estado, stream_mode="updates"):
        for no, atualizacao in passo.items():
            caminho.append(no)
            estado.update(atualizacao)
    return estado, caminho


CASOS = [
    "Estou sem medicação e passando mal, preciso de atendimento agora",
    "Preciso saber como solicitar uma segunda via de um documento",
    "Qual o prazo de restituição do imposto de renda de 2031?",
]

if __name__ == "__main__":
    modelo = obter_modelo(ModeloMock())
    print(f"Modelo em uso: {modelo.nome}\n")
    app = construir_grafo(modelo)
    for texto in CASOS:
        estado, caminho = executar(app, texto)
        print("=" * 70)
        print("Solicitação:", texto)
        print("Caminho    :", " -> ".join(caminho))
        print("Urgência   :", estado.get("urgencia"), "| tentativas:", estado.get("tentativas"),
              "| validada:", estado.get("valida"))
        print("Resposta   :", estado.get("resposta"), "\n")
