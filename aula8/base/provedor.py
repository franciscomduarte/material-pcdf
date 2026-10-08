"""
provedor.py -- escolhe o modelo (OpenAI ou Ollama) pelo .env. Os agentes não mudam; só esta função muda.

    PROVIDER=openai   OpenAI           -> OPENAI_API_KEY, OPENAI_DEFAULT_MODEL (gpt-4o-mini)
    PROVIDER=ollama   Ollama local     -> OLLAMA_BASE_URL, OLLAMA_MODEL (o modelo precisa estar baixado)

Uso nos exemplos:
    from base.provedor import configurar
    modelo = configurar()      # depois é só Agent(...) e Runner.run_sync(...)

Sem chave (ou sem Ollama no ar) o programa PARA dizendo o que fazer. Não existe modelo de mentira.
"""
import json
import os
import urllib.request

from agents import set_default_openai_api, set_default_openai_client, set_tracing_disabled
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

AJUDA = (
    "Configure um provedor real: copie .env.example para .env e preencha.\n"
    "  - OpenAI: PROVIDER=openai e OPENAI_API_KEY=...\n"
    "  - Ollama: PROVIDER=ollama, `ollama serve` no ar e `ollama pull llama3.1`."
)


def _modelos_do_ollama(base_url: str) -> list[str] | None:
    """Nomes dos modelos que o Ollama tem (None se ele não responde)."""
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/models", timeout=3) as r:
            return [m["id"] for m in json.load(r).get("data", [])]
    except (OSError, ValueError, KeyError):
        return None


def configurar() -> str:
    """Aplica o provedor do .env ao SDK de agentes e devolve o modelo em uso (ex.: 'openai:gpt-4o-mini')."""
    provedor = os.getenv("PROVIDER", "openai").strip().lower()
    set_tracing_disabled(True)  # o tracing deste curso é OpenTelemetry/Langfuse, não o da OpenAI

    if provedor == "openai":
        chave = os.getenv("OPENAI_API_KEY")
        if not chave:
            raise SystemExit("PROVIDER=openai exige OPENAI_API_KEY.\n" + AJUDA)
        modelo = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
        os.environ["OPENAI_DEFAULT_MODEL"] = modelo  # modelo usado por todo Agent(...) sem `model`
        set_default_openai_client(AsyncOpenAI(api_key=chave))
        return f"openai:{modelo}"

    if provedor == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        modelo = os.getenv("OLLAMA_MODEL", "llama3.1")
        disponiveis = _modelos_do_ollama(base_url)
        if disponiveis is None:
            raise SystemExit(f"PROVIDER=ollama, mas o Ollama não responde em {base_url}. Rode `ollama serve`.\n" + AJUDA)
        if not any(m == modelo or m.startswith(modelo + ":") for m in disponiveis):
            raise SystemExit(f"O modelo {modelo!r} não está no Ollama (há: {', '.join(disponiveis) or 'nenhum'}). "
                             f"Rode `ollama pull {modelo}` ou ajuste OLLAMA_MODEL no .env.")
        os.environ["OPENAI_DEFAULT_MODEL"] = modelo
        set_default_openai_client(AsyncOpenAI(base_url=base_url, api_key="ollama"))  # chave obrigatória, ignorada
        set_default_openai_api("chat_completions")  # o Ollama não tem a Responses API
        return f"ollama:{modelo}"

    raise SystemExit(f"PROVIDER desconhecido: {provedor!r}. Use openai ou ollama.")
