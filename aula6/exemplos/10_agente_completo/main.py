"""
Exemplo 10 -- O AGENTE COMPLETO, COMO GRAFO DE EXECUÇÃO.

Junta tudo o que construímos:
  ex 03  estado compartilhado (TypedDict)          ex 06  decisão (conditional edges)
  ex 05  nós devolvem só a atualização             ex 08  ciclo + condição de parada
  ex 09  LLM dentro do nó, atrás da abstração Modelo

START
  ↓
receber
  ↓
classificar (LLM)
  ↓
 ┌───────────────┐
 ↓               ↓
simples       complexa
 ↓               ↓
responder     pesquisar (tool)
                 ↓
              analisar (LLM)  <──────────┐
                 ↓                       │
              validar (LLM)              │
             /      \                    │
           OK        ERRO                │
           ↓           ↓                 │
       responder    revisar ─────────────┘
                    (para após MAX_TENTATIVAS)

Um agente complexo = um sistema de ESTADOS que percorre um GRAFO de execução.
Quem "pensa" são os LLMs dos nós; quem controla a ORDEM é o grafo.
'pesquisar' é uma TOOL (função comum): mostra que no grafo cabem LLM, tools
e -- num sistema real -- chamadas MCP ou A2A, todos como nós.

Rodar (Mock, padrão -- sem API Key):
    python main.py
    python main.py "Qual o horário de atendimento?"        # caminho simples

Trocar de modelo SEM alterar este arquivo (PowerShell):
    $env:PROVEDOR = "ollama"    # ou "openai" / "claude" (veja ../../.env.example)
"""
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from langgraph.graph import END, START, StateGraph

from modelo_mock import ModeloMock
from provedor import obter_modelo

modelo = obter_modelo(ModeloMock())  # o grafo só conhece a abstração Modelo

MAX_TENTATIVAS = 3


class Estado(TypedDict):
    solicitacao: str
    categoria: str
    informacao: str
    analise: str
    resposta: str
    valida: bool
    tentativas: int
    feedback: str  # motivo da reprovação, lido por 'analisar' na volta do ciclo


# ---------------------------------------------------------------- ferramenta
BASE_CONHECIMENTO = {
    "segunda via": "Agendar atendimento; levar documento com foto; pagar a taxa de emissão.",
}


def buscar_procedimentos(solicitacao: str) -> str:
    """Uma TOOL comum: nenhuma IA aqui. No mundo real seria uma API ou um MCP Server."""
    for assunto, texto in BASE_CONHECIMENTO.items():
        if assunto in solicitacao.lower():
            return texto
    return "Nenhuma informação encontrada na base."


# --------------------------------------------------------------------- nós
def receber(estado: Estado) -> dict:
    print("[receber]")
    # Inicializa TODOS os campos: o caminho "simples" nunca passa por pesquisar/analisar,
    # e 'responder' lê 'analise'. Campo não escrito = KeyError (lembra do exemplo 05?).
    return {
        "solicitacao": estado["solicitacao"].strip(),
        "categoria": "",
        "informacao": "",
        "analise": "",
        "resposta": "",
        "valida": False,
        "tentativas": 0,
        "feedback": "",
    }


def classificar(estado: Estado) -> dict:
    print("[classificar]")
    texto = modelo.gerar(
        "TAREFA: classificar\n"
        "Classifique a solicitação como 'simples' ou 'complexa'.\n"
        "- simples: pergunta objetiva com resposta de uma frase "
        "(ex.: 'Qual o horário de atendimento?', 'Qual o endereço?').\n"
        "- complexa: pede procedimento com vários passos, prazos ou documentos "
        "(ex.: 'Como abrir uma empresa?', 'Quais documentos preciso para o passaporte?').\n"
        "Responda com UMA palavra: simples ou complexa.\n"
        f"Solicitação: {estado['solicitacao']}"
    )
    categoria = "complexa" if "complexa" in texto.lower() else "simples"
    print(f"            categoria = {categoria}")
    return {"categoria": categoria}


def pesquisar(estado: Estado) -> dict:
    print("[pesquisar]")
    return {"informacao": buscar_procedimentos(estado["solicitacao"])}


def analisar(estado: Estado) -> dict:
    tentativa = estado["tentativas"] + 1
    print(f"[analisar]  tentativa {tentativa}")
    correcao = f"Correção solicitada: {estado['feedback']}\n" if estado["feedback"] else ""
    analise = modelo.gerar(
        "TAREFA: analisar\n"
        "Analise a solicitação usando as informações pesquisadas e indique os passos "
        "numerados (1., 2., 3.) para atendê-la.\n"
        f"{correcao}"
        f"Solicitação: {estado['solicitacao']}\n"
        f"Informações: {estado['informacao']}"
    )
    return {"analise": analise, "tentativas": tentativa}


def validar(estado: Estado) -> dict:
    texto = modelo.gerar(
        "TAREFA: validar\n"
        "A análise é válida se trouxer pelo menos três passos numerados e concretos. "
        "Responda apenas 'OK' ou 'ERRO: <motivo>'.\n"
        f"Análise: {estado['analise']}"
    )
    ok = texto.strip().upper().startswith("OK")
    print(f"[validar]   {'OK' if ok else texto.strip()}")
    return {"valida": ok, "feedback": "" if ok else texto.strip()}


def revisar(estado: Estado) -> dict:
    print("[revisar]   voltando para analisar com o feedback")
    return {"feedback": f"corrija — {estado['feedback']}"}


def responder(estado: Estado) -> dict:
    print("[responder]")
    contexto = f"Análise: {estado['analise']}\n" if estado["analise"] else ""
    aviso = "" if estado["valida"] or not estado["analise"] else "(análise não validada; avise o usuário)\n"
    resposta = modelo.gerar(
        "TAREFA: responder\n"
        "Escreva uma resposta curta e cordial ao usuário.\n"
        f"{aviso}"
        f"Solicitação: {estado['solicitacao']}\n"
        f"{contexto}"
    )
    return {"resposta": resposta}


# ------------------------------------------------------------- roteadores
def rotear_apos_classificar(estado: Estado) -> str:
    return estado["categoria"]  # "simples" ou "complexa"


def rotear_apos_validar(estado: Estado) -> str:
    if estado["valida"]:
        return "ok"
    if estado["tentativas"] >= MAX_TENTATIVAS:
        return "desistir"  # CONDIÇÃO DE PARADA do ciclo
    return "erro"


# ------------------------------------------------------------------- grafo
construtor = StateGraph(Estado)
for nome, funcao in [
    ("receber", receber),
    ("classificar", classificar),
    ("pesquisar", pesquisar),
    ("analisar", analisar),
    ("validar", validar),
    ("revisar", revisar),
    ("responder", responder),
]:
    construtor.add_node(nome, funcao)

construtor.add_edge(START, "receber")
construtor.add_edge("receber", "classificar")
construtor.add_conditional_edges(
    "classificar", rotear_apos_classificar, {"simples": "responder", "complexa": "pesquisar"}
)
construtor.add_edge("pesquisar", "analisar")
construtor.add_edge("analisar", "validar")
construtor.add_conditional_edges(
    "validar", rotear_apos_validar, {"ok": "responder", "desistir": "responder", "erro": "revisar"}
)
construtor.add_edge("revisar", "analisar")  # o ciclo
construtor.add_edge("responder", END)

app = construtor.compile()


def executar(solicitacao: str) -> None:
    print("=" * 64)
    print("Solicitação:", solicitacao)
    print("=" * 64)
    estado: dict = {"solicitacao": solicitacao}
    caminho = []
    # stream(updates): um item por nó executado -- é assim que "vemos" o caminho percorrido
    for passo in app.stream(estado, stream_mode="updates"):
        for no, atualizacao in passo.items():
            caminho.append(no)
            estado.update(atualizacao)
    print("\nCaminho percorrido:", " -> ".join(caminho))
    print(f"Tentativas de análise: {estado.get('tentativas', 0)} | validada: {estado.get('valida')}")
    print("Resposta:", estado["resposta"], "\n")


if __name__ == "__main__":
    print(f"Modelo em uso: {modelo.nome}\n")
    if len(sys.argv) > 1:
        executar(" ".join(sys.argv[1:]))
    else:
        executar("Qual o horário de atendimento?")
        executar("Preciso saber quais são os procedimentos para solicitar uma segunda via de um documento.")
