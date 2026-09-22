import asyncio
from agents import Agent, Runner, function_tool

async def precisa_aprovacao(_ctx, params, _call_id) -> bool:
    """Só exige aprovação se a palavra 'urgente' aparecer na mensagem (case-insensitive)."""
    mensagem = params.get("mensagem", "")
    return "urgente" in mensagem.lower()

@function_tool(needs_approval=precisa_aprovacao)   # ← predicado condicional, não True fixo
async def enviar_notificacao(destinatario: str, mensagem: str) -> str:
    """Envia uma notificação para um destinatário."""
    return f"Notificação enviada para {destinatario}: {mensagem!r}"

agente = Agent(
    name="Agente de Notificações",
    instructions="Envie a notificação pedida pelo usuário, usando a ferramenta enviar_notificacao.",
    tools=[enviar_notificacao],
)

async def rodar(pedido: str):
    resultado = await Runner.run(agente, pedido)

    while resultado.interruptions:                  # ← só entra aqui se ALGUMA aprovação foi pedida
        estado = resultado.to_state()                # ← congela o run pausado
        for pendencia in resultado.interruptions:
            print(f"Aprovação pedida: {pendencia.tool_name}({pendencia.arguments})")
            resposta = input("Aprovar? [s/n]: ").strip().lower()
            if resposta == "s":
                estado.approve(pendencia)
            else:
                estado.reject(pendencia)
        resultado = await Runner.run(agente, estado)  # ← retoma de onde parou

    print(resultado.final_output)

async def main():
    print("--- pedido comum (não deve pausar) ---")
    await rodar("Envie uma notificação para o João avisando que a reunião foi remarcada.")

    print("\n--- pedido urgente (deve pausar pra aprovação) ---")
    await rodar("Envie uma notificação urgente pro João: o sistema caiu.")

asyncio.run(main())