from datetime import date
from agents import Agent, Runner

DIAS_PT = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
           "sexta-feira", "sábado", "domingo"]

# --- versão ingênua: o modelo tem que ADIVINHAR a data ---
agente_ruim = Agent(
    name="Assistente",
    instructions="Responda as perguntas do usuário.",
)
r1 = Runner.run_sync(agente_ruim, "Que dia da semana é hoje?")
# resposta plausível, mas baseada em nada real — o modelo não tem relógio

print("\n\n---\n\n")
print(r1.final_output)

# --- versão corrigida: a data real é INJETADA nas instructions ---
hoje = date.today()
texto_hoje = f"{DIAS_PT[hoje.weekday()]}, {hoje.strftime('%d/%m/%Y')}"

agente_bom = Agent(
    name="Assistente",
    instructions=f"Hoje é {texto_hoje}. Responda as perguntas do usuário considerando essa data real.",
)
r2 = Runner.run_sync(agente_bom, "Que dia da semana é hoje?")
# agora a resposta é calculada a partir de um fato, não de um palpite

print("\n\n---\n\n")
print(r2.final_output)
