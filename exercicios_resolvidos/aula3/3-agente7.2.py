import asyncio
import time
import requests
from agents import Agent, Runner, function_tool


@function_tool
def consultar_cnpj_resiliente(cnpj: str, max_tentativas: int = 4) -> str:
    """Consulta dados cadastrais de uma empresa pelo CNPJ (BrasilAPI), com retry e backoff exponencial."""
    espera_base = 1.0  # segundos — CNPJ costuma ser mais sensível a rate limit que clima

    for tentativa in range(1, max_tentativas + 1):
        resp = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", timeout=5)

        if resp.status_code == 429:
            # só o 429 (rate limit) entra em retry — é a única falha aqui que
            # tem chance real de melhorar sozinha, esperando um pouco
            if tentativa == max_tentativas:
                raise RuntimeError(f"Rate limit da BrasilAPI persistiu após {max_tentativas} tentativas.")
            espera = espera_base * (2 ** (tentativa - 1))  # 1s, 2s, 4s, 8s...
            print(f"  [retry] 429 recebido; tentando de novo em {espera}s...")
            time.sleep(espera)
            continue

        resp.raise_for_status()  # outros erros HTTP (404, 500...) propagam direto, sem retry
        dados = resp.json()
        return f"{dados['razao_social']} — {dados['descricao_situacao_cadastral']}, {dados['municipio']}/{dados['uf']}"

    raise RuntimeError("Não deveria chegar aqui.")


@function_tool
def consultar_endereco(endereco: str) -> str:
    """Converte um endereço em coordenadas geográficas (Nominatim)."""
    resp = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": endereco, "format": "json", "limit": 1},
        headers={"User-Agent": "curso-pcdf-agente-investigacao"},
        timeout=5,
    )
    resp.raise_for_status()
    resultados = resp.json()
    if not resultados:
        raise ValueError(f"Endereço não encontrado: {endereco}")
    local = resultados[0]
    return f"lat={local['lat']}, lon={local['lon']} ({local['display_name']})"


@function_tool(needs_approval=True)
async def registrar_ocorrencia(resumo: str) -> str:
    """Registra oficialmente uma ocorrência com o resumo da investigação."""
    return f"Ocorrência registrada: {resumo}"


agente = Agent(
    name="Apoio Completo e Resiliente",
    instructions=(
        "Você apoia investigações. Consulte CNPJ e/ou endereço conforme o pedido, "
        "decidindo sozinho a ordem e quais são necessários. Só registre uma ocorrência "
        "depois de reunir os dados relevantes."
    ),
    tools=[consultar_cnpj_resiliente, consultar_endereco, registrar_ocorrencia],
)


async def main():
    pedido = (
        "Consulte o CNPJ 19131243000197 e o endereço 'Praça dos Três Poderes, Brasília' "
        "e registre uma ocorrência resumindo o que encontrou."
    )
    resultado = await Runner.run(agente, pedido)

    # o mesmo laço de aprovação da Seção 5 / 7.2
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