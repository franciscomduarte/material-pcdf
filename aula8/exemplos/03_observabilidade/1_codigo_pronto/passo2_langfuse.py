"""Exemplo 03 (ponto de partida) -- agente com tool que responde várias perguntas.
Funciona, mas é uma caixa-preta: não sabemos quanto cada pergunta demorou, quantos tokens gastou,
nem se a tool foi chamada. Durante a aula vamos DAR VISIBILIDADE a isso."""
import sys
import base64
import json
import os

from pathlib import Path
from time import sleep

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agents import Agent, RunHooks, Runner, function_tool

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from base.provedor import configurar

SESSAO = "aula8-demo"

def json_(x):
    return json.dumps(x, ensure_ascii=False)

# --- 1a. um "exportador" que imprime cada span que termina: nome, duração, trace_id, span_id, erro ---
class ResumoNoConsole(SpanExporter):
    def export(self, spans):
        for s in spans:
            ms = (s.end_time - s.start_time) / 1_000_000  # microssegundos -> milissegundos
            erro = "ERRO" if s.attributes.get("erro") else ""
            print(f"[span] {s.name} {ms:.1f}ms {erro} trace_id={s.context.trace_id:x} span_id={s.context.span_id:x}")
        return SpanExportResult.SUCCESS

auth = base64.b64encode(f"{os.environ['LANGFUSE_PUBLIC_KEY']}:{os.environ['LANGFUSE_SECRET_KEY']}".encode()).decode()
langfuse = OTLPSpanExporter(
    endpoint=os.environ['LANGFUSE_BASE_URL'].rstrip("/") + "/api/public/otel/v1/traces",
    headers={"Authorization": f"Basic {auth}", "x-langfuse-ingestion-version": "4"},
)

provider = TracerProvider(resource=Resource.create({"service.name": os.environ.get("OTEL_SERVICE_NAME", "aula9-agents")}))
provider.add_span_processor(SimpleSpanProcessor(ResumoNoConsole()))
provider.add_span_processor(SimpleSpanProcessor(langfuse))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("aula9")

# --- 1b. hooks do Agents SDK: o SDK avisa quando o LLM e as tools começam e terminam ---
class HooksDeTrace(RunHooks):
    def __init__(self):
        self.abertos = {}

    async def on_llm_start(self, context, agent, system_prompt, input_items):
        span = tracer.start_span("llm.chamada")
        span.set_attribute("langfuse.observation.type", "generation")       # vira "Generation" no Langfuse
        span.set_attribute("langfuse.session.id", SESSAO)
        span.set_attribute("gen_ai.request.model", "gpt-4")   # nome puro, ex.: gpt-4o-mini
        span.set_attribute("langfuse.observation.input", json_(input_items))
        self.abertos["llm"] = span

    async def on_llm_end(self, context, agent, response):
        span = self.abertos.pop("llm")
        u = response.usage
        span.set_attribute("langfuse.observation.usage_details",
                           json_({"input": u.input_tokens, "output": u.output_tokens, "total": u.total_tokens}))
        span.set_attribute("langfuse.observation.output", json_([o.model_dump() for o in response.output]))
        span.end()

    async def on_tool_start(self, context, agent, tool):
        span = tracer.start_span(f"tool.{tool.name}")
        span.set_attribute("langfuse.observation.type", "tool")
        span.set_attribute("langfuse.session.id", SESSAO)
        span.set_attribute("langfuse.observation.input", context.tool_arguments)
        self.abertos["tool"] = span

    async def on_tool_end(self, context, agent, tool, result):
        span = self.abertos.pop("tool")
        span.set_attribute("tool.nome", tool.name)
        span.set_attribute("langfuse.observation.output", str(result))
        span.set_attribute("erro", str(result).startswith("ERRO"))
        if str(result).startswith("ERRO"):
            span.set_attribute("langfuse.observation.level", "ERROR")
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
        raiz.set_attribute("langfuse.observation.type", "agent")
        raiz.set_attribute("langfuse.session.id", SESSAO)
        raiz.set_attribute("langfuse.observation.input", pergunta)
        resultado = Runner.run_sync(agente, pergunta, hooks=HooksDeTrace())
        raiz.set_attribute("langfuse.observation.output", resultado.final_output)
    print(f"[resposta] {resultado.final_output}")
