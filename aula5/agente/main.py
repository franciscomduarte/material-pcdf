"""
Agente final da CISP -- conecta aos três MCP Servers via STREAMABLE HTTP
(não mais stdio). É a versão que roda em produção, cada peça no seu
próprio container Docker, falando entre si pela rede `cisp-net`.

Diferença em relação aos exemplos anteriores (stdio):
  - stdio: o Agent Framework SOBE o processo do MCP Server (subprocess)
    e fala com ele por stdin/stdout. Só funciona quando os dois processos
    estão na mesma máquina.
  - streamable-http: o MCP Server já está rodando (como um serviço HTTP
    de longa duração, em outro container/máquina) e o Agent Framework só
    se CONECTA nele por HTTP, num endereço configurável (MCP_*_URL).

Modo interativo (o container `agente` do docker-compose sobe com
stdin_open/tty para isso). Rodar localmente contra os serviços do Docker:

    python main.py
"""
import asyncio
import os
import sys

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

from provedor import configurar

configurar()

URL_OCORRENCIAS = os.getenv("MCP_OCORRENCIAS_URL", "http://localhost:8001/mcp")
URL_OPERACOES = os.getenv("MCP_OPERACOES_URL", "http://localhost:8002/mcp")
URL_SERVICOS = os.getenv("MCP_SERVICOS_URL", "http://localhost:8003/mcp")

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
diga quais ferramentas usou e com quais parâmetros. Se a pergunta exigir
dados que nenhuma ferramenta sua consegue fornecer, diga isso claramente.
"""


async def montar_agente() -> tuple[Agent, list]:
    mcp_ocorrencias = MCPServerStreamableHttp(name="MCP Ocorrências", params={"url": URL_OCORRENCIAS})
    mcp_operacoes = MCPServerStreamableHttp(name="MCP Operações", params={"url": URL_OPERACOES})
    mcp_servicos = MCPServerStreamableHttp(name="MCP Serviços", params={"url": URL_SERVICOS})
    servidores = [mcp_ocorrencias, mcp_operacoes, mcp_servicos]

    for servidor in servidores:
        await servidor.connect()

    agente = Agent(name="Assistente Analítico CISP", instructions=INSTRUCOES, mcp_servers=servidores)
    return agente, servidores


async def loop_interativo():
    agente, servidores = await montar_agente()
    try:
        print("Assistente CISP pronto. Digite sua pergunta (ou 'sair').")
        while True:
            pergunta = input("\n> ").strip()
            if pergunta.lower() in {"sair", "exit", "quit"}:
                break
            if not pergunta:
                continue
            resultado = await Runner.run(agente, pergunta, max_turns=20)
            print(resultado.final_output)
    finally:
        for servidor in servidores:
            await servidor.cleanup()


async def rodar_uma_pergunta(pergunta: str) -> str:
    """Usado por scripts de teste/CI -- roda uma pergunta e devolve a resposta final."""
    agente, servidores = await montar_agente()
    try:
        resultado = await Runner.run(agente, pergunta, max_turns=20)
        return resultado.final_output
    finally:
        for servidor in servidores:
            await servidor.cleanup()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pergunta = " ".join(sys.argv[1:])
        print(asyncio.run(rodar_uma_pergunta(pergunta)))
    else:
        asyncio.run(loop_interativo())
