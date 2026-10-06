"""
agentes.py -- os agentes da Aula 7 (já prontos), usados a partir do exemplo 03.

Cada especialista é um `Agent(name=..., instructions=...)`, como nas Aulas 1 a 4. Quem o executa é o `Runner`:

    resultado = Runner.run_sync(agentes.investigador, "texto de entrada")
    resultado.final_output      # o texto que o agente respondeu

Nos exemplos 01 e 02 você escreve os agentes à mão; daqui em diante eles já vêm prontos e o foco passa a ser o
ESTADO que circula entre eles e o GRAFO que os liga. As instruções estão em prompts.py.
"""
from agents import Agent, ModelSettings

import prompts

# temperature=0: respostas mais estáveis (os testes dos desafios conferem o caminho do grafo, não o texto).
CONFIG = ModelSettings(temperature=0, max_tokens=700)

investigador = Agent(name="Investigador", instructions=prompts.INSTR_INVESTIGADOR, model_settings=CONFIG)
juridico = Agent(name="Juridico", instructions=prompts.INSTR_JURIDICO, model_settings=CONFIG)
risco = Agent(name="Analista de risco", instructions=prompts.INSTR_RISCO, model_settings=CONFIG)
redator = Agent(name="Redator da recomendacao", instructions=prompts.INSTR_REDATOR, model_settings=CONFIG)
comunicacao = Agent(name="Comunicacao", instructions=prompts.INSTR_COMUNICACAO, model_settings=CONFIG)
classificador = Agent(name="Classificador de risco", instructions=prompts.INSTR_CLASSIFICADOR, model_settings=CONFIG)
conformidade = Agent(name="Conformidade", instructions=prompts.INSTR_CONFORMIDADE, model_settings=CONFIG)
