"""
Exemplo 02 -- PRIMEIRO MCP SERVER.

Mesma capacidade do Exemplo 01 (consultar ocorrências), mas agora ela não
mora mais dentro do processo do agente. Ela é um PROCESSO SEPARADO, que
fala o protocolo MCP. Qualquer agente, em qualquer linguagem, que souber
falar MCP, pode usar esta tool -- sem importar nenhum .py nosso.

Uma única ferramenta, SEM parâmetros (de propósito -- vamos adicionar
parâmetros no Exemplo 03).

Rodar sozinho com o MCP Inspector (não precisa de agente para isso):
    npx @modelcontextprotocol/inspector python server.py

Rodar "cru" (o processo fica esperando mensagens MCP via stdin/stdout --
não tem saída visível, é normal, é assim que stdio funciona):
    python server.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # aula5/ (provedor.py)

from mcp.server.mcpserver import MCPServer
from agents import Agent, Runner
from database import query
from provedor import configurar

configurar()

mcp = MCPServer("ocorrencias-mcp")

@mcp.tool()
def consultar_ocorrencias_natural(pergunta: str) -> list[dict]:
    """
    Consulta ocorrências da CISP a partir de uma pergunta em linguagem natural.

    Exemplos:
    - "Quais foram as 20 ocorrências mais recentes?"
    - "Quais ocorrências graves aconteceram hoje?"
    - "Mostre ocorrências em andamento da Região Alfa"
    """
      
    sql = gerar_sql(pergunta)

    print(f"SQL gerado: {sql}", file=sys.stderr)

    return query(sql)

def gerar_sql(pergunta: str) -> str:
    """
    Converte uma pergunta em linguagem natural
    para uma consulta SQL PostgreSQL.
    """

    agente = Agent(
        name="Gerador SQL",
        instructions="""
        Você é um especialista em PostgreSQL.

        Sua função é transformar perguntas em linguagem natural
        em consultas SQL.

        Estrutura do banco:

        Tabela ocorrencias:
            id
            data_hora
            tipo_ocorrencia_id
            regiao_id
            gravidade
            status

        Tabela tipos_ocorrencia:
            id
            nome

        Tabela regioes:
            id
            nome

        Valores reais das colunas (use EXATAMENTE estes, em maiúsculas):

        ocorrencias.status: REGISTRADA, EM_ANDAMENTO, CONCLUIDA, ARQUIVADA
            ("abertas" = REGISTRADA ou EM_ANDAMENTO)
        ocorrencias.gravidade: BAIXA, MEDIA, ALTA, CRITICA
            ("graves" = ALTA ou CRITICA)
        regioes.nome: "Região Alfa", "Região Bravo", "Região Charlie", ...
            (alfabeto fonético; para filtrar use ILIKE '%alfa%', nunca "Norte")
        tipos_ocorrencia.nome: Furto, Roubo, Roubo de Veículo, Homicídio,
            Lesão Corporal, Tráfico de Entorpecentes, Violência Doméstica,
            Perturbação do Sossego, Dano ao Patrimônio Público,
            Acidente de Trânsito

        Os dados vão de 2025-09-22 a 2026-09-21. Para "hoje" ou "recentes",
        não filtre por CURRENT_DATE: use ORDER BY data_hora DESC.

        Relacionamentos:

        ocorrencias.tipo_ocorrencia_id -> tipos_ocorrencia.id
        ocorrencias.regiao_id -> regioes.id

        Regras:

        1. Gere somente comandos SELECT.
        2. Nunca faça INSERT, UPDATE, DELETE ou DROP.
        3. Utilize somente as tabelas e campos apresentados.
        4. Utilize JOIN quando necessário.
        4.1. NUNCA use SELECT *. Selecione somente estas colunas, com alias:
             o.id, o.data_hora, t.nome AS tipo, r.nome AS regiao,
             o.gravidade, o.status (faça JOIN com tipos_ocorrencia t e
             regioes r). Só inclua outras colunas se a pergunta pedir.
        5. Sempre limite o resultado a no máximo 20 registros.
        6. Ordene as ocorrências mais recentes primeiro quando fizer sentido.
        7. Retorne SOMENTE o SQL.
        8. Não coloque o SQL dentro de ```sql.
        """
    )

    resultado = Runner.run_sync(
        agente,
        pergunta
    )

    return resultado.final_output.strip()

if __name__ == "__main__":
    mcp.run(transport="stdio")
