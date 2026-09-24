"""
Exemplo 07 -- DOIS MCP SERVERS.

Momento importante da aula: o mesmo agente conecta em DOIS MCP Servers
diferentes (Ocorrências/Postgres e Operações/SQL Server) e o LLM decide
sozinho QUANDO usar cada um, na ordem certa, para responder uma pergunta
que nenhum dos dois bancos responde sozinho:

    "Quais regiões possuem mais ocorrências e quais unidades atendem
     essas regiões?"

Não existe JOIN entre os bancos. O agente:
  1. chama estatisticas_ocorrencias(agrupar_por='regiao') no MCP Ocorrências
     -> descobre o ranking de regiões;
  2. chama consultar_unidades() no MCP Operações
     -> descobre as unidades e a região de cada uma;
  3. CRUZA os dois resultados na própria resposta, casando pelo nome da
     região (texto), porque é essa a única "chave" que os dois sistemas
     compartilham conceitualmente.

Isso é a integração acontecendo no AGENTE, não no banco.

Rodar:
    python agente.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from provedor import configurar

configurar()

BASE = Path(__file__).resolve().parents[1]
SERVER_OCORRENCIAS = str(BASE / "05_multiplas_tools" / "server.py")
SERVER_OPERACOES = str(BASE / "06_mcp_operacoes" / "server.py")


async def main():
    async with MCPServerStdio(
        name="MCP Ocorrências",
        params={"command": "python", "args": [SERVER_OCORRENCIAS]},
    ) as mcp_ocorrencias, MCPServerStdio(
        name="MCP Operações",
        params={"command": "python", "args": [SERVER_OPERACOES]},
    ) as mcp_operacoes:

        agente = Agent(
            name="Assistente CISP",
            instructions=(
                "Você integra dados de dois sistemas independentes da CISP: "
                "o MCP Ocorrências (fatos criminais) e o MCP Operações "
                "(unidades, viaturas, equipes). Eles NÃO compartilham banco de "
                "dados -- a única forma de cruzá-los é pelo nome da região. "
                "Sempre que a pergunta exigir os dois sistemas, consulte ambos "
                "antes de responder, e explique de qual sistema veio cada dado."
            ),
            mcp_servers=[mcp_ocorrencias, mcp_operacoes],
        )

        pergunta = (
            "Quais são as 3 regiões com mais ocorrências? Para cada uma, "
            "diga quais unidades operacionais atendem essa região."
        )
        resultado = await Runner.run(agente, pergunta)

        # Trilha: qual tool, de qual MCP Server, com quais parâmetros.
        for item in resultado.new_items:
            if type(item).__name__ == "ToolCallItem":
                servidor = getattr(item.tool_origin, "mcp_server_name", None)
                print(f"[tool] {servidor} | {item.raw_item.name} {item.raw_item.arguments}")

        print("\n--- Resposta do agente ---")
        print(resultado.final_output)


if __name__ == "__main__":
    asyncio.run(main())
