"""
4.2 (Desafio 1) — Saída estruturada aninhada + lista.

Enunciado: a partir de um relato livre, gerar um objeto `Ocorrencia` com tipo,
data, local, resumo e uma LISTA de envolvidos, onde cada envolvido é ele mesmo
um modelo (`Envolvido` com nome e papel). Percorrer a lista no final.

Novidade sobre o 4.1: modelos DENTRO de modelos. `list[Envolvido]` diz ao SDK
"aqui vem uma quantidade variável de pessoas, cada uma no formato Envolvido".
O modelo de linguagem monta essa estrutura sozinho a partir do texto corrido.
"""


from agents import Agent, Runner
from pydantic import BaseModel

from provedor import configurar
configurar()


class Envolvido(BaseModel):
    nome: str
    papel: str  # ex.: 'vítima', 'suspeito', 'testemunha'


class Ocorrencia(BaseModel):
    tipo: str
    data: str
    local: str
    envolvidos: list[Envolvido]   # lista de modelos aninhados
    resumo: str


agente_bo = Agent(
    name="Extrator de Ocorrências",
    instructions=(
        "Extraia os dados da ocorrência a partir do relato. "
        "Para cada pessoa citada, defina o papel (vítima, suspeito ou testemunha)."
    ),
    output_type=Ocorrencia,
)

texto = (
    "No dia 28/09, por volta das 22h10, ocorreu um furto de veículo na quadra 303 da Asa Norte, em Brasília. A vítima, Camila Rodrigues, informou que havia estacionado seu carro, um veículo de cor prata, próximo à entrada do bloco B, aproximadamente às 21h40. Ao retornar, cerca de meia hora depois, percebeu que o automóvel havia desaparecido. Nas imagens das câmeras do condomínio, segundo relato preliminar, João Martins teria sido visto caminhando próximo ao veículo. O porteiro, Antônio Ferreira, que estava trabalhando no momento da ocorrência, afirmou ter acompanhado parte da movimentação. Não houve relato de confronto ou ameaça à vítima."
)

def executar_agente_output_type(mensagem: str):
    return Runner.run_sync( agente_bo, mensagem )