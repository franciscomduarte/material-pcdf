from agents import Agent, Runner, RunHooks, function_tool     # ← que classe importar pra criar hooks?
from provedor import configurar
configurar()

@function_tool
def consultar_clima(cidade: str) -> str:
    """Retorna o clima atual de uma cidade."""
    dados = {"São Paulo": "22°C, nublado", "Brasília": "28°C, sol"}
    return dados.get(cidade, "Cidade não encontrada.")

class LoopVisivel(RunHooks):                       # ← de qual classe herdar?
    turno = 0
    async def on_llm_start(self, ctx, agent, system_prompt, input_items):
        self.turno += 1
        print(f"\n--- turno {self.turno}: o modelo vai decidir ---")

    async def on_tool_start(self, ctx, agent, tool):
        print(f"  → decidiu chamar a ferramenta: {tool.name}")

    async def on_tool_end(self, ctx, agent, tool, result):
        print(f"  ← ferramenta devolveu: {result}")

agente = Agent(
    name="Assistente de Clima",
    instructions="Use a ferramenta quando perguntarem sobre o tempo.",
    tools=[consultar_clima],
)

resultado = Runner.run_sync(agente, "Como está o tempo em Brasília?", hooks=LoopVisivel())   # ← qual parâmetro liga os hooks?
print("\nResposta final:", resultado.final_output)