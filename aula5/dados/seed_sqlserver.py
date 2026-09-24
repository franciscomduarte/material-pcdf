"""
seed_sqlserver.py -- popula o banco de OPERAÇÕES (SQL Server) da CISP.

Gera as mesmas 22 unidades do MCP Ocorrências (mesmo `codigo`, sem FK
entre bancos), 120 viaturas e ~300 equipes, com padrões INTENCIONAIS:

  - regiões hotspot (BRAVO, FOXTROT, KILO) têm proporcionalmente MENOS
    viaturas DISPONIVEL (mais em EM_ATENDIMENTO/MANUTENCAO) -- é o que
    o Exemplo 08 vai expor: "muita ocorrência, pouca viatura disponível";
  - histórico de mudanças de status nas últimas 72h por viatura.

Uso:
    python dados/seed_sqlserver.py
Requer: pymssql (ver dados/requirements.txt) e o container 'cisp-mssql'
no ar, com o schema de banco-sqlserver/init.sql já aplicado.
"""
import os
import random
from datetime import datetime, timedelta

import pymssql

from referencia import (
    UNIDADES, REGIOES, STATUS_VIATURA, TURNOS, ESPECIALIDADES, TIPOS_VIATURA,
    SEED_DETERMINISTICO,
)

MSSQL_CONN = dict(
    server=os.getenv("MSSQL_HOST", "127.0.0.1"),
    port=int(os.getenv("MSSQL_PORT", "1433")),
    user=os.getenv("MSSQL_USER", "sa"),
    password=os.getenv("MSSQL_PASSWORD", "YourStrong@Password123"),
    database=os.getenv("MSSQL_DATABASE", "cisp_operacoes"),
)

VIATURAS_POR_UNIDADE_MIN = 3
VIATURAS_POR_UNIDADE_MAX = 8
EQUIPES_POR_UNIDADE_MIN = 8
EQUIPES_POR_UNIDADE_MAX = 16
AGORA = datetime(2026, 9, 22, 12, 0, 0)

random.seed(SEED_DETERMINISTICO + 1)  # seed derivada, mas ainda determinística


def conectar():
    return pymssql.connect(**MSSQL_CONN, autocommit=False)


def limpar(cur):
    cur.execute("DELETE FROM historico_viaturas;")
    cur.execute("DELETE FROM equipes;")
    cur.execute("DELETE FROM viaturas;")
    cur.execute("DELETE FROM unidades;")
    cur.execute("DBCC CHECKIDENT ('unidades', RESEED, 0);")
    cur.execute("DBCC CHECKIDENT ('viaturas', RESEED, 0);")
    cur.execute("DBCC CHECKIDENT ('equipes', RESEED, 0);")
    cur.execute("DBCC CHECKIDENT ('historico_viaturas', RESEED, 0);")


def inserir_unidades(cur):
    regiao_nome = {c: n for c, n, *_ in REGIOES}
    unidade_ids = {}
    for codigo, nome, regiao_cod, tipo, lat, lon in UNIDADES:
        cur.execute(
            "INSERT INTO unidades (codigo, nome, regiao, tipo, latitude, longitude) "
            "OUTPUT INSERTED.id VALUES (%s, %s, %s, %s, %s, %s)",
            (codigo, nome, regiao_nome[regiao_cod], tipo, lat, lon),
        )
        unidade_ids[codigo] = cur.fetchone()[0]
    return unidade_ids


def status_disponibilidade_pesos(regiao_cod, hotspots):
    """
    Distribuição de status de viatura. Nas regiões hotspot, menos
    DISPONIVEL e mais EM_ATENDIMENTO/MANUTENCAO -- padrão intencional
    para o Exemplo 08 (cruzar ocorrências x viaturas disponíveis).
    """
    if regiao_cod in hotspots:
        # DISPONIVEL, EM_ATENDIMENTO, EM_DESLOCAMENTO, MANUTENCAO, INDISPONIVEL
        return [25, 35, 20, 12, 8]
    return [50, 20, 15, 10, 5]


def main():
    hotspots = {"BRAVO", "FOXTROT", "KILO"}

    conn = conectar()
    cur = conn.cursor()
    try:
        limpar(cur)
        unidade_ids = inserir_unidades(cur)

        prefixo_seq = 1
        viatura_ids_por_unidade = {}
        linhas_historico = []

        for codigo, _nome, regiao_cod, _tipo, lat_base, lon_base in UNIDADES:
            uid = unidade_ids[codigo]
            n_viaturas = random.randint(VIATURAS_POR_UNIDADE_MIN, VIATURAS_POR_UNIDADE_MAX)
            pesos_status = status_disponibilidade_pesos(regiao_cod, hotspots)
            viatura_ids_por_unidade[codigo] = []

            for _ in range(n_viaturas):
                prefixo = f"VTR-{prefixo_seq:04d}"
                prefixo_seq += 1
                tipo_v = random.choices(TIPOS_VIATURA, weights=[55, 25, 10, 10], k=1)[0]
                status = random.choices(STATUS_VIATURA, weights=pesos_status, k=1)[0]
                lat = round(lat_base + random.uniform(-0.015, 0.015), 6)
                lon = round(lon_base + random.uniform(-0.015, 0.015), 6)
                minutos_atras = random.randint(1, 240)
                ultima_atualizacao = AGORA - timedelta(minutes=minutos_atras)

                cur.execute(
                    "INSERT INTO viaturas (prefixo, unidade_id, tipo, status, latitude, longitude, ultima_atualizacao) "
                    "OUTPUT INSERTED.id VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (prefixo, uid, tipo_v, status, lat, lon, ultima_atualizacao),
                )
                vid = cur.fetchone()[0]
                viatura_ids_por_unidade[codigo].append(vid)

                # histórico das últimas 72h: 1 a 3 trocas de status
                n_eventos = random.randint(1, 3)
                cursor_tempo = AGORA - timedelta(hours=72)
                for i in range(n_eventos):
                    dur = timedelta(hours=random.randint(4, 30))
                    inicio = cursor_tempo
                    fim = inicio + dur
                    if fim > AGORA:
                        fim = None
                    status_evento = random.choice(STATUS_VIATURA)
                    linhas_historico.append((vid, status_evento, inicio, fim))
                    cursor_tempo = fim or AGORA

            n_equipes = random.randint(EQUIPES_POR_UNIDADE_MIN, EQUIPES_POR_UNIDADE_MAX)
            for _ in range(n_equipes):
                turno = random.choice(TURNOS)
                especialidade = random.choices(
                    ESPECIALIDADES, weights=[50, 20, 15, 15], k=1
                )[0]
                qtd_agentes = random.randint(2, 6)
                status_equipe = random.choices(
                    ["EM_SERVICO", "FOLGA", "TREINAMENTO"], weights=[65, 30, 5], k=1
                )[0]
                cur.execute(
                    "INSERT INTO equipes (unidade_id, turno, quantidade_agentes, especialidade, status) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (uid, turno, qtd_agentes, especialidade, status_equipe),
                )

        for vid, status_evento, inicio, fim in linhas_historico:
            cur.execute(
                "INSERT INTO historico_viaturas (viatura_id, status, data_hora_inicio, data_hora_fim) "
                "VALUES (%s, %s, %s, %s)",
                (vid, status_evento, inicio, fim),
            )

        conn.commit()

        cur.execute("SELECT COUNT(*) FROM unidades;")
        print("Unidades:", cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM viaturas;")
        print("Viaturas:", cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM equipes;")
        print("Equipes:", cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM historico_viaturas;")
        print("Histórico de viaturas:", cur.fetchone()[0])

        cur.execute("""
            SELECT regiao, disponiveis, total
            FROM (
                SELECT u.regiao,
                       SUM(CASE WHEN v.status = 'DISPONIVEL' THEN 1 ELSE 0 END) AS disponiveis,
                       COUNT(*) AS total
                FROM viaturas v JOIN unidades u ON u.id = v.unidade_id
                GROUP BY u.regiao
            ) resumo
            ORDER BY disponiveis * 1.0 / total ASC;
        """)
        print("Proporção de viaturas disponíveis por região (menor primeiro):")
        for regiao, disp, total in cur.fetchall():
            print(f"  {regiao}: {disp}/{total} ({disp/total:.0%})")

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
