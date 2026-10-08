"""
guardrails.py -- carrega uma pasta de configuração do NeMo Guardrails usando o MESMO provedor do .env.

O NeMo tem o próprio cliente de modelo. Esta função só aponta esse cliente para a OpenAI ou para o Ollama,
conforme PROVIDER, para que os exemplos não mudem.

    rails = carregar_rails("pasta/com/config.yml")
    rails.check(messages=[...], rail_types=[RailType.INPUT])
"""
import os

from dotenv import load_dotenv
from nemoguardrails import LLMRails, RailsConfig

load_dotenv()


def carregar_rails(pasta) -> LLMRails:
    config = RailsConfig.from_path(str(pasta))
    principal = next(m for m in config.models if m.type == "main")
    if os.getenv("PROVIDER", "openai").strip().lower() == "ollama":
        principal.engine = "openai"  # o Ollama fala o protocolo da OpenAI
        principal.model = os.getenv("OLLAMA_MODEL", "llama3.1")
        principal.parameters = {"base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"), "api_key": "ollama"}
    else:
        principal.engine = "openai"
        principal.model = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
    return LLMRails(config)
