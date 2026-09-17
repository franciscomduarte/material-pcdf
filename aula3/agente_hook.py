from agents import Agent, Runner, RunHooks
from provedor import configurar

configurar()

class MeuHook(RunHooks):

    async def on_llm_start(
        self, # meu próprio objeto Hook
        ctx, # o contexto do agente
        agent, # o agente
        system_prompt, # o prompt do sistema
        input_items # entradas enviadas ao modelo
    ):
        print("O modelo começou a trabalhar! ")
        print(f"O agente {agent.name} começou a trabalhar!")


agente = Agent(
    name="Assistente",
    instructions="Responda de forma simples e objetiva."
)

resultado = Runner.run_sync(
    agente,
    "O que é inteligência artificial?",
    hooks=MeuHook()
)

print("Resposta:", resultado.final_output)