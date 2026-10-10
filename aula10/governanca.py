"""
🆕 B -- Hooks para CONTROLAR, não só para observar (Etapa 6, 10 min). Volta aqui na ETAPA 10.1 (observabilidade).

Conceito que você já conhece: em aula3/agente_hook2.py e aula3/agente_loop.py os RunHooks só IMPRIMIAM
("turno 2", "chamou a ferramenta X"). Contexto novo: o mesmo gancho roda ANTES de cada tool (on_tool_start) e
ANTES de cada chamada ao modelo (on_llm_start) -- então ele pode BARRAR a execução. Não há exemplo pronto disto.

ESQUELETO:
  🆕 B.1 -- PERMISSOES: quais tools cada agente pode chamar
  🆕 B.2 -- on_tool_start: tool fora da lista do agente OU orçamento de tools estourado -> LimiteExcedido
  🆕 B.3 -- on_llm_start: orçamento de chamadas ao modelo estourado -> LimiteExcedido
  ETAPA 10.1 -- on_tool_end / on_agent_end: registre tool, argumentos, resultado e tokens (o MESMO hook, outro papel)

REFERÊNCIAS NAS AULAS
  aula3/agente_hook2.py, aula3/agente_hook3.py   a assinatura dos métodos de RunHooks (on_llm_start, on_tool_start...)
  aula3/agente_loop.py                           o hook contando turnos e tools do loop do agente
  aula8/exemplos/06_excessive_agency/1_codigo_pronto/main.py   o risco que a lista de permissões evita

Por que funciona: o SDK chama on_tool_start ANTES de executar a tool. Uma exceção levantada ali interrompe o
Runner e a tool NÃO roda. Trate LimiteExcedido em volta do Runner (etapa6_linear.py). Dois detalhes do SDK:
  1. LimiteExcedido herda de AgentsException. Se herdasse de Exception, o SDK a embrulharia num UserError
     ("Error running tool ...") e o seu `except LimiteExcedido` não a pegaria.
  2. Dentro de um especialista chamado via as_tool, o SDK, por padrão, transforma QUALQUER erro em uma mensagem
     de texto para o Coordenador, e a execução continua: o bloqueio seria engolido. Por isso, em
     agentes.criar_coordenador(), as as_tool recebem failure_error_function=None (o erro sobe de verdade).
"""
from agents import AgentsException, RunHooks


class LimiteExcedido(AgentsException):
    """Levantada pelo hook quando um agente sai do que lhe é permitido."""


# 🆕 B.1 -- agente -> conjunto de nomes de tools permitidas.
#   Os especialistas usam as tools de agentes.py; o Coordenador só chama os especialistas (os tool_name das as_tool).
#   O salário (consultar_remuneracao) só pode passar pelo Financeiro.
PERMISSOES: dict[str, set[str]] = {
    # "Normas": {"consultar_normas"},
    # TODO 🆕 B.1: complete para Escala, Financeiro e Coordenador
}


class Governanca(RunHooks):
    def __init__(self, max_tools: int = 6, max_llm: int = 12, verbose: bool = True):
        self.max_tools, self.max_llm, self.verbose = max_tools, max_llm, verbose
        self.tools_chamadas = 0
        self.chamadas_llm = 0
        self.eventos: list[dict] = []  # ETAPA 10.1: o que aconteceu, para gravar em saidas/metricas.jsonl

    async def on_tool_start(self, context, agent, tool) -> None:
        # 🆕 B.2 -- conte a chamada; levante LimiteExcedido se:
        #   - tool.name não está em PERMISSOES.get(agent.name, set())   -> "Coordenador não pode usar consultar_remuneracao"
        #   - self.tools_chamadas > self.max_tools                       -> "orçamento de tools estourado (N de M)"
        #   Imprima a decisão quando self.verbose (ex.: "[governança] Financeiro -> tabela_diarias: OK").
        raise NotImplementedError("🆕 B.2: on_tool_start")

    async def on_llm_start(self, context, agent, system_prompt, input_items) -> None:
        # 🆕 B.3 -- conte a chamada ao modelo; acima de self.max_llm, levante LimiteExcedido.
        #   (Parece o max_turns da Etapa 4.7, mas a mensagem e o registro são SEUS, e vale para a equipe toda.)
        raise NotImplementedError("🆕 B.3: on_llm_start")

    async def on_tool_end(self, context, agent, tool, result) -> None:
        # ETAPA 10.1 -- acrescente a self.eventos: {"agente", "tool", "argumentos", "resultado" (truncado)}.
        #   Os argumentos estão em context.tool_arguments (texto JSON) quando a tool é uma function_tool.
        pass

    async def on_agent_end(self, context, agent, output) -> None:
        # ETAPA 10.1 -- acrescente a self.eventos os tokens até aqui: context.usage.total_tokens
        pass
