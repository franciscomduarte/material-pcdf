"""
provedor.py -- mesmo mecanismo de troca de provedor das Aulas 4 e 5
(variável PROVEDOR no .env), agora entregando um objeto Modelo.

O GRAFO só conhece a abstração Modelo (método gerar). Quem escolhe a
implementação é obter_modelo(), lendo PROVEDOR:

    PROVEDOR=mock    (padrão) determinístico, sem internet e sem API Key
    PROVEDOR=openai  OpenAI            -> OPENAI_API_KEY, OPENAI_DEFAULT_MODEL
    PROVEDOR=ollama  Ollama local      -> OLLAMA_BASE_URL, OLLAMA_MODEL
    PROVEDOR=claude  Anthropic/Claude  -> ANTHROPIC_API_KEY, ANTHROPIC_MODEL (opcional)

Trocar de provedor NÃO exige mexer no grafo.
"""
import os

from dotenv import load_dotenv

load_dotenv()


class Modelo:
    """Contrato que o grafo conhece: recebe um prompt, devolve texto."""

    nome = "modelo"

    def gerar(self, prompt: str) -> str:
        raise NotImplementedError


class ModeloOpenAI(Modelo):
    """OpenAI e Ollama: ambos falam a API compatível com OpenAI (muda só o base_url)."""

    def __init__(self, base_url=None, api_key=None, modelo="gpt-4o-mini", nome="openai"):
        from openai import OpenAI  # import tardio: só quem usa precisa do pacote

        self.cliente = OpenAI(base_url=base_url, api_key=api_key)
        self.modelo = modelo
        self.nome = f"{nome}:{modelo}"

    def gerar(self, prompt: str) -> str:
        resp = self.cliente.chat.completions.create(
            model=self.modelo,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300,  # respostas curtas: modelos locais em CPU são lentos
        )
        return (resp.choices[0].message.content or "").strip()


class ModeloClaude(Modelo):
    """Anthropic/Claude. A chave vem SEMPRE da variável de ambiente."""

    def __init__(self, modelo=None):
        chave = os.getenv("ANTHROPIC_API_KEY")
        if not chave:
            raise SystemExit("PROVEDOR=claude exige a variável ANTHROPIC_API_KEY. Use PROVEDOR=mock para rodar sem chave.")
        import anthropic  # import tardio

        self.cliente = anthropic.Anthropic(api_key=chave)
        self.modelo = modelo or os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
        self.nome = f"claude:{self.modelo}"

    def gerar(self, prompt: str) -> str:
        resp = self.cliente.messages.create(
            model=self.modelo,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()


def obter_modelo(mock: Modelo) -> Modelo:
    """Devolve o Modelo do provedor escolhido. O Mock é passado por quem chama
    (cada exemplo tem o seu modelo_mock.py, com as respostas do seu cenário)."""
    provedor = os.getenv("PROVEDOR", "mock").strip().lower()

    if provedor == "mock":
        return mock
    if provedor == "openai":
        chave = os.getenv("OPENAI_API_KEY")
        if not chave:
            raise SystemExit("PROVEDOR=openai exige OPENAI_API_KEY no .env. Use PROVEDOR=mock ou ollama para rodar sem chave.")
        return ModeloOpenAI(api_key=chave, modelo=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini"))
    if provedor == "ollama":
        return ModeloOpenAI(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            api_key="ollama",
            modelo=os.getenv("OLLAMA_MODEL", "llama3.1"),
            nome="ollama",
        )
    if provedor == "claude":
        return ModeloClaude()
    raise SystemExit(f"PROVEDOR desconhecido: {provedor!r}. Use mock, openai, ollama ou claude.")
