import asyncio
import requests
from agents import Agent, Runner, function_tool


@function_tool
def consultar_cnpj(cnpj: str) -> str:
    """Consulta dados cadastrais de uma empresa pelo CNPJ (BrasilAPI)."""
    resp = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", timeout=5)
    resp.raise_for_status()
    dados = resp.json()
    return f"{dados['razao_social']} — {dados['descricao_situacao_cadastral']}, {dados['municipio']}/{dados['uf']}"


@function_tool
def consultar_endereco(endereco: str) -> str:
    """Converte um endereço em coordenadas geográficas (Nominatim)."""
    resp = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": endereco, "format": "json", "limit": 1},
        headers={"User-Agent": "curso-pcdf-agente-investigacao"},  # Nominatim exige User-Agent
        timeout=5,
    )
    resp.raise_for_status()
    resultados = resp.json()
    if not resultados:
        raise ValueError(f"Endereço não encontrado: {endereco}")
    local = resultados[0]
    return f"lat={local['lat']}, lon={local['lon']} ({local['display_name']})"


@function_tool(needs_approval=True)   # ← escrita: sempre pausa pra aprovação, igual à Seção 5
async def registrar_ocorrencia(resumo: str) -> str:
    """Registra oficialmente uma ocorrência com o resumo da investigação."""
    return f"Ocorrência registrada: {resumo}"


agente = Agent(
    name="Apoio Completo à Investigação",
    instructions=(
        "Você apoia investigações. Consulte CNPJ e/ou endereço conforme o pedido, "
        "decidindo sozinho a ordem e quais são necessários. Só registre uma ocorrência "
        "depois de reunir os dados relevantes, usando registrar_ocorrencia com um resumo claro."
    ),
    tools=[consultar_cnpj, consultar_endereco, registrar_ocorrencia],
)


async def main():
    pedido = (
        "Consulte o CNPJ 19131243000197 e o endereço 'Praça dos Três Poderes, Brasília' "
        "e registre uma ocorrência resumindo o que encontrou."
    )
    resultado = await Runner.run(agente, pedido)

    # o mesmo laço de aprovação da Seção 5 — só a última ferramenta (a escrita) pausa
    while resultado.interruptions:
        estado = resultado.to_state()
        for pendencia in resultado.interruptions:
            print(f"Aprovação pedida: {pendencia.tool_name}({pendencia.arguments})")
            resposta = input("Aprovar? [s/n]: ").strip().lower()
            if resposta == "s":
                estado.approve(pendencia)
            else:
                estado.reject(pendencia)
        resultado = await Runner.run(agente, estado)

    print(f"\nResposta final: {resultado.final_output}")


asyncio.run(main())