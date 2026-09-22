"""
5.1 — Memória de conversa (Session).

Problema: cada `Runner.run_sync` é, por padrão, SEM MEMÓRIA. O 2º turno não sabe
nada do 1º. Para um chat multi-turno isso não serve.

Solução: `SQLiteSession(id)`. É um objeto que guarda o histórico da conversa
(perguntas, respostas e até resultados de ferramentas) e reinjeta esse
histórico a cada nova chamada. Basta passar `session=...` no Runner.

- O `id` ("conversa_do_jr") identifica a conversa. Mesmo id => mesma memória.
- Por padrão a memória é EM MEMÓRIA RAM (`:memory:`): vale só enquanto o programa
  roda; ao fechar, some. Para gravar em arquivo e sobreviver ao reinício, veja 5.5.
- No 2º turno usamos "ela" sem dizer "Paris" — o agente resolve pelo histórico.
"""


from pathlib import Path
from agents import Agent, Runner, SQLiteSession
from agents.memory import Session

from provedor import configurar
configurar()

agente = Agent(
    name="Assistente",
    instructions="Responda de forma concisa, em português.",
)


def main():
    # A sessão guarda o histórico sob um identificador.
    # Sem `db_path`, o SQLite fica só na RAM: a memória morre quando o script termina.
    #sessao = SQLiteSession("conversa_do_jr", db_path="C:\\projetos\\testes\\file.json")

    sessao = Session(
        session_id="conversa_do_jr",
        file_path="C:/projetos/testes/conversa.json"
    )

    # 1º turno
    r1 = Runner.run_sync(agente, "Qual a capital da França?", session=sessao)
    print(r1.final_output)  # "Paris"

    # 2º turno — repare que não repito "França" nem "capital".
    # O agente recebe todo o histórico da `sessao` e entende que "ela" = Paris.
    r2 = Runner.run_sync(agente, "E quantos habitantes ela tem?", session=sessao)
    print(r2.final_output)


main()