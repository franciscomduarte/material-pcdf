"""
Cliente de teste do Exemplo 02.1 -- pergunta em português, resposta em português.

Sobe `python server.py`, chama a tool perguntar_ocorrencias e imprime:
  - o SQL que o server gerou (vem do stderr do server, só para você ver);
  - a resposta em texto, que é tudo o que um agente receberia.

Rodar:
    python cliente.py
    python cliente.py "Quais os tipos de ocorrência mais comuns?"
"""
import asyncio
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = str(Path(__file__).resolve().parent / "server.py")
PERGUNTA = sys.argv[1] if len(sys.argv) > 1 else "Quantas ocorrências graves aconteceram na Região Bravo?"


async def main():
    params = StdioServerParameters(command=sys.executable, args=[SERVER])
    log_server = tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace")   # stderr do server
    async with stdio_client(params, errlog=log_server) as (leitura, escrita):
        async with ClientSession(leitura, escrita) as sessao:
            await sessao.initialize()
            print(f"Pergunta: {PERGUNTA}\n")
            resposta = await sessao.call_tool("perguntar_ocorrencias", {"pergunta": PERGUNTA})

            log_server.seek(0)
            print("--- Por dentro do server (não chega ao agente) ---")
            for linha in log_server:
                if "HTTP Request" not in linha and linha.strip():
                    print(linha.rstrip())

            print("\n--- Resposta (tudo o que o agente recebe) ---")
            if resposta.is_error:
                print("ERRO:", resposta.content)
                return
            for item in resposta.content:
                print(item.text)


if __name__ == "__main__":
    asyncio.run(main())
