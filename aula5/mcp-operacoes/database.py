"""
database.py -- acesso ao SQL Server do MCP Operações.

Mesma ideia do database.py do MCP Ocorrências: só este módulo sabe que
existe um SQL Server. O agente nunca vê isso -- só vê as tools do server.py.
"""
import os
from pathlib import Path

import pymssql
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MSSQL_CONFIG = dict(
    server=os.getenv("MSSQL_HOST", "127.0.0.1"),
    port=int(os.getenv("MSSQL_PORT", "1433")),
    user=os.getenv("MSSQL_USER", "sa"),
    password=os.getenv("MSSQL_PASSWORD", "YourStrong@Password123"),
    database=os.getenv("MSSQL_DATABASE", "cisp_operacoes"),
)


def conectar():
    return pymssql.connect(**MSSQL_CONFIG, as_dict=True)


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Executa um SELECT e devolve uma lista de dicts (nome da coluna -> valor)."""
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())
