"""
Exemplo 09 (conteúdo) -- MCP QUE NÃO USA BANCO.

Adicionamos o MCP Serviços (mcp-servicos/server.py) -- que não tem NENHUM
banco atrás dele, só cálculo. Agora o agente combina TRÊS servidores:

    MCP Ocorrências (Postgres)  -> fatos criminais
    MCP Operações   (SQL Server)-> unidades, viaturas, equipes
    MCP Serviços    (sem banco) -> distância geográfica, índice operacional

Pergunta que só faz sentido com os três:
    "Qual a unidade mais próxima da última ocorrência de ROUBO registrada
     na Região Bravo, e quantas viaturas disponíveis ela tem?"

Fluxo esperado:
  1. consultar_ocorrencias(regiao='Bravo', tipo='ROUBO', periodo_dias=30)
     -> pega latitude/longitude da ocorrência mais recente;
  2. consultar_unidades(regiao='Bravo') -> lista de unidades com lat/long;
  3. encontrar_unidades_proximas(lat, lon, unidades=<resultado do passo 2>)
     -> AQUI o agente passa o resultado de uma tool como ENTRADA de outra,
        sem nenhuma delas saber da existência da outra;
  4. consultar_viaturas_disponiveis(unidade=<código da unidade mais próxima>).

Este é o exemplo que fecha a ideia central da aula: MCP não é "MCP + banco".
É uma camada de capacidades -- e capacidades podem ser cálculo puro.

Rodar:
    python agente_com_servicos.py
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
RAIZ = Path(__file__).resolve().parents[2]
SERVER_OCORRENCIAS = str(BASE / "05_multiplas_tools" / "server.py")
SERVER_OPERACOES = str(Path(__file__).resolve().parent / "server_operacoes.py")
SERVER_SERVICOS = str(RAIZ / "mcp-servicos" / "server.py")


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
            name="Assistente CISP",
            instructions=(
                "Você tem acesso a três MCP Servers independentes da CISP: "
                "Ocorrências (fatos criminais, Postgres), Operações (unidades/"
                "viaturas/equipes, SQL Server) e Serviços (cálculo geográfico e "
                "índices, SEM banco de dados). Nenhum deles compartilha dados "
                "diretamente -- você é quem cruza as informações. Para achar a "
                "unidade mais próxima de um ponto, primeiro pegue a lista de "
                "unidades candidatas no MCP Operações e SÓ ENTÃO chame "
                "encontrar_unidades_proximas no MCP Serviços, passando essa lista."
            ),
            mcp_servers=[mcp_ocorrencias, mcp_operacoes, mcp_servicos],
        )

        pergunta = (
            "Qual a unidade mais próxima da ocorrência de ROUBO mais recente "
            "registrada na Região Bravo? Diga também quantas viaturas "
            "disponíveis essa unidade tem agora."
        )
        resultado = await Runner.run(agente, pergunta, max_turns=15)
        print(resultado.final_output)


if __name__ == "__main__":
    asyncio.run(main())
