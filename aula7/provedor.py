"""
provedor.py -- mesmo mecanismo de troca de provedor das Aulas 4 e 5 (variável PROVEDOR no .env),
entregando um objeto Modelo. Na Aula 7 TODOS os exemplos, exercícios e desafios usam LLM REAL.

O GRAFO só conhece a abstração Modelo (método gerar). Quem escolhe a implementação é obter_modelo(),
lendo PROVEDOR:

    PROVEDOR=openai  (padrão) OpenAI           -> OPENAI_API_KEY, OPENAI_DEFAULT_MODEL (gpt-4o-mini)
    PROVEDOR=ollama  Ollama local, grátis      -> OLLAMA_BASE_URL, OLLAMA_MODEL (o modelo precisa estar baixado)
    PROVEDOR=claude  Anthropic/Claude          -> ANTHROPIC_API_KEY, ANTHROPIC_MODEL (opcional)

Sem a chave (ou sem o Ollama no ar) o programa PARA com uma mensagem dizendo o que fazer: não há LLM de mentira.
Trocar de provedor NÃO exige mexer no grafo.
"""
import json
import os
import urllib.request

from dotenv import load_dotenv

load_dotenv()

AJUDA = (
    "Configure um provedor real: copie o .env.example para .env e preencha.\n"
    "  - OpenAI: PROVEDOR=openai e OPENAI_API_KEY=...\n"
    "  - Ollama (grátis, local): PROVEDOR=ollama, `ollama serve` no ar e o modelo baixado (`ollama pull <modelo>`)."
)


class Modelo:
    """Contrato que o grafo conhece: recebe um prompt, devolve texto."""

    nome = "modelo"

    def gerar(self, prompt: str) -> str:
        raise NotImplementedError


class ModeloOpenAI(Modelo):
    """OpenAI e Ollama: ambos falam a API compatível com OpenAI (muda só o base_url)."""

    def __init__(self, base_url=None, api_key=None, modelo="gpt-4o-mini", nome="openai"):
        from openai import OpenAI  # import tardio: só quem usa precisa do pacote

        self.cliente = OpenAI(base_url=base_url, api_key=api_key, timeout=180)
        self.modelo = modelo
        self.nome = f"{nome}:{modelo}"

    def gerar(self, prompt: str) -> str:
        resp = self.cliente.chat.completions.create(
            model=self.modelo,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=700,
        )
        return (resp.choices[0].message.content or "").strip()


class ModeloClaude(Modelo):
    """Anthropic/Claude. A chave vem SEMPRE da variável de ambiente."""

    def __init__(self, modelo=None):
        chave = os.getenv("ANTHROPIC_API_KEY")
        if not chave:
            raise SystemExit("PROVEDOR=claude exige a variável ANTHROPIC_API_KEY.\n" + AJUDA)
        import anthropic  # import tardio

        self.cliente = anthropic.Anthropic(api_key=chave)
        self.modelo = modelo or os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
        self.nome = f"claude:{self.modelo}"

    def gerar(self, prompt: str) -> str:
        resp = self.cliente.messages.create(
            model=self.modelo,
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()


def _modelos_do_ollama(base_url: str) -> list[str] | None:
    """Nomes dos modelos que o Ollama tem (None se ele não responde)."""
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/models", timeout=3) as r:
            return [m["id"] for m in json.load(r).get("data", [])]
    except (OSError, ValueError, KeyError):
        return None


def obter_modelo() -> Modelo:
    """Devolve o Modelo REAL do provedor escolhido em PROVEDOR (padrão: openai)."""
    provedor = os.getenv("PROVEDOR", "openai").strip().lower()

    if provedor == "openai":
        chave = os.getenv("OPENAI_API_KEY")
        if not chave:
            raise SystemExit("PROVEDOR=openai exige OPENAI_API_KEY.\n" + AJUDA)
        return ModeloOpenAI(api_key=chave, modelo=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini"))
    if provedor == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        modelo = os.getenv("OLLAMA_MODEL", "llama3.1")
        disponiveis = _modelos_do_ollama(base_url)
        if disponiveis is None:
            raise SystemExit(f"PROVEDOR=ollama, mas o Ollama não responde em {base_url}. Rode `ollama serve`.\n" + AJUDA)
        if not any(m == modelo or m.startswith(modelo + ":") for m in disponiveis):
            raise SystemExit(f"O modelo {modelo!r} não está no Ollama (há: {', '.join(disponiveis) or 'nenhum'}). "
                             f"Rode `ollama pull {modelo}` ou ajuste OLLAMA_MODEL no .env.")
        return ModeloOpenAI(base_url=base_url, api_key="ollama", modelo=modelo, nome="ollama")
    if provedor == "claude":
        return ModeloClaude()
    raise SystemExit(f"PROVEDOR desconhecido: {provedor!r}. Use openai, ollama ou claude.")
