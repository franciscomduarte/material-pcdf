"""
provedor.py -- configura o SDK de agentes (openai-agents) para o provedor escolhido em PROVEDOR (.env).

Mesmo mecanismo das Aulas 2 a 5: os agentes são `Agent(name=..., instructions=...)` e rodam com `Runner`.
Quem muda de OpenAI para Ollama é só esta função; os agentes e o grafo NÃO mudam.

    PROVEDOR=openai  (padrão) OpenAI      -> OPENAI_API_KEY, OPENAI_DEFAULT_MODEL (gpt-4o-mini)
    PROVEDOR=ollama  Ollama local, grátis -> OLLAMA_BASE_URL, OLLAMA_MODEL (o modelo precisa estar baixado)

Sem a chave (ou sem o Ollama no ar) o programa PARA com uma mensagem dizendo o que fazer: não há LLM de mentira.
"""
import json
import os
import urllib.request

import httpx
from agents import set_default_openai_api, set_default_openai_client, set_tracing_disabled
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

AJUDA = (
    "Configure um provedor real: copie o .env.example para .env e preencha.\n"
    "  - OpenAI: PROVEDOR=openai e OPENAI_API_KEY=...\n"
    "  - Ollama (grátis, local): PROVEDOR=ollama, `ollama serve` no ar e o modelo baixado (`ollama pull <modelo>`)."
)


def _cliente(base_url: str | None, api_key: str) -> AsyncOpenAI:
    # O LangGraph executa cada nó síncrono numa thread, e cada Runner.run_sync() cria o seu próprio laço de
    # eventos. Conexões HTTP reaproveitadas entre laços diferentes travam: por isso, sem conexões persistentes.
    http = httpx.AsyncClient(limits=httpx.Limits(max_keepalive_connections=0), timeout=180)
    return AsyncOpenAI(base_url=base_url, api_key=api_key, http_client=http)


def _modelos_do_ollama(base_url: str) -> list[str] | None:
    """Nomes dos modelos que o Ollama tem (None se ele não responde)."""
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/models", timeout=3) as r:
            return [m["id"] for m in json.load(r).get("data", [])]
    except (OSError, ValueError, KeyError):
        return None


def configurar() -> str:
    """Aplica o provedor do `.env` ao SDK de agentes e devolve o nome do modelo em uso (ex.: 'openai:gpt-4o-mini')."""
    provedor = os.getenv("PROVEDOR", "openai").strip().lower()
    set_tracing_disabled(True)  # sem envio de traces para a OpenAI

    if provedor == "openai":
        chave = os.getenv("OPENAI_API_KEY")
        if not chave:
            raise SystemExit("PROVEDOR=openai exige OPENAI_API_KEY.\n" + AJUDA)
        modelo = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
        os.environ["OPENAI_DEFAULT_MODEL"] = modelo  # é o modelo que todo Agent(...) usa quando não recebe `model`
        set_default_openai_client(_cliente(None, chave))
        return f"openai:{modelo}"

    if provedor == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        modelo = os.getenv("OLLAMA_MODEL", "llama3.1")
        disponiveis = _modelos_do_ollama(base_url)
        if disponiveis is None:
            raise SystemExit(f"PROVEDOR=ollama, mas o Ollama não responde em {base_url}. Rode `ollama serve`.\n" + AJUDA)
        if not any(m == modelo or m.startswith(modelo + ":") for m in disponiveis):
            raise SystemExit(f"O modelo {modelo!r} não está no Ollama (há: {', '.join(disponiveis) or 'nenhum'}). "
                             f"Rode `ollama pull {modelo}` ou ajuste OLLAMA_MODEL no .env.")
        os.environ["OPENAI_DEFAULT_MODEL"] = modelo
        set_default_openai_client(_cliente(base_url, "ollama"))  # a api_key é obrigatória, mas o Ollama a ignora
        set_default_openai_api("chat_completions")  # o Ollama não implementa a Responses API
        return f"ollama:{modelo}"

    raise SystemExit(f"PROVEDOR desconhecido: {provedor!r}. Use openai ou ollama.")
