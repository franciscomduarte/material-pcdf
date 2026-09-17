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
    """Aplica a configuração do provedor escolhido no `.env`. Devolve o nome dele."""
    provedor = os.getenv("PROVEDOR", "openai").strip().lower()

    if provedor == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        # A api_key é obrigatória no construtor, mas o Ollama a ignora.
        cliente = AsyncOpenAI(base_url=base_url, api_key="ollama")
        set_default_openai_client(cliente)        # todas as chamadas vão para o Ollama
        set_default_openai_api("chat_completions")  # Ollama não implementa a Responses API
        set_tracing_disabled(True)                 # sem envio de traces para a OpenAI
    else:
        # Caminho padrão: OpenAI de verdade.
        set_default_openai_key(os.getenv("OPENAI_API_KEY"))

    return provedor