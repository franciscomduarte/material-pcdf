"""
Exemplo 03 -- ESTADO COMPARTILHADO.

No exemplo 01, 'categoria' era uma variável solta que ninguém usava. No 02,
o grafo dizia POR ONDE ir, mas não O QUE circula entre as etapas.

Agora criamos o ESTADO: um único dicionário tipado com tudo o que sabemos
sobre a solicitação. Cada nó recebe o estado e devolve o que quer ATUALIZAR.

              ESTADO
                │
        ┌───────┼────────┐
        ↓       ↓        ↓
      nó 1     nó 2     nó 3
        │       │        │
        └───────┼────────┘
                ↓
          estado atualizado

Ainda sem LangGraph: o "motor" que executa os nós é um laço de poucas linhas
escrito por nós. Guarde essa ideia -- no exemplo 04 o LangGraph faz esse
papel.

Rodar:
    python main.py
"""
from typing import TypedDict


class Estado(TypedDict):
    solicitacao: str
    categoria: str
    resultado: str
    resposta: str


# Cada nó: recebe o ESTADO inteiro, devolve só a PARTE que mudou.
def receber(estado: Estado) -> dict:
    print("[receber]")
    return {"solicitacao": estado["solicitacao"].strip()}


def classificar(estado: Estado) -> dict:
    print("[classificar]")
    return {"categoria": "simples"}


def analisar(estado: Estado) -> dict:
    print("[analisar]")
    # este nó LÊ 'categoria', escrita por outro nó: é isso que "compartilhar" significa
    return {"resultado": f"análise de solicitação {estado['categoria']}"}


def responder(estado: Estado) -> dict:
    print("[responder]")
    return {"resposta": f"Resposta baseada em: {estado['resultado']}"}


# Estado inicial: só a entrada; o resto é preenchido pelos nós.
estado: Estado = {
    "solicitacao": "  Preciso saber como solicitar uma segunda via.  ",
    "categoria": "",
    "resultado": "",
    "resposta": "",
}

print("Estado inicial:", estado, "\n")

# O "motor" manual: executa cada nó e MESCLA a atualização no estado.
for no in [receber, classificar, analisar, responder]:
    atualizacao = no(estado)
    estado.update(atualizacao)
    print("   estado agora:", estado, "\n")

print("Estado final:")
for campo, valor in estado.items():
    print(f"  {campo:12} = {valor!r}")

# ---------------------------------------------------------------------------
# Repare: nenhum nó recebe argumentos "soltos" e nenhum precisa conhecer os
# outros. Todos conversam através do estado. Isso resolve a pergunta 3 do
# exemplo 01 ("onde está o estado?").
# ---------------------------------------------------------------------------
