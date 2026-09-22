import hashlib
from agents import Agent, Runner, function_tool
from datetime import date

REGISTROS = {}  # chave_idempotencia -> ocorrência já gravada (simula um banco)

def _chave_idempotencia(tipo: str, local: str, data: str) -> str:
    bruto = f"{tipo}|{local}|{data}".lower().strip()
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()

@function_tool
def registrar_ocorrencia(tipo: str, local: str, data: str) -> str:
    """Registra uma ocorrência.

    Args:
        tipo: tipo da ocorrência (ex.: 'furto', 'roubo').
        local: bairro ou cidade onde ocorreu.
        data: SEMPRE no formato YYYY-MM-DD. Se o usuário não informar o ano,
            use o ano corrente — nunca invente um ano diferente do atual.
    """
    print(f"[debug] tipo={tipo!r} local={local!r} data={data!r}")
    chave = _chave_idempotencia(tipo, local, data)

    if chave in REGISTROS:
        return f"Ocorrência já registrada antes (id={chave[:8]}) — nada duplicado."

    REGISTROS[chave] = {"tipo": tipo, "local": local, "data": data}
    return f"Ocorrência registrada com sucesso (id={chave[:8]})."

def montar_agente():
    hoje = date.today().isoformat()  # ex.: "2026-09-16"
    return Agent(
        name="Agente de Registro",
        instructions=(
            f"Hoje é {hoje}. Registre a ocorrência descrita pelo usuário usando a "
            "ferramenta registrar_ocorrencia. Quando o usuário não informar o ano da "
            "data, use o ano de hoje — nunca invente ou assuma outro ano."
        ),
        tools=[registrar_ocorrencia],
    )

agente = montar_agente()

r1 = Runner.run_sync(agente, "Registre um furto em Ceilândia ocorrido em 10/09/2025.")
print(r1.final_output)

r2 = Runner.run_sync(agente, "Registre de novo, por precaução, o mesmo furto em Ceilândia de 10/09.")
print(r2.final_output)

print(f"\nTotal de registros distintos no 'banco': {len(REGISTROS)}")