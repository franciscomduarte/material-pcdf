from agents import Agent, Runner, SQLiteSession
from pydantic import BaseModel
from provedor import configurar

configurar()

agente = Agent( 
    name="agente_memoria",
    instructions=("Você é um agente que mantém o contexto da conversa em memória. Responda com precisão")
)

    # ← o objeto de memória (sem db_path = RAM)

def main():
    sessao = SQLiteSession("conversa_do_molina", db_path="conversa_do_molina.db")  # ← o objeto de memória (com db_path = arquivo)

    r1 = Runner.run_sync(agente, "Qual a capital da França?", session=sessao)
    print(r1.final_output)
    r2 = Runner.run_sync(agente, "E quantos habitantes ela tem?", session=sessao)
    print(r2.final_output)

main()