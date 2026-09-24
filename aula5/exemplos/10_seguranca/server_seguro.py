"""
Exemplo 11 -- SEGURANÇA.

Até aqui, todo MCP Server da aula só teve tools de LEITURA. Este server
adiciona uma tool de ESCRITA (alterar_status_ocorrencia) para discutir,
na prática, os controles que uma tool assim exige e que
consultar_ocorrencias() nunca precisou:

  - AUTORIZAÇÃO: exige um token de supervisor (simulado). Sem token
    válido, a chamada é recusada -- o MCP Server nega, não é o agente
    que "decide educadamente" não escrever.
  - VALIDAÇÃO: novo_status só aceita valores de um enum fechado.
  - MENOR PRIVILÉGIO: a tool só altera 1 campo (status) de 1 ocorrência
    por vez -- não existe "alterar_ocorrencias_em_lote".
  - AUDITORIA: toda tentativa (autorizada ou não) é gravada em
    auditoria.log, com quem pediu, o quê, quando e o resultado.

Rodar:
    npx @modelcontextprotocol/inspector python server_seguro.py
"""
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp-ocorrencias"))

from mcp.server.mcpserver import MCPServer

from database import query  # reaproveita o database.py do MCP Ocorrências

mcp = MCPServer("ocorrencias-seguro-mcp")

TOKEN_SUPERVISOR = os.getenv("TOKEN_SUPERVISOR", "supervisor-demo-2026")
STATUS_VALIDOS = {"REGISTRADA", "EM_ANDAMENTO", "CONCLUIDA", "ARQUIVADA"}
ARQUIVO_AUDITORIA = Path(__file__).resolve().parent / "auditoria.log"


def _registrar_auditoria(acao: str, parametros: dict, resultado: str) -> None:
    linha = f"{datetime.now().isoformat()} | acao={acao} | params={parametros} | resultado={resultado}\n"
    with open(ARQUIVO_AUDITORIA, "a", encoding="utf-8") as f:
        f.write(linha)


@mcp.tool()
def consultar_ocorrencias(regiao: str | None = None, periodo_dias: int = 30) -> list[dict]:
    """Consulta ocorrências (somente leitura). Args: regiao opcional, periodo_dias (padrão 30)."""
    condicoes = ["o.data_hora >= NOW() - (%s || ' days')::interval"]
    params: list = [periodo_dias]
    if regiao:
        condicoes.append("r.nome ILIKE %s")
        params.append(f"%{regiao}%")
    sql = f"""
        SELECT o.id, o.data_hora::text, t.codigo AS tipo, r.nome AS regiao, o.status
        FROM ocorrencias o
        JOIN tipos_ocorrencia t ON t.id = o.tipo_ocorrencia_id
        JOIN regioes r ON r.id = o.regiao_id
        WHERE {' AND '.join(condicoes)}
        ORDER BY o.data_hora DESC LIMIT 20;
    """
    return query(sql, tuple(params))


@mcp.tool()
def alterar_status_ocorrencia(
    ocorrencia_id: int,
    novo_status: str,
    motivo: str,
    token_autorizacao: str,
) -> dict:
    """[ESCRITA -- requer autorização] Altera o status de UMA ocorrência.

    Esta é uma operação sensível: toda tentativa é auditada, mesmo quando
    negada. Exige um token de supervisor válido e um motivo obrigatório.

    Args:
        ocorrencia_id: id da ocorrência a alterar.
        novo_status: um de REGISTRADA, EM_ANDAMENTO, CONCLUIDA, ARQUIVADA.
        motivo: justificativa obrigatória (fica registrada na auditoria).
        token_autorizacao: token de supervisor. Sem ele, a chamada é negada.
    """
    parametros = {"ocorrencia_id": ocorrencia_id, "novo_status": novo_status, "motivo": motivo}

    if token_autorizacao != TOKEN_SUPERVISOR:
        _registrar_auditoria("alterar_status_ocorrencia", parametros, "NEGADO: token inválido")
        return {"sucesso": False, "erro": "Token de autorização inválido. Operação negada e registrada em auditoria."}

    if novo_status not in STATUS_VALIDOS:
        _registrar_auditoria("alterar_status_ocorrencia", parametros, f"NEGADO: status inválido ({novo_status})")
        return {"sucesso": False, "erro": f"Status inválido. Use um de: {sorted(STATUS_VALIDOS)}"}

    if not motivo or not motivo.strip():
        _registrar_auditoria("alterar_status_ocorrencia", parametros, "NEGADO: motivo vazio")
        return {"sucesso": False, "erro": "Motivo é obrigatório para alterar o status de uma ocorrência."}

    # Em um sistema real: UPDATE ocorrencias SET status = %s WHERE id = %s.
    # Aqui, simulado de propósito -- o ponto da aula é o CONTROLE em volta
    # da escrita, não a escrita em si.
    _registrar_auditoria("alterar_status_ocorrencia", parametros, "AUTORIZADO (simulado)")
    return {"sucesso": True, "ocorrencia_id": ocorrencia_id, "novo_status": novo_status}


if __name__ == "__main__":
    mcp.run(transport="stdio")
