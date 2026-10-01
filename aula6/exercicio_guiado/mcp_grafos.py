"""
PASSO 3 -- MCP Server que entrega o desenho dos grafos da Aula 6.

Você já sabe gerar o Mermaid (passo 1). Agora vai expor isso como TOOLS de um MCP Server, para
qualquer cliente (o seu script de teste, o Claude Code...) pedir "me mostra o grafo do exemplo X".

Tools a implementar (leia o README.md, passo 3):
    listar_exemplos()              -> list[str]   os nomes de exemplo disponíveis
    mermaid_do_grafo(exemplo)      -> str         o texto Mermaid do grafo
    descrever_grafo(exemplo)       -> dict        nós e arestas (fixa ou condicional)

Testar SEM Claude:
    python cliente_teste.py
    python cliente_teste.py mermaid_do_grafo 07_dag

REGRA DE OURO de um servidor stdio: NUNCA use print() aqui. O stdout é o canal do protocolo MCP;
um print estraga a conversa (para depurar, use print(..., file=sys.stderr)).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.mcpserver import MCPServer

from carregar_grafo import EXEMPLOS, carregar_app

mcp = MCPServer("grafos-mcp")


# A docstring de cada tool é o que o CLIENTE (e o LLM) lê para decidir quando usá-la: escreva bem.
@mcp.tool()
def listar_exemplos() -> list[str]:
    """Lista os exemplos da Aula 6 cujo grafo pode ser consultado."""
    # TODO 1: devolva a lista de exemplos (já importada acima).
    raise NotImplementedError("TODO 1")


@mcp.tool()
def mermaid_do_grafo(exemplo: str) -> str:
    """Devolve o diagrama Mermaid do grafo de um exemplo da Aula 6.

    Args:
        exemplo: nome da pasta do exemplo (ex.: '10_agente_completo'). Use listar_exemplos para ver as opções.
    """
    # TODO 2: carregue o app do exemplo e devolva o Mermaid (como no passo 1).
    #         Se o nome não existir, carregar_app levanta ValueError: devolva "ERRO: <mensagem>"
    #         em vez de deixar o servidor quebrar.
    raise NotImplementedError("TODO 2")


@mcp.tool()
def descrever_grafo(exemplo: str) -> dict:
    """Resume o grafo de um exemplo: nós e arestas (com o tipo: fixa ou condicional).

    Args:
        exemplo: nome da pasta do exemplo (ex.: '07_dag').
    """
    # TODO 3: com grafo = carregar_app(exemplo).get_graph(), devolva:
    #   {"exemplo": exemplo,
    #    "nos": list(grafo.nodes),
    #    "arestas": [{"origem": a.source, "destino": a.target, "condicional": bool(a.conditional)}
    #                for a in grafo.edges]}
    #   Exemplo desconhecido: devolva {"erro": "<mensagem>"}.
    raise NotImplementedError("TODO 3")


if __name__ == "__main__":
    mcp.run(transport="stdio")
