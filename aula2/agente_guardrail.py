
import asyncio

from pydantic import BaseModel, Field
from agents import (
    Agent,
    Runner,
    RunContextWrapper,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    TResponseInputItem,
    input_guardrail,
)

from provedor import configurar

configurar()


# ---------------------------------------------------------------------------
# 1. Schema de saída do agente classificador
# ---------------------------------------------------------------------------
class TopicCheckOutput(BaseModel):
    similaridade: float = Field(
        description=(
            "Score de 0.0 a 1.0 indicando o quão semanticamente próximo "
            "o input está de tópicos proibidos (receitas, futebol, fofoca). "
            "0.0 = totalmente sobre programação/dev. "
            "1.0 = totalmente sobre o tópico proibido."
        )
    )
    motivo: str = Field(description="Breve justificativa da nota dada")


# ---------------------------------------------------------------------------
# 2. Agente classificador (o "cérebro" do guardrail)
# ---------------------------------------------------------------------------
guardrail_agent = Agent(
    name="Topic Similarity Guardrail",
    instructions=(
        "Você avalia o quão semanticamente relacionado o input do usuário está "
        "a tópicos proibidos: receitas culinárias, futebol, fofoca de celebridades. "
        "Dê uma nota de 0.0 a 1.0 considerando o SENTIDO da mensagem, não apenas "
        "palavras-chave isoladas. Por exemplo, uma pergunta sobre como programar "
        "um scraper que coleta resultados de futebol deve ter nota baixa (é sobre "
        "programação), mesmo mencionando a palavra 'futebol'. Já uma pergunta "
        "pedindo a escalação do jogo de hoje deve ter nota alta."
    ),
    output_type=TopicCheckOutput,
)

LIMIAR = 0.7  # ajuste conforme falsos positivos/negativos observados


# ---------------------------------------------------------------------------
# 3. Função guardrail em si
# ---------------------------------------------------------------------------
@input_guardrail
async def bloquear_off_topics(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    resultado = await Runner.run(guardrail_agent, input, context=ctx.context)
    saida = resultado.final_output_as(TopicCheckOutput)

    return GuardrailFunctionOutput(
        output_info={
            "similaridade": saida.similaridade,
            "motivo": saida.motivo,
        },
        tripwire_triggered=saida.similaridade >= LIMIAR,
    )


# ---------------------------------------------------------------------------
# 4. Agente principal, protegido pelo guardrail
# ---------------------------------------------------------------------------
agente_principal = Agent(
    name="Assistente de Programação",
    model="gpt-4o-mini",
    instructions=(
        "Você é um assistente especializado em programação e desenvolvimento "
        "de software. Responda de forma clara e objetiva, com exemplos de "
        "código quando fizer sentido."
    ),
    input_guardrails=[bloquear_off_topics],
)


# ---------------------------------------------------------------------------
# 5. Loop de execução / demo
# ---------------------------------------------------------------------------
async def perguntar(pergunta: str) -> None:
    print(f"\n>>> Pergunta: {pergunta}")
    try:
        resultado = await Runner.run(agente_principal, pergunta)
        print(f"Resposta: {resultado.final_output}")
    except InputGuardrailTripwireTriggered as e:
        # e.guardrail_result.output.output_info contém o dict que retornamos
        info = e.guardrail_result.output.output_info
        print(
            f"[BLOQUEADO] similaridade={info['similaridade']:.2f} "
            f"| motivo: {info['motivo']}"
        )


async def main() -> None:
    perguntas = [
        "Como faço um decorator em Python que mede o tempo de execução?",
        "Qual a melhor receita de bolo de chocolate?",
        "Como faço um scraper em Python pra pegar resultados de futebol?",
        "Quem ganhou o jogo do Brasil ontem?",
        "Me conta uma fofoca de celebridade.",
    ]

    for p in perguntas:
        await perguntar(p)


if __name__ == "__main__":
    asyncio.run(main())