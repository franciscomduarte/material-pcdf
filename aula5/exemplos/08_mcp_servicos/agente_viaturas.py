"""
Exemplo 08 -- pergunta que exige raciocínio em cadeia sobre os dois sistemas.

    "Quantas viaturas disponíveis existem nas unidades responsáveis pelas
     regiões com maior número de ocorrências?"

Para responder, o agente precisa (sem que ninguém dite a ordem):
  1. consultar ocorrências agregadas por região (MCP Ocorrências);
  2. identificar as regiões com mais ocorrências;
  3. consultar as unidades dessas regiões (MCP Operações);
  4. consultar as viaturas disponíveis dessas unidades (MCP Operações);
  5. somar/organizar o resultado final.

Isso são 3-4 chamadas de tool em sequência, decididas pelo próprio LLM.
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
SERVER_OPERACOES = str(Path(__file__).resolve().parent / "server_operacoes.py")


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
                "Você integra o MCP Ocorrências e o MCP Operações da CISP, que "
                "não compartilham banco de dados. Para perguntas que envolvem "
                "'regiões com mais ocorrências' E 'viaturas/unidades', primeiro "
                "descubra as regiões (MCP Ocorrências), depois busque unidades e "
                "viaturas dessas regiões (MCP Operações), uma região por vez. "
                "Mostre o raciocínio: quais tools chamou e com quais parâmetros."
            ),
            mcp_servers=[mcp_ocorrencias, mcp_operacoes],
        )

        pergunta = (
            "Quantas viaturas disponíveis existem nas unidades responsáveis "
            "pelas 3 regiões com maior número de ocorrências?"
        )
        resultado = await Runner.run(agente, pergunta, max_turns=25)
        print(resultado.final_output)


if __name__ == "__main__":
    asyncio.run(main())
