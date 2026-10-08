"""
verificar_ambiente.py -- confere se tudo que a aula usa está instalado e no ar.

    python verificar_ambiente.py            # tudo
    python verificar_ambiente.py --sem-llm  # pula a chamada real ao modelo (não gasta tokens)

[OK] funciona | [FALTA] opcional ainda não configurado (ex.: Docker parado) | [ERRO] precisa corrigir.
"""
import os
import sys
import urllib.request
from importlib.metadata import PackageNotFoundError, version

from dotenv import load_dotenv

load_dotenv()
erros = 0


def ok(msg): print(f"  [OK]    {msg}")
def falta(msg): print(f"  [FALTA] {msg}")


def erro(msg):
    global erros
    erros += 1
    print(f"  [ERRO]  {msg}")


def http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status < 400
    except OSError:
        return False


print("1) Python")
v = sys.version_info
if (v.major, v.minor, v.micro) == (3, 11, 0):
    erro("Python 3.11.0 tem um bug que impede o openai-agents. Use 3.10 ou 3.11.1+.")
elif (3, 10) <= (v.major, v.minor) < (3, 14):
    ok(f"Python {v.major}.{v.minor}.{v.micro}")
else:
    erro(f"Python {v.major}.{v.minor} fora da faixa suportada (3.10 a 3.13).")

print("2) Bibliotecas")
for pacote in ["openai-agents", "openai", "langgraph", "opentelemetry-sdk", "opentelemetry-exporter-otlp-proto-http",
               "langfuse", "prometheus-client", "nemoguardrails", "python-dotenv", "pytest"]:
    try:
        ok(f"{pacote} {version(pacote)}")
    except PackageNotFoundError:
        erro(f"{pacote} não instalado -> python -m pip install -r requirements.txt")

print("3) Provedor de modelo")
print(f"  PROVIDER={os.getenv('PROVIDER', 'openai')}")
if "--sem-llm" in sys.argv:
    falta("chamada ao modelo pulada (--sem-llm)")
else:
    try:
        from agents import Agent, Runner

        from base.provedor import configurar

        modelo = configurar()
        r = Runner.run_sync(Agent(name="Teste", instructions="Responda só com a palavra: PRONTO"), "Diga a palavra.")
        ok(f"{modelo} respondeu: {r.final_output.strip()[:40]!r}")
    except SystemExit as e:
        erro(str(e))
    except Exception as e:  # noqa: BLE001 - queremos mostrar qualquer falha de rede/chave
        erro(f"falha ao chamar o modelo: {type(e).__name__}: {str(e)[:150]}")

print("4) Langfuse (Cloud ou local)")
if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
    try:
        import httpx

        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").rstrip("/")
        r = httpx.get(host + "/api/public/projects", timeout=15,
                      auth=(os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"]))
        if r.status_code == 200:
            ok(f"credenciais aceitas por {host}")
        else:
            erro(f"Langfuse respondeu {r.status_code} em {host}. Chaves erradas ou região errada: "
                 "EUA = https://us.cloud.langfuse.com, Europa = https://cloud.langfuse.com")
    except Exception as e:  # noqa: BLE001
        erro(f"Langfuse: {type(e).__name__}: {str(e)[:150]}")
else:
    falta("LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY vazias no .env (necessário a partir do exemplo de Langfuse)")

print("5) Infraestrutura Docker (docker compose up -d)")
opa = os.getenv("OPA_URL", "http://localhost:8181")
for nome, url in [("OPA", opa + "/health"), ("Prometheus", "http://localhost:9090/-/healthy"),
                  ("Grafana", "http://localhost:3000/api/health")]:
    if http_ok(url):
        ok(f"{nome} no ar")
    else:
        falta(f"{nome} não responde em {url} (suba o Docker: docker compose up -d)")

print()
print("Resultado:", "tudo certo." if erros == 0 else f"{erros} erro(s) para corrigir.")
sys.exit(1 if erros else 0)
