import hashlib
from agents import Agent, Runner, function_tool

REGISTROS = {}  # chave_idempotencia -> ocorrência já gravada (simula um banco)

def _chave_idempotencia(tipo: str, local: str, data: str) -> str:
    bruto = f"{tipo}|{local}|{data}".lower().strip()
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()

@function_tool
def registrar_ocorrencia(tipo: str, local: str, data: str) -> str:
    """Registra uma ocorrência. Chamar duas vezes com os mesmos dados NÃO duplica o registro."""
    print(f"[debug] tipo={tipo!r} local={local!r} data={data!r}")
    chave = _chave_idempotencia(tipo, local, data)

    if chave in REGISTROS:
        return f"Ocorrência já registrada antes (id={chave[:8]}) — nada duplicado."

    REGISTROS[chave] = {"tipo": tipo, "local": local, "data": data}
    return f"Ocorrência registrada com sucesso (id={chave[:8]})."

agente = Agent(
    name="Agente de Registro",
    instructions="Registre a ocorrência descrita pelo usuário usando a ferramenta registrar_ocorrencia.",
    tools=[registrar_ocorrencia],
)

r1 = Runner.run_sync(agente, "Registre um furto em Ceilândia ocorrido em 10/09.")
print(r1.final_output)

r2 = Runner.run_sync(agente, "Registre de novo, por precaução, o mesmo furto em Ceilândia de 10/09.")
print(r2.final_output)

print(f"\nTotal de registros distintos no 'banco': {len(REGISTROS)}")