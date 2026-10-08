"""Exemplo 03 (ponto de partida) -- agente com tool que responde várias perguntas.
Funciona, mas é uma caixa-preta: não sabemos quanto cada pergunta demorou, quantos tokens gastou,
nem se a tool foi chamada. Durante a aula vamos DAR VISIBILIDADE a isso."""
import sys
from pathlib import Path
from time import sleep

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agents import Agent, RunHooks, Runner, function_tool

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

from base.provedor import configurar

# --- 1a. um "exportador" que imprime cada span que termina: nome, duração, trace_id, span_id, erro ---
class ResumoNoConsole(SpanExporter):
    def export(self, spans):
        for s in spans:
            ms = (s.end_time - s.start_time) / 1_000_000  # microssegundos -> milissegundos
            erro = "ERRO" if s.attributes.get("erro") else ""
            print(f"[span] {s.name} {ms:.1f}ms {erro} trace_id={s.context.trace_id:x} span_id={s.context.span_id:x}")
        return SpanExportResult.SUCCESS

provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ResumoNoConsole()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("aula9")

class HooksDeTrace(RunHooks):
    def __init__(self):
        self.abertos = {}

    async def on_llm_start(self, context, agent, system_prompt, input_items):
        self.abertos["llm"] = tracer.start_span("llm.chamada")

    async def on_llm_end(self, context, agent, response):
        self.abertos.pop("llm").end()

    async def on_tool_start(self, context, agent, tool):
        self.abertos["tool"] = tracer.start_span(f"tool.{tool.name}")

    async def on_tool_end(self, context, agent, tool, result):
        span = self.abertos.pop("tool")
        span.set_attribute("tool.nome", tool.name)
        span.set_attribute("erro", str(result).startswith("ERRO"))
        span.end()


TEMPERATURAS = {"brasília": 25, "são paulo": 22, "rio de janeiro": 28}

@function_tool
def consultar_temperatura(cidade: str) -> str:
    """Devolve a temperatura atual, em graus Celsius, de uma cidade."""
    graus = TEMPERATURAS.get(cidade.lower())
    sleep(2)  # simula demora de 0,5s
    return f"{graus}°C" if graus is not None else "ERRO: cidade desconhecida"


modelo = configurar()

agente = Agent(
    name="Meteorologista",
    instructions="Responda em português, em uma frase. Para temperatura de cidade, use a ferramenta.",
    tools=[consultar_temperatura],
)

PERGUNTAS = [
    "Quanto está fazendo em Brasília agora?",
    "E em São Paulo?",
    "Qual a temperatura em Gotham City?",  # a tool vai devolver ERRO
    "Quanto é 2 + 2?",                      # não precisa de tool
]

for pergunta in PERGUNTAS:
    resultado = Runner.run_sync(agente, pergunta)
    print(f"[usuário] {pergunta}\n")
    with tracer.start_as_current_span("agente.execucao") as raiz:   # a raiz do trace
        raiz.set_attribute("modelo", modelo)
        resultado = Runner.run_sync(agente, pergunta, hooks=HooksDeTrace())
    print(f"[resposta] {resultado.final_output}")
