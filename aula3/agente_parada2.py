from pydantic import BaseModel
from agents import Agent, Runner, SQLiteSession

from provedor import configurar
configurar()

class StatusInvestigacao(BaseModel):
    resumo: str
    concluido: bool

agente = Agent(
    name="Investigador",
    instructions=(
        "Você está reunindo informações sobre um caso aos poucos, uma mensagem por vez. "
        "A cada rodada, resuma o que já sabe e marque concluido=True quando achar que já tem "
        "pelo menos nome, local e data do caso."
    ),
    output_type=StatusInvestigacao,
)


def investigar(mensagens_do_usuario: list[str], max_rodadas: int = 8):
    sessao = SQLiteSession("investigacao_002")
    confirmacoes_seguidas = 0
    ultimo_status = None

    for rodada, msg in enumerate(mensagens_do_usuario, start=1):
        resultado = Runner.run_sync(agente, msg, session=sessao)
        status = resultado.final_output
        print(f"Rodada {rodada}: concluido={status.concluido} — {status.resumo}")
        ultimo_status = status

        if status.concluido:
            confirmacoes_seguidas += 1
        else:
            confirmacoes_seguidas = 0  # qualquer "False" reseta a contagem

        if confirmacoes_seguidas >= 2:
            print(f"\nConfirmado em 2 rodadas seguidas — parando na rodada {rodada}.")
            return status

        if rodada == max_rodadas:
            raise RuntimeError("Não confirmou conclusão dentro do limite de rodadas.")

    return ultimo_status  # esgotou a lista sem 2 confirmações seguidas


investigar([
    "Recebemos uma denúncia sobre um caso em Taguatinga.",
    "Foi na semana passada, terça-feira.",
    "A vítima se chama João Silva.",
    "Na verdade não foi terça, foi quarta-feira mesmo.",
])