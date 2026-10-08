"""PASSO 3 -- Métricas Prometheus: contadores e tempos, expostos em http://localhost:8000/metrics."""
import base64
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agents import Agent, RunHooks, Runner, function_tool
from opentelemetry import trace
from prometheus_client import Counter, Histogram, start_http_server
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, SpanExporter, SpanExportResult

from base.provedor import configurar   # (já carrega o .env)


# --- 3a. as métricas: quantas vezes aconteceu? (e quanto tempo levou) ---
REQUISICOES = Counter("agent_requests", "Perguntas recebidas pelo agente")           # vira agent_requests_total
ERROS = Counter("agent_errors", "Execuções do agente que terminaram em exceção")      # agent_errors_total
DURACAO = Histogram("agent_request_duration_seconds", "Tempo total de uma pergunta")
TOOLS = Counter("tool_calls", "Chamadas de tool", ["tool"])                           # tool_calls_total
TOOLS_ERROS = Counter("tool_errors", "Tools que devolveram erro", ["tool"])           # tool_errors_total
start_http_server(int(os.getenv("PROMETHEUS_PORT", "8000")))                          # abre o /metrics

SESSAO = "aula8-demo"   # agrupa as perguntas numa sessão no Langfuse


def json_(x):
    return json.dumps(x, default=str, ensure_ascii=False)


# --- 1a. um "exportador" que imprime cada span que termina: nome, duração, trace_id, span_id, erro ---
class ResumoNoConsole(SpanExporter):
    def export(self, spans):
        for s in spans:
            ms = (s.end_time - s.start_time) / 1e6
            erro = "ERRO" if s.attributes.get("erro") else "ok"
            print(f"   {s.name:<26}{ms:6.0f} ms  trace={s.context.trace_id:032x}  "
                  f"span={s.context.span_id:016x}  {erro}")
        return SpanExportResult.SUCCESS


# --- 2a. segundo destino: o Langfuse recebe OpenTelemetry (OTLP/HTTP) com autenticação Basic ---
auth = base64.b64encode(f"{os.environ['LANGFUSE_PUBLIC_KEY']}:{os.environ['LANGFUSE_SECRET_KEY']}".encode()).decode()
langfuse = OTLPSpanExporter(
    endpoint=os.environ["LANGFUSE_BASE_URL"].rstrip("/") + "/api/public/otel/v1/traces",
    headers={"Authorization": f"Basic {auth}", "x-langfuse-ingestion-version": "4"},
)

provider = TracerProvider(resource=Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "aula8-agents")}))
provider.add_span_processor(SimpleSpanProcessor(ResumoNoConsole()))   # console (como no passo 1)
provider.add_span_processor(BatchSpanProcessor(langfuse))              # Langfuse
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("aula8")


# --- 1b. hooks do Agents SDK: o SDK avisa quando o LLM e as tools começam e terminam ---
class HooksDeTrace(RunHooks):
    def __init__(self):
        self.abertos = {}

    async def on_llm_start(self, context, agent, system_prompt, input_items):
        span = tracer.start_span("llm.chamada")
        span.set_attribute("langfuse.observation.type", "generation")       # vira "Generation" no Langfuse
        span.set_attribute("langfuse.session.id", SESSAO)
        span.set_attribute("gen_ai.request.model", MODELO.split(":")[1])   # nome puro, ex.: gpt-4o-mini
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
        TOOLS.labels(tool.name).inc()
        if str(result).startswith("ERRO"):
            TOOLS_ERROS.labels(tool.name).inc()
        span.set_attribute("langfuse.observation.output", str(result))
        span.set_attribute("erro", str(result).startswith("ERRO"))
        if str(result).startswith("ERRO"):
            span.set_attribute("langfuse.observation.level", "ERROR")
        span.end()


# --- o agente: igual ao ponto de partida ---
TEMPERATURAS = {"brasília": 25, "são paulo": 22, "rio de janeiro": 28}


@function_tool
def consultar_temperatura(cidade: str) -> str:
    """Devolve a temperatura atual, em graus Celsius, de uma cidade."""
    graus = TEMPERATURAS.get(cidade.lower())
    return f"{graus}°C" if graus is not None else "ERRO: cidade desconhecida"


modelo = MODELO = configurar()
agente = Agent(name="Meteorologista",
               instructions="Responda em português, em uma frase. Para temperatura de cidade, use a ferramenta.",
               tools=[consultar_temperatura])

PERGUNTAS = ["Quanto está fazendo em Brasília agora?", "Qual a temperatura em Gotham City?", "Quanto é 2 + 2?"]

for pergunta in PERGUNTAS * 3:      # 9 perguntas, para o gráfico ter o que mostrar
    print(f"\n[usuário] {pergunta}")
    REQUISICOES.inc()
    try:
        with DURACAO.time(), tracer.start_as_current_span("agente.execucao") as raiz:
            raiz.set_attribute("modelo", modelo)
            raiz.set_attribute("langfuse.observation.type", "agent")
            raiz.set_attribute("langfuse.session.id", SESSAO)
            raiz.set_attribute("langfuse.observation.input", pergunta)
            resultado = Runner.run_sync(agente, pergunta, hooks=HooksDeTrace())
            raiz.set_attribute("langfuse.observation.output", resultado.final_output)
        print(f"[resposta] {resultado.final_output}")
    except Exception as e:  # noqa: BLE001
        ERROS.inc()
        print(f"[erro] {type(e).__name__}: {e}")

provider.force_flush()
print("\nMétricas em http://localhost:8000/metrics  |  Prometheus em http://localhost:9090/targets")
try:
    input("Deixe rodando e abra o Prometheus/Grafana. ENTER para encerrar... ")
except EOFError:
    pass