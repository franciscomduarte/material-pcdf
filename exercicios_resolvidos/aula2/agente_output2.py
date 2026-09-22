from agents import Agent, Runner
from pydantic import BaseModel, Field
from provedor import configurar
from enum import Enum

configurar()

class PapelEnvolvido(str, Enum):
    VITIMA = "vítima"
    SUSPEITO = "suspeito"
    TESTEMUNHA = "testemunha"
    COMUNICANTE = "comunicante"

class Envolvido(BaseModel):
    nome: str = Field(
        description="Nome completo da pessoa citada na ocorrência."
    )
    papel: PapelEnvolvido = Field(
        description=(
            "Papel do envolvido no fato: "
            "'vítima' (quem sofreu a ação patrimonial ou física), "
            "'suspeito' (autor ou investigado da conduta), "
            "'testemunha' (presenciou os fatos), ou "
            "'comunicante' (apenas reportou o fato sem ter presenciado)."
        )
    )

class Ocorrencia(BaseModel):
    tipo: str = Field(
        description="Tipificação resumida da ocorrência (ex.: 'Furtos', 'Roubo', 'Ameaça')."
    )
    data: str = Field(
        description="Data aproximada ou exata do fato (ex.: 'YYYY-MM-DD' ou texto relativo)."
    )
    local: str = Field(
        description="Endereço ou ponto de referência do local do fato."
    )
    objetos: list[str] = Field(
        description="Lista de todos os objetos envolvidos na ocorrência e que sejam relevantes para os fatos descritos."
    )
    envolvidos: list[Envolvido] = Field(
        description="Lista de todas as pessoas mencionadas na ocorrência com seus respetivos papéis."
    )
    resumo: str = Field(
        description="Síntese factual da narrativa constante na ocorrência."
    )

agente_bo = Agent(
    name="Executor de Ocorrências",
    instructions=(
        "Extraia os dados da ocorrência a partir do relato. "
        "Para cada pessoa citada, defina o papel (vítima, suspeito ou testemunha)."
    ),
    output_type=Ocorrencia
)

def executar_agente_output2(mensagem: str):
    resultado = Runner.run_sync(
        agente_bo,
        mensagem
    )
    return resultado.final_output