
from pydantic import BaseModel
from fastapi import FastAPI

from primeiro_agente import executar_agente
from agente_handoff import executar_agente_handoff
from agente_handoff2 import executar_agente_handoff2
from agente_output import executar_agente_output
from agente_output2 import executar_agente_output2
from agente_memoria import executar_agente_memoria


app = FastAPI()

class Pergunta(BaseModel):
    mensagem: str

class PerguntaMemoria(BaseModel):
    mensagem: str
    sessao_id: str

@app.get("/")
def inicio():
    return {
        "mensagem": "Olá mundo!"
    }

@app.post("/tools")
def perguntar_tools(pergunta: Pergunta):
    resultado = executar_agente(
        pergunta.mensagem
    )

    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }

@app.post("/handoff")
def perguntar_handoff(pergunta: Pergunta):
    resultado = executar_agente_handoff(
        pergunta.mensagem
    )

    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }

@app.post("/handoff2")
def perguntar_handoff(pergunta: Pergunta):
    resultado = executar_agente_handoff2(
        pergunta.mensagem
    )

    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }

@app.post("/output")
def perguntar_output(pergunta: Pergunta):
    resultado = executar_agente_output(
        pergunta.mensagem
    )

    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }

@app.post("/output2")
def perguntar_output(pergunta: Pergunta):
    resultado = executar_agente_output2(
        pergunta.mensagem
    )

    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }

# ============================================================
# 9. AGENTE COM MEMÓRIA
# ============================================================

@app.post("/memoria")
def perguntar_memoria(pergunta: PerguntaMemoria):

    # O sessao_id identifica qual histórico de conversa
    # deve ser utilizado pelo agente.
    resultado = executar_agente_memoria(
        pergunta.mensagem,
        pergunta.sessao_id
    )

    return {
        "sessao_id": pergunta.sessao_id,
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }