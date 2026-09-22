import requests
from agents import Agent, Runner, RunHooks, function_tool

@function_tool
def consultar_cnpj(cnpj: str) -> str:
    """Consulta dados cadastrais de uma empresa pelo CNPJ (BrasilAPI)."""
    resp = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", timeout=5)
    resp.raise_for_status()
    dados = resp.json()
    return f"{dados['razao_social']} — {dados['descricao_situacao_cadastral']}, {dados['municipio']}/{dados['uf']}"

@function_tool
def consultar_ddd(ddd: str) -> str:
    """Consulta estado e municípios cobertos por um DDD (BrasilAPI)."""
    resp = requests.get(f"https://brasilapi.com.br/api/ddd/v1/{ddd}", timeout=5)
    resp.raise_for_status()
    dados = resp.json()
    return f"DDD {ddd}: {dados['state']}, municípios: {', '.join(dados['cities'][:5])}..."

class ContadorDeTurnos(RunHooks):
    turno = 0
    async def on_llm_start(self, ctx, agent, system_prompt, input_items):
        self.turno += 1
        print(f"\n--- turno {self.turno} ---")
    async def on_tool_start(self, ctx, agent, tool):
        print(f"  → decidiu consultar: {tool.name}")
    async def on_tool_end(self, ctx, agent, tool, result):
        print(f"  ← devolveu: {result}")

agente = Agent(
    name="Apoio à Investigação",
    instructions=(
        "Você apoia investigações reunindo dados cadastrais e de telefonia. "
        "Decida sozinho quais ferramentas consultar e em que ordem, conforme o que for pedido."
    ),
    tools=[consultar_cnpj, consultar_ddd],
)

def investigar(pedido: str):
    hooks = ContadorDeTurnos()
    resultado = Runner.run_sync(agente, pedido, hooks=hooks)
    print(f"\nResposta final: {resultado.final_output}")
    print(f"Total de turnos: {hooks.turno}")

investigar("Preciso saber a situação cadastral do CNPJ 19131243000197 e a cidade coberta pelo DDD 61.")