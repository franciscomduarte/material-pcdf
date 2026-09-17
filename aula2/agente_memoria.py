#agente_memoria.py

from agents import Agent, Runner, SQLiteSession

from provedor import configurar

configurar()

# ============================================================
# 2. CRIAÇÃO DO AGENTE
# ============================================================

agente_memoria = Agent(

    name="agente_memoria",

    instructions=(
        "Você é um agente que mantém o contexto da conversa "
        "em memória. "
        "Utilize as informações anteriores da conversa quando "
        "forem necessárias para responder às próximas perguntas. "
        "Responda com precisão e clareza."
    )
)


# ============================================================
# 3. EXECUÇÃO DO AGENTE
# ============================================================

def executar_agente_memoria(
    mensagem: str,
    sessao_id: str
) -> str:

    # Cria ou recupera a sessão.
    #
    # Se o sessao_id já existir no banco, o histórico
    # daquela conversa será recuperado.
    session = SQLiteSession(
        sessao_id,
        "conversas.db"
    )

    resultado = Runner.run_sync(
        agente_memoria,
        mensagem,
        session=session
    )

    return resultado.final_output