"""
Testes do exercício guiado (rodam sem API Key e sem internet). Na pasta aula6/:

    python -m unittest exercicio_guiado.test_guiado -v

Cada teste corresponde a um passo do README. Um teste passando de cada vez é um bom ritmo.
Para testar a solução do professor:  $env:GUIADO_DIR = "exercicio_guiado\\solucao"
"""
import asyncio
import os
import subprocess
import sys
import unittest
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE = Path(__file__).resolve().parent
PASTA = Path(os.getenv("GUIADO_DIR", BASE))
if not PASTA.is_absolute():
    PASTA = BASE.parent / PASTA


class TestPasso1(unittest.TestCase):
    def test_gera_mmd_e_md(self):
        for arquivo in (BASE / "saida").glob("07_dag.*"):
            arquivo.unlink()
        r = subprocess.run([sys.executable, str(PASTA / "passo1_mermaid.py"), "07_dag"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        mmd = (BASE / "saida" / "07_dag.mmd").read_text(encoding="utf-8")
        md = (BASE / "saida" / "07_dag.md").read_text(encoding="utf-8")
        self.assertIn("graph TD", mmd)
        self.assertIn("consolidar", mmd)
        self.assertIn("```mermaid", md)
        self.assertIn(mmd.strip(), md)


async def _com_servidor(funcao):
    params = StdioServerParameters(command=sys.executable, args=[str(PASTA / "mcp_grafos.py")])
    with open(os.devnull, "w") as silencio:
        async with stdio_client(params, errlog=silencio) as (leitura, escrita):
            async with ClientSession(leitura, escrita) as sessao:
                await sessao.initialize()
                return await funcao(sessao)


def com_servidor(funcao):
    return asyncio.run(_com_servidor(funcao))


class TestPasso3Servidor(unittest.TestCase):
    def test_expoe_as_tres_tools(self):
        async def f(s):
            return {t.name for t in (await s.list_tools()).tools}
        self.assertEqual(com_servidor(f), {"listar_exemplos", "mermaid_do_grafo", "descrever_grafo"})

    def test_listar_exemplos(self):
        async def f(s):
            return [i.text for i in (await s.call_tool("listar_exemplos", {})).content]
        exemplos = com_servidor(f)
        self.assertIn("10_agente_completo", exemplos)
        self.assertIn("07_dag", exemplos)

    def test_mermaid_do_grafo(self):
        async def f(s):
            return (await s.call_tool("mermaid_do_grafo", {"exemplo": "07_dag"})).content[0].text
        texto = com_servidor(f)
        self.assertIn("graph TD", texto)
        self.assertIn("classificar --> pesquisar", texto)

    def test_descrever_grafo(self):
        import json

        async def f(s):
            return json.loads((await s.call_tool("descrever_grafo", {"exemplo": "10_agente_completo"})).content[0].text)
        dados = com_servidor(f)
        self.assertIn("validar", dados["nos"])
        self.assertTrue(any(a["condicional"] for a in dados["arestas"]), "o exemplo 10 tem arestas condicionais")
        self.assertTrue(all({"origem", "destino", "condicional"} <= set(a) for a in dados["arestas"]))

    def test_exemplo_inexistente_nao_derruba_o_servidor(self):
        async def f(s):
            erro = (await s.call_tool("mermaid_do_grafo", {"exemplo": "xyz"})).content[0].text
            depois = (await s.call_tool("listar_exemplos", {})).content  # o servidor continua vivo?
            return erro, depois
        erro, depois = com_servidor(f)
        self.assertTrue(erro.startswith("ERRO"))
        self.assertTrue(depois)


if __name__ == "__main__":
    unittest.main()
