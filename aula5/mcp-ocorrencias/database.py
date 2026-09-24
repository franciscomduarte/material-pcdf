"""
database.py -- acesso ao PostgreSQL do MCP Ocorrências.

Importante para a aula: este módulo é o ÚNICO lugar que sabe que existe um
PostgreSQL, com qual host/porta e qual SQL. Nem o agente, nem o MCP Client,
nem o LLM enxergam nada disso -- eles só veem as tools do server.py.
"""
import os
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Carrega o .env explicitamente (não dá pra contar com env var herdada do
# processo pai: quando o Agent Framework sobe este server via MCPServerStdio,
# ele NÃO repassa o ambiente do processo pai por padrão -- só o que estiver
# em params["env"], ou o que este módulo carregar aqui).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PG_CONFIG = dict(
    host=os.getenv("PG_HOST", "127.0.0.1"),
    port=int(os.getenv("PG_PORT", "5434")),
    user=os.getenv("PG_USER", "postgres"),
    password=os.getenv("PG_PASSWORD", "Postgres@12345"),
    dbname=os.getenv("PG_DATABASE", "cisp_ocorrencias"),
)


def conectar():
    return psycopg2.connect(**PG_CONFIG)


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Executa um SELECT e devolve uma lista de dicts (nome da coluna -> valor)."""
    with conectar() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            linhas = cur.fetchall()
            return [dict(linha) for linha in linhas]
