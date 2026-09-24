"""
Cliente de teste do Exemplo 02 -- chama o MCP Server sem precisar de agente.

Sobe `python server.py` como subprocesso, abre uma sessão MCP e chama a
tool consultar_ocorrencias_natural.

Rodar:
    python cliente.py
    python cliente.py "Quais ocorrências graves aconteceram hoje?"
"""
import asyncio
import json
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = str(Path(__file__).resolve().parent / "server.py")
PERGUNTA = sys.argv[1] if len(sys.argv) > 1 else "Quais as 10 ocorrências mais recentes?"


async def main():
    params = StdioServerParameters(command=sys.executable, args=[SERVER])
    # O server escreve o SQL gerado no stderr. Guardamos esse stderr num arquivo
    # temporário para mostrá-lo em ordem, logo antes do resultado.
    log_server = tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace")
    async with stdio_client(params, errlog=log_server) as (leitura, escrita):
        async with ClientSession(leitura, escrita) as sessao:
            await sessao.initialize()
            print(f"Pergunta: {PERGUNTA}\n")
            resposta = await sessao.call_tool(
                "consultar_ocorrencias_natural", {"pergunta": PERGUNTA}
            )
            if resposta.is_error:
                print("ERRO:", resposta.content)
                return
            log_server.seek(0)
            sql = [l.rstrip() for l in log_server if "HTTP Request" not in l]
            print("--- SQL gerado pelo server ---")
            print("\n".join(sql).replace("SQL gerado: ", "", 1).strip(), "\n")
            print("--- Resultado ---")
            for item in resposta.content:
                linha = json.loads(item.text)
                print(linha["data_hora"], "|", linha.get("tipo"), "|",
                      linha.get("regiao"), "|", linha.get("gravidade"), "|", linha.get("status"))


if __name__ == "__main__":
    asyncio.run(main())
