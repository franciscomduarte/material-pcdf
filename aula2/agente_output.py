from agents import Agent, Runner
from pydantic import BaseModel
from provedor import configurar

configurar()

class Evento(BaseModel):
    nome: str
    data: str
    local: str
    participantes: int

agente = Agent(
    name="Executor de Eventos",
    instructions="Extraia as informações do evento a partir do texto fornecido pelo usuário",   
    output_type=Evento
)

def executar_agente_output(mensagem: str) -> Evento:
    resultado = Runner.run_sync(
        agente,
        mensagem
    )
    return resultado.final_output