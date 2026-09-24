"""
seed_postgres.py -- popula o banco de OCORRÊNCIAS (PostgreSQL) da CISP.

Gera ~20.000 ocorrências fictícias, distribuídas em 12 meses, com padrões
INTENCIONAIS e determinísticos (mesma seed para toda a turma):

  - regiões BRAVO, FOXTROT e KILO concentram mais ocorrências (hotspots),
    sobretudo ROUBO e ROUBO_VEICULO;
  - horário noturno (19h-23h) tem mais ocorrências violentas;
  - os últimos 30 dias têm um crescimento deliberado de ROUBO nas regiões
    hotspot, para alimentar o desafio final ("três regiões com maior
    crescimento de roubos");
  - variação sazonal leve ao longo dos 12 meses.

Uso:
    python dados/seed_postgres.py
Requer: psycopg2-binary (ver dados/requirements.txt) e o container
'cisp-postgres' no ar (docker compose up -d postgres).
"""
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

from referencia import REGIOES, TIPOS_OCORRENCIA, UNIDADES, STATUS_OCORRENCIA, SEED_DETERMINISTICO

# Mesmo .env dos MCP Servers (aula5/.env) -- porta, senha etc.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PG_DSN = dict(
    host=os.getenv("PG_HOST", "127.0.0.1"),
    port=int(os.getenv("PG_PORT", "5434")),
    user=os.getenv("PG_USER", "postgres"),
    password=os.getenv("PG_PASSWORD", "Postgres@12345"),
    dbname=os.getenv("PG_DATABASE", "cisp_ocorrencias"),
)

TOTAL_OCORRENCIAS = 20_000
DIAS_HISTORICO = 365
HOJE = datetime(2026, 9, 22, 12, 0, 0)  # data fixa -> geração 100% determinística
INICIO = HOJE - timedelta(days=DIAS_HISTORICO)

random.seed(SEED_DETERMINISTICO)


def conectar():
    return psycopg2.connect(**PG_DSN)


def carregar_referencias(cur):
    cur.execute("DELETE FROM ocorrencias;")
    cur.execute("DELETE FROM unidades;")
    cur.execute("DELETE FROM tipos_ocorrencia;")
    cur.execute("DELETE FROM regioes;")

    execute_values(
        cur,
        "INSERT INTO regioes (codigo, nome, zona) VALUES %s RETURNING id, codigo",
        [(c, n, z) for c, n, z, _, _ in REGIOES],
    )
    regiao_ids = {codigo: rid for rid, codigo in cur.fetchall()}

    execute_values(
        cur,
        "INSERT INTO tipos_ocorrencia (codigo, nome, categoria, gravidade_base) VALUES %s RETURNING id, codigo",
        [(c, n, cat, grav) for c, n, cat, grav, _ in TIPOS_OCORRENCIA],
    )
    tipo_ids = {codigo: tid for tid, codigo in cur.fetchall()}

    unidades_rows = [(codigo, nome, regiao_ids[regiao_cod]) for codigo, nome, regiao_cod, _tipo, _lat, _lon in UNIDADES]
    execute_values(
        cur,
        "INSERT INTO unidades (codigo, nome, regiao_id) VALUES %s RETURNING id, codigo",
        unidades_rows,
    )
    unidade_ids = {codigo: uid for uid, codigo in cur.fetchall()}

    return regiao_ids, tipo_ids, unidade_ids


def unidades_por_regiao():
    mapa = {}
    for codigo, _nome, regiao_cod, _tipo, _lat, _lon in UNIDADES:
        mapa.setdefault(regiao_cod, []).append(codigo)
    return mapa


def sortear_hora():
    """Distribuição de horário com pico noturno (19h-23h)."""
    faixas = [
        (range(0, 6), 0.10),
        (range(6, 12), 0.18),
        (range(12, 19), 0.32),
        (range(19, 24), 0.40),
    ]
    r = random.random()
    acumulado = 0.0
    for horas, peso in faixas:
        acumulado += peso
        if r <= acumulado:
            return random.choice(list(horas))
    return random.randint(0, 23)


def sortear_dia_com_tendencia(regiao_codigo, hotspots):
    """
    Sorteia um dia dentro dos 365 do histórico. Nas regiões hotspot, os
    últimos 30 dias recebem peso extra para simular CRESCIMENTO recente
    de ocorrências (usado no desafio final: "regiões com maior
    crescimento de roubos nos últimos 30 dias").
    """
    dia_offset = random.randint(0, DIAS_HISTORICO - 1)
    if regiao_codigo in hotspots and random.random() < 0.35:
        dia_offset = random.randint(DIAS_HISTORICO - 30, DIAS_HISTORICO - 1)
    return INICIO + timedelta(days=dia_offset)


def gerar_lat_lon_proxima(lat_base, lon_base):
    return round(lat_base + random.uniform(-0.02, 0.02), 6), round(lon_base + random.uniform(-0.02, 0.02), 6)


def main():
    hotspots = {"BRAVO", "FOXTROT", "KILO"}
    regiao_por_codigo = {c: (n, z, po, pv) for c, n, z, po, pv in REGIOES}
    unidade_por_codigo = {c: (nome, regiao_cod, tipo, lat, lon) for c, nome, regiao_cod, tipo, lat, lon in UNIDADES}
    tipos_por_codigo = {c: (n, cat, grav, freq) for c, n, cat, grav, freq in TIPOS_OCORRENCIA}
    mapa_unidades_regiao = unidades_por_regiao()

    # peso de cada região = peso_ocorrencias (concentra hotspots)
    regioes_codigos = [c for c, *_ in REGIOES]
    pesos_regiao = [regiao_por_codigo[c][2] for c in regioes_codigos]

    tipos_codigos = [c for c, *_ in TIPOS_OCORRENCIA]
    pesos_tipo_base = [tipos_por_codigo[c][3] for c in tipos_codigos]

    conn = conectar()
    conn.autocommit = False
    cur = conn.cursor()
    try:
        regiao_ids, tipo_ids, unidade_ids = carregar_referencias(cur)

        linhas = []
        for _ in range(TOTAL_OCORRENCIAS):
            regiao_cod = random.choices(regioes_codigos, weights=pesos_regiao, k=1)[0]

            # nas regiões hotspot, ROUBO e ROUBO_VEICULO têm peso extra
            pesos_tipo = list(pesos_tipo_base)
            if regiao_cod in hotspots:
                for i, tc in enumerate(tipos_codigos):
                    if tc in ("ROUBO", "ROUBO_VEICULO"):
                        pesos_tipo[i] *= 2.2

            tipo_cod = random.choices(tipos_codigos, weights=pesos_tipo, k=1)[0]
            nome_tipo, categoria, gravidade_base, _freq = tipos_por_codigo[tipo_cod]

            dia = sortear_dia_com_tendencia(regiao_cod, hotspots)
            hora = sortear_hora()
            data_hora = dia.replace(hour=hora, minute=random.randint(0, 59), second=random.randint(0, 59))

            unidade_cod = random.choice(mapa_unidades_regiao[regiao_cod])
            _nome_u, _reg_u, _tipo_u, lat_base, lon_base = unidade_por_codigo[unidade_cod]
            lat, lon = gerar_lat_lon_proxima(lat_base, lon_base)

            # gravidade tem uma pequena variação em torno da gravidade_base
            gravidade = random.choices(
                ["BAIXA", "MEDIA", "ALTA", "CRITICA"],
                weights={
                    "BAIXA": [70, 20, 8, 2],
                    "MEDIA": [15, 55, 25, 5],
                    "ALTA": [5, 20, 55, 20],
                    "CRITICA": [2, 8, 30, 60],
                }[gravidade_base],
                k=1,
            )[0]

            idade_dias = (HOJE - data_hora).days
            if idade_dias < 2:
                status = random.choices(STATUS_OCORRENCIA, weights=[50, 40, 8, 2], k=1)[0]
            elif idade_dias < 30:
                status = random.choices(STATUS_OCORRENCIA, weights=[5, 15, 60, 20], k=1)[0]
            else:
                status = random.choices(STATUS_OCORRENCIA, weights=[1, 3, 46, 50], k=1)[0]

            linhas.append((
                data_hora, tipo_ids[tipo_cod], regiao_ids[regiao_cod],
                gravidade, status, unidade_ids[unidade_cod], lat, lon,
            ))

        execute_values(
            cur,
            """INSERT INTO ocorrencias
               (data_hora, tipo_ocorrencia_id, regiao_id, gravidade, status, unidade_responsavel_id, latitude, longitude)
               VALUES %s""",
            linhas,
            page_size=1000,
        )
        conn.commit()
        print(f"OK: {len(linhas)} ocorrências inseridas em cisp_ocorrencias.")

        cur.execute("SELECT COUNT(*) FROM ocorrencias;")
        print("Total na tabela:", cur.fetchone()[0])

        cur.execute("""
            SELECT r.nome, COUNT(*) AS total
            FROM ocorrencias o JOIN regioes r ON r.id = o.regiao_id
            GROUP BY r.nome ORDER BY total DESC LIMIT 5;
        """)
        print("Top 5 regiões por volume de ocorrências:")
        for nome, total in cur.fetchall():
            print(f"  {nome}: {total}")

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
