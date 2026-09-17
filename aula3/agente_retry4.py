import requests
from agents import Agent, Runner, function_tool
from provedor import configurar

configurar()

# --- versão ingênua: pergunta direto pro modelo, sem nenhuma fonte real ---
agente_ruim = Agent(
    name="Assistente Financeiro",
    instructions="Responda as perguntas do usuário sobre câmbio.",
)
resultado_ruim = Runner.run_sync(agente_ruim, "Quanto está o dólar em reais hoje?")
print(resultado_ruim.final_output)
# saída de exemplo: "O dólar está cotado em aproximadamente R$ 5,00 hoje."
# (número plausível, mas "congelado" no tempo do treinamento — pode estar bem defasado)

# --- versão corrigida: uma ferramenta consulta a cotação REAL, agora ---
@function_tool
def consultar_cotacao(moeda_origem: str, moeda_destino: str) -> float:
    """Consulta a cotação atual entre duas moedas (ex.: USD -> BRL).

    Args:
        moeda_origem: código de 3 letras da moeda de origem (ex.: 'USD').
        moeda_destino: código de 3 letras da moeda de destino (ex.: 'BRL').
    """
    resposta = requests.get(
        "https://api.frankfurter.app/latest",
        params={"from": moeda_origem, "to": moeda_destino},
        timeout=3,
    )
    resposta.raise_for_status()   # detecta erro HTTP cedo, antes de tentar ler o JSON
    dados = resposta.json()
    return dados["rates"][moeda_destino]   # o valor real, consultado agora — não um palpite

agente_bom = Agent(
    name="Assistente Financeiro",
    instructions="Use a ferramenta consultar_cotacao para responder sobre câmbio. Nunca chute um valor de cabeça.",
    tools=[consultar_cotacao],
)
resultado_bom = Runner.run_sync(agente_bom, "Quanto está o dólar em reais hoje?")
print(resultado_bom.final_output)
# saída de exemplo: "1 USD equivale a R$ 5,42 hoje."
# (valor batendo com a cotação real do dia — veio da API, não de um palpite)