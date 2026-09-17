import requests

from agents import Agent, Runner, function_tool
from provedor import configurar


# =========================================================
# 1. CONFIGURAÇÃO DO PROVEDOR
# =========================================================
configurar()


# =========================================================
# 2. FERRAMENTA: TEMPERATURA
# =========================================================
@function_tool
def get_temperatura(cidade: str) -> str:
    """
    Consulta a temperatura atual de uma cidade.

    Args:
        cidade: Nome da cidade. Exemplo: Brasília.
    """

    print(f"\n[TOOL CLIMA] Consultando temperatura de: {cidade}")

    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": cidade,
                "count": 1,
                "language": "pt",
                "format": "json"
            },
            timeout=10
        )
        geo.raise_for_status()
        dados_geo = geo.json()

        if not dados_geo.get("results"):
            return f"Não encontrei a cidade '{cidade}'."

        local = dados_geo["results"][0]

        print(
            f"[TOOL CLIMA] Local encontrado: "
            f"{local['name']} "
            f"({local['latitude']}, {local['longitude']})"
        )

        clima = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": local["latitude"],
                "longitude": local["longitude"],
                "current": "temperature_2m",
                "timezone": "auto"
            },
            timeout=10
        )
        clima.raise_for_status()
        dados_clima = clima.json()

        temperatura = dados_clima["current"]["temperature_2m"]

        print(f"[TOOL CLIMA] Temperatura retornada: {temperatura} °C")

        return (
            f"A temperatura atual em {local['name']} "
            f"é {temperatura} °C."
        )

    except requests.RequestException as e:
        return f"Erro ao consultar o serviço de clima: {e}"
    except (KeyError, IndexError):
        return "Não consegui interpretar a resposta do serviço de clima."


# =========================================================
# 3. FERRAMENTA: CONVERSÃO DE MOEDAS
# =========================================================
@function_tool
def converter_moeda(
    valor: float,
    moeda_origem: str,
    moeda_destino: str
) -> str:
    """
    Converte um valor entre duas moedas.

    Args:
        valor: Valor que será convertido.
        moeda_origem: Código da moeda de origem. Exemplo: USD.
        moeda_destino: Código da moeda de destino. Exemplo: BRL.
    """

    origem = moeda_origem.upper()
    destino = moeda_destino.upper()

    print(f"\n[TOOL FINANCEIRO] Convertendo {valor} {origem} para {destino}")

    try:
        resposta = requests.get(
            f"https://api.frankfurter.dev/v2/rate/{origem}/{destino}",
            timeout=10
        )
        resposta.raise_for_status()
        dados = resposta.json()

        cotacao = dados["rate"]
        convertido = valor * cotacao

        print(f"[TOOL FINANCEIRO] Cotação: {cotacao}")

        return (
            f"{valor:.2f} {origem} = "
            f"{convertido:.2f} {destino}. "
            f"Cotação utilizada: {cotacao:.4f}."
        )

    except requests.RequestException as e:
        return f"Erro ao consultar o serviço financeiro: {e}"
    except KeyError:
        return f"Não consegui obter a cotação de {origem} para {destino}."


# =========================================================
# 4. AGENTE ESPECIALISTA EM CLIMA
# =========================================================
agente_climatico = Agent(
    name="Agente de Temperatura",

    instructions=(
        "Você é um agente especialista em temperatura atual. "
        "Quando receber uma pergunta sobre temperatura de uma cidade, "
        "utilize a ferramenta get_temperatura. "
        "A ferramenta é a fonte oficial da resposta. "
        "Não responda utilizando seu conhecimento interno. "
        "Não invente temperaturas."
    ),

    tools=[get_temperatura],
    tool_use_behavior="stop_on_first_tool"
)


# =========================================================
# 5. AGENTE ESPECIALISTA FINANCEIRO
# =========================================================
agente_financeiro = Agent(
    name="Agente Financeiro",

    instructions=(
        "Você é um agente especialista em conversão de moedas. "
        "Quando receber uma solicitação de conversão ou cotação, "
        "utilize a ferramenta converter_moeda. "
        "A ferramenta é a fonte oficial da cotação. "
        "Não utilize valores memorizados. "
        "Não invente taxas de câmbio."
    ),

    tools=[converter_moeda],
    tool_use_behavior="stop_on_first_tool"
)


# =========================================================
# 6. AGENTE TRIADOR (agora orquestrador via agents-as-tools)
# =========================================================
# Em vez de "handoff" (que transfere o controle e encerra a execução
# no especialista), os agentes especialistas são expostos como
# ferramentas do triador. Isso permite que o triador chame um, outro,
# ou os dois, e componha a resposta final combinando os resultados.
agente_triador = Agent(
    name="Agente Triador",

    instructions=(
        "Você é o agente responsável por orquestrar as respostas. "

        "A pergunta do usuário pode conter mais de um assunto. "
        "Identifique cada assunto separadamente: "

        "Se houver pergunta sobre temperatura ou clima de uma cidade, "
        "utilize a ferramenta consultar_temperatura. "

        "Se houver pergunta sobre cotação ou conversão de moedas, "
        "utilize a ferramenta consultar_conversao. "

        "Utilize quantas ferramentas forem necessárias para responder "
        "a TODOS os assuntos presentes na pergunta. "

        "Depois de obter os resultados das ferramentas, componha uma "
        "resposta final única e organizada, cobrindo cada assunto. "

        "Não invente informações. Use apenas o que as ferramentas "
        "retornarem. "

        "Se algum assunto não pertencer a nenhuma dessas áreas, "
        "informe que não existe um agente especializado disponível "
        "para esse assunto específico."
    ),

    tools=[
        agente_climatico.as_tool(
            tool_name="consultar_temperatura",
            tool_description=(
                "Consulta a temperatura atual de uma cidade. "
                "Use quando a pergunta envolver clima ou temperatura."
            )
        ),
        agente_financeiro.as_tool(
            tool_name="consultar_conversao",
            tool_description=(
                "Converte um valor entre duas moedas usando a cotação "
                "atual. Use quando a pergunta envolver câmbio ou "
                "conversão monetária."
            )
        ),
    ]
)


# =========================================================
# 7. EXECUÇÃO
# =========================================================
def main():

    pergunta = "Qual é a temperatura atual em Brasília? E quanto vale $200,00 em Reais?"

    print("\nPergunta:")
    print(pergunta)

    resultado = Runner.run_sync(
        agente_triador,
        pergunta
    )

    print("\nResposta:")
    print(resultado.final_output)

    print("\nAgente que respondeu:")
    print(resultado.last_agent.name)


if __name__ == "__main__":
    main()