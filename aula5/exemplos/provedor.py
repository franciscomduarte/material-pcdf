"""
provedor.py -- mesmo mecanismo de troca OpenAI/Ollama usado na Aula 4.
Todo exemplo com agente chama configurar() no topo, antes de criar o Agent.
Backend decidido por PROVEDOR no .env (PROVEDOR=openai por padrão).
"""
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    set_default_openai_api,
    set_default_openai_client,
    set_default_openai_key,
    set_tracing_disabled,
)

load_dotenv()


def configurar() -> str:
    """Aplica a configuração do provedor escolhido no .env. Devolve o nome dele."""
    provedor = os.getenv("PROVEDOR", "openai").strip().lower()

    if provedor == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        cliente = AsyncOpenAI(base_url=base_url, api_key="ollama")
        set_default_openai_client(cliente)
        set_default_openai_api("chat_completions")
        set_tracing_disabled(True)
    else:
        set_default_openai_key(os.getenv("OPENAI_API_KEY"))

    return provedor
