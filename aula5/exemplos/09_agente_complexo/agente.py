"""
Exemplo 10 -- PERGUNTA COMPLEXA (o agente decide o caminho sozinho).

Agora usamos as versões FINAIS dos três MCP Servers (mcp-ocorrencias/,
mcp-operacoes/, mcp-servicos/ -- na raiz da aula5, não mais as versões
reduzidas dos exemplos anteriores). Isso dá ao agente o conjunto completo
de capacidades: comparar_periodos, consultar_disponibilidade,
calcular_indice_operacional etc.

DE PROPÓSITO não descrevemos aqui a sequência de chamadas. O objetivo
deste exemplo é observar o RACIOCÍNIO OPERACIONAL do agente: quais tools
ele escolhe, em que ordem, e como ele lida com uma pergunta que não tem
um caminho único e óbvio.

Pergunta (a mesma do desafio final da aula):
    "Nos últimos 30 dias, identifique as três regiões com maior
     crescimento de roubos. Para cada região, identifique a unidade
     responsável, consulte a quantidade de viaturas disponíveis e calcule
     a distância aproximada até a unidade mais próxima. Produza uma
     análise consolidada."

Rodar:
    python agente.py

Depois de rodar, para a discussão em aula, use Runner.run com
tracing/RunResult (ver Exemplo 11 -- Observabilidade) para responder:
qual tool foi chamada primeiro? Quantas chamadas no total? Alguma
chamada foi redundante?
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from provedor import configurar

configurar()

RAIZ = Path(__file__).resolve().parents[2]
SERVER_OCORRENCIAS = str(RAIZ / "mcp-ocorrencias" / "server.py")
SERVER_OPERACOES = str(RAIZ / "mcp-operacoes" / "server.py")
SERVER_SERVICOS = str(RAIZ / "mcp-servicos" / "server.py")

INSTRUCOES = """\
Você é o Assistente Analítico da CISP (Central Integrada de Segurança
Pública). Você tem acesso a três MCP Servers independentes, que NÃO
compartilham banco de dados entre si:

  - MCP Ocorrências: fatos criminais (tipos, regiões, gravidade, tendências).
  - MCP Operações: unidades, viaturas e equipes.
  - MCP Serviços: cálculo geográfico e índices operacionais (sem banco).

Para perguntas que cruzam sistemas, planeje as chamadas você mesmo:
descubra os dados no MCP Ocorrências primeiro, depois busque as unidades
correspondentes no MCP Operações casando pelo NOME DA REGIÃO, e use o MCP
Serviços quando precisar de distância ou de um índice consolidado. Sempre
que responder, diga explicitamente quais ferramentas usou e com quais
parâmetros -- isso faz parte da resposta, não é opcional.
"""


async def main():
    async with MCPServerStdio(
        name="MCP Ocorrências",
        params={"command": "python", "args": [SERVER_OCORRENCIAS]},
    ) as mcp_ocorrencias, MCPServerStdio(
        name="MCP Operações",
        params={"command": "python", "args": [SERVER_OPERACOES]},
    ) as mcp_operacoes, MCPServerStdio(
        name="MCP Serviços",
        params={"command": "python", "args": [SERVER_SERVICOS]},
    ) as mcp_servicos:

        agente = Agent(
            name="Assistente Analítico CISP",
            instructions=INSTRUCOES,
            mcp_servers=[mcp_ocorrencias, mcp_operacoes, mcp_servicos],
        )

        pergunta = (
            "Nos últimos 30 dias, identifique as três regiões com maior "
            "crescimento de roubos (compare com os 30 dias anteriores). "
            "Para cada uma dessas regiões, identifique a unidade "
            "responsável, consulte a quantidade de viaturas disponíveis e "
            "calcule a distância aproximada até a unidade mais próxima da "
            "sede da região. Produza uma análise consolidada."
        )
        resultado = await Runner.run(agente, pergunta, max_turns=25)
        print(resultado.final_output)


if __name__ == "__main__":
    asyncio.run(main())
