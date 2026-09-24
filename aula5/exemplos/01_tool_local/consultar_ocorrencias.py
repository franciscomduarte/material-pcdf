"""
Exemplo 01 -- O PROBLEMA SEM MCP.

Uma tool Python "tradicional": uma função comum, chamada diretamente
pelo agente via function calling (como vocês já viram na Aula 4).

Não há banco de verdade aqui ainda -- só uma lista fixa em memória --
porque o ponto desta etapa não é a fonte de dados, é o ACOPLAMENTO:
o agente e a implementação da tool moram no mesmo processo, no mesmo
arquivo, na mesma linguagem.

Rode este arquivo sozinho (sem agente) para ver a função funcionando:
    python consultar_ocorrencias.py
"""

OCORRENCIAS_FICTICIAS = [
    {"id": 1, "tipo": "ROUBO", "regiao": "Região Bravo", "gravidade": "ALTA", "status": "EM_ANDAMENTO"},
    {"id": 2, "tipo": "FURTO", "regiao": "Região Alfa", "gravidade": "BAIXA", "status": "CONCLUIDA"},
    {"id": 3, "tipo": "ROUBO_VEICULO", "regiao": "Região Kilo", "gravidade": "ALTA", "status": "REGISTRADA"},
    {"id": 4, "tipo": "ROUBO_VEICULO", "regiao": "Região Delta", "gravidade": "ALTA", "status": "REGISTRADA"},
]


def consultar_ocorrencias() -> list[dict]:
    """Retorna as ocorrências mais recentes (dados fictícios, em memória)."""
    return OCORRENCIAS_FICTICIAS


if __name__ == "__main__":
    for ocorrencia in consultar_ocorrencias():
        print(ocorrencia)
