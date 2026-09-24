"""
Exemplo 02.1 -- MCP 100% EM LINGUAGEM NATURAL.

No Exemplo 02 a pergunta entrava em português, mas a resposta voltava como
LINHAS de tabela (JSON). Aqui a tool fala português nos DOIS sentidos:

    pergunta em português  ->  resposta em português

Por dentro, o server faz três passos (e só ele os conhece):

    1. GERAR   um agente escreve o SQL a partir da pergunta
    2. EXECUTAR o SQL, depois de validado, em uma conexão SOMENTE LEITURA
    3. REDIGIR  um segundo agente transforma as linhas em uma resposta em texto

Para quem chama (agente, Inspector, cliente), existe UMA tool com UM texto de
entrada e UM texto de saída: nenhum SQL, nenhuma tabela.

Rodar sozinho com o MCP Inspector:
    npx @modelcontextprotocol/inspector python server.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # aula5/ (provedor.py)

import psycopg2.extras
from agents import Agent, Runner
from mcp.server.mcpserver import MCPServer

from database import conectar
from provedor import configurar

configurar()

sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # o log do server sempre em UTF-8

mcp = MCPServer("ocorrencias-natural-mcp")

LIMITE_LINHAS = 50

# ----------------------------------------------------------------------------
# Passo 1 -- GERAR o SQL
# ----------------------------------------------------------------------------
INSTRUCOES_SQL = """
Você é um especialista em PostgreSQL. Transforme a pergunta do usuário em UMA
consulta SQL. Responda SOMENTE com o SQL, sem explicações e sem ```.

Estrutura do banco:

  ocorrencias(id, data_hora, tipo_ocorrencia_id, regiao_id, gravidade, status)
  tipos_ocorrencia(id, nome)
  regioes(id, nome)

  ocorrencias.tipo_ocorrencia_id -> tipos_ocorrencia.id
  ocorrencias.regiao_id          -> regioes.id

Valores reais das colunas (use EXATAMENTE estes, em maiúsculas):

  ocorrencias.status:    REGISTRADA, EM_ANDAMENTO, CONCLUIDA, ARQUIVADA
                         ("abertas" = REGISTRADA ou EM_ANDAMENTO)
  ocorrencias.gravidade: BAIXA, MEDIA, ALTA, CRITICA
                         ("graves" = ALTA ou CRITICA)
  regioes.nome:          "Região Alfa", "Região Bravo", "Região Charlie", ...
                         (alfabeto fonético; filtre com ILIKE '%alfa%', nunca "Norte")
  tipos_ocorrencia.nome: Furto, Roubo, Roubo de Veículo, Homicídio, Lesão Corporal,
                         Tráfico de Entorpecentes, Violência Doméstica,
                         Perturbação do Sossego, Dano ao Patrimônio Público,
                         Acidente de Trânsito

Os dados vão de 2025-09-22 a 2026-09-21. Para "hoje", "ontem" ou "recentes", não
use CURRENT_DATE: use ORDER BY data_hora DESC, ou datas dentro desse intervalo.

Regras:
  1. Somente SELECT (ou WITH ... SELECT). Uma única consulta, sem ponto e vírgula no meio.
  2. Nunca use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE ou GRANT.
  3. Use somente as tabelas e colunas acima.
  4. Perguntas de contagem, ranking ou comparação: use COUNT e GROUP BY.
     Perguntas de lista: selecione o.id, o.data_hora, t.nome AS tipo,
     r.nome AS regiao, o.gravidade, o.status (nunca SELECT *).
  4.1. Em contagens e rankings, agrupe e mostre o NOME (t.nome, r.nome), nunca o id.
  5. NÃO use LIMIT, a não ser que a pergunta peça uma quantidade (por exemplo, "as 5 mais
     recentes"). O limite de linhas é aplicado pelo sistema.
  6. Se a pergunta não puder ser respondida com essas tabelas, responda apenas: IMPOSSIVEL
"""

# ----------------------------------------------------------------------------
# Passo 3 -- REDIGIR a resposta
# ----------------------------------------------------------------------------
INSTRUCOES_REDATOR = """
Você redige respostas para operadores da CISP (Central Integrada de Segurança Pública).

Você recebe uma PERGUNTA, as LINHAS que o banco devolveu e um indicador "truncado". Responda em português,
de forma direta e curta.

Regras:
  - Use SOMENTE os dados das linhas. Não invente números, nomes nem datas.
  - Se não houver linhas, diga que não encontrou registros para essa pergunta.
  - Se "truncado" for true, o banco tinha MAIS linhas do que você recebeu: NUNCA diga
    que o total é o número de linhas recebidas. Diga que há mais registros e que a
    resposta considera só os primeiros.
  - Para listas longas, resuma (quantidade e os itens mais relevantes).
  - Lembre que os dados cobrem de 22/09/2025 a 21/09/2026.
  - Não mostre SQL nem nomes de colunas técnicos.
"""

PALAVRAS_PROIBIDAS = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|call|do|execute)\b",
    re.IGNORECASE,
)


# ----------------------------------------------------------------------------
# Passo 2 -- VALIDAR e EXECUTAR (somente leitura)
# ----------------------------------------------------------------------------
def validar_sql(sql: str) -> str | None:
    """Devolve o motivo da recusa, ou None se o SQL é aceitável."""
    corpo = sql.strip().rstrip(";").strip()
    if not corpo:
        return "SQL vazio"
    if ";" in corpo:
        return "mais de um comando"
    if not re.match(r"(?is)^(select|with)\b", corpo):
        return "não começa com SELECT/WITH"
    if PALAVRAS_PROIBIDAS.search(corpo):
        return "contém comando de escrita"
    return None


def executar_somente_leitura(sql: str) -> tuple[list[dict], bool]:
    """Executa em uma sessão READ ONLY: mesmo que o SQL escape da validação, o banco recusa escrita.

    Devolve (linhas, truncado). Lê uma linha a mais que o limite só para saber se
    o resultado foi cortado: o redator precisa dessa informação para não afirmar
    um total que ele não viu.
    """
    conn = conectar()
    try:
        conn.set_session(readonly=True)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # O limite é imposto AQUI, por fora do SQL do LLM: assim sabemos se houve corte.
            corpo = sql.strip().rstrip(";")
            cur.execute(f"SELECT * FROM ({corpo}) AS q LIMIT {LIMITE_LINHAS + 1}", None)
            linhas = [dict(l) for l in cur.fetchall()]
            return linhas[:LIMITE_LINHAS], len(linhas) > LIMITE_LINHAS
    finally:
        conn.close()


def _texto(agente: Agent, entrada: str) -> str:
    return Runner.run_sync(agente, entrada).final_output.strip()


@mcp.tool()
def perguntar_ocorrencias(pergunta: str) -> str:
    """Responde, em português, perguntas sobre as ocorrências da CISP.

    Recebe uma pergunta em linguagem natural e devolve uma resposta em texto.
    Serve para contagens, rankings e listas (por região, tipo, gravidade, status).

    Exemplos:
    - "Quantas ocorrências graves aconteceram na Região Bravo?"
    - "Quais os tipos de ocorrência mais comuns?"
    - "Mostre as 5 ocorrências abertas mais recentes."

    Args:
        pergunta: a pergunta, em português, sobre as ocorrências.
    """
    # 1. GERAR
    sql = _texto(Agent(name="Gerador SQL", instructions=INSTRUCOES_SQL), pergunta)
    sql = re.sub(r"^```(?:sql)?|```$", "", sql, flags=re.MULTILINE).strip()
    print(f"[02.1] SQL gerado: {' '.join(sql.split())}", file=sys.stderr)

    if sql.upper().startswith("IMPOSSIVEL"):
        return "Não consigo responder a essa pergunta com os dados de ocorrências disponíveis."

    # 2. VALIDAR + EXECUTAR
    motivo = validar_sql(sql)
    if motivo:
        print(f"[02.1] SQL recusado: {motivo}", file=sys.stderr)
        return "Não consegui montar uma consulta segura para essa pergunta. Tente reformulá-la."
    try:
        linhas, truncado = executar_somente_leitura(sql)
    except Exception as erro:
        print(f"[02.1] erro ao executar: {erro}", file=sys.stderr)
        return "Não consegui consultar os dados para essa pergunta. Tente reformulá-la."
    print(f"[02.1] {len(linhas)} linha(s){' (TRUNCADO)' if truncado else ''}", file=sys.stderr)

    # 3. REDIGIR
    entrada = json.dumps({"pergunta": pergunta, "linhas": linhas, "truncado": truncado},
                         ensure_ascii=False, default=str)
    return _texto(Agent(name="Redator", instructions=INSTRUCOES_REDATOR), entrada)


if __name__ == "__main__":
    mcp.run(transport="stdio")
