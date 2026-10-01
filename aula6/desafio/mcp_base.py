"""
MCP Server do desafio 1 -- a BASE DE CONHECIMENTO do atendimento, como um serviço.

    consultar_base(solicitacao) -> [{"assunto", "texto", "prazo_dias_uteis"}]   (lista VAZIA se não souber)

Lê base_conhecimento.csv. Nenhuma IA aqui: é só consulta. Quem sobe este processo é o nó do grafo (via stdio);
o grafo só conhece o NOME da tool e seus parâmetros (o contrato, como na Aula 5).

REGRA DE OURO de um servidor stdio: NUNCA use print() aqui (o stdout é o canal do protocolo MCP).

Testar isolado:
    npx @modelcontextprotocol/inspector python mcp_base.py
"""
import csv
from pathlib import Path

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("base-atendimento-mcp")

CSV = Path(__file__).resolve().parent / "base_conhecimento.csv"


@mcp.tool()
def consultar_base(solicitacao: str) -> list[dict]:
    """Procura, na base de conhecimento do atendimento, o assunto citado na solicitação.

    Devolve uma lista com UM item {assunto, texto, prazo_dias_uteis} quando o assunto está na base,
    ou uma lista VAZIA quando não está (nesse caso o sistema NÃO pode inventar uma resposta).

    Args:
        solicitacao: o texto da solicitação do usuário (ex.: 'Preciso de uma segunda via do documento').
    """
    texto = solicitacao.lower()
    with open(CSV, encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            if linha["assunto"].lower() in texto:
                return [{
                    "assunto": linha["assunto"],
                    "texto": linha["texto"],
                    "prazo_dias_uteis": int(linha["prazo_dias_uteis"]),
                }]
    return []


if __name__ == "__main__":
    mcp.run(transport="stdio")
