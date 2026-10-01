"""
provedor.py -- mesmo mecanismo de troca de provedor das Aulas 4 e 5
(variável PROVEDOR no .env), agora entregando um objeto Modelo.

O GRAFO só conhece a abstração Modelo (método gerar). Quem escolhe a
implementação é obter_modelo(), lendo PROVEDOR:

    PROVEDOR=mock    determinístico, sem internet e sem API Key (padrão dos exemplos 01 a 08 e dos desafios)
    PROVEDOR=openai  OpenAI            -> OPENAI_API_KEY, OPENAI_DEFAULT_MODEL
    PROVEDOR=ollama  Ollama local      -> OLLAMA_BASE_URL, OLLAMA_MODEL
    PROVEDOR=claude  Anthropic/Claude  -> ANTHROPIC_API_KEY, ANTHROPIC_MODEL (opcional)

Os exemplos 09, 10 e 11 e os desafios usam LLM REAL por padrão (openai; Ollama com PROVEDOR=ollama). Sem chave ou sem
Ollama no ar, caem no Mock com aviso. PROVEDOR=mock força o Mock.

Trocar de provedor NÃO exige mexer no grafo.
"""
import os
import sys
import urllib.request

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


def _cair_no_mock(mock: Modelo, motivo: str, provedor: str) -> Modelo:
    """Sem chave (ou sem servidor): o exemplo NÃO trava, roda com o Mock e avisa."""
    print(
        f"AVISO: PROVEDOR={provedor}, mas {motivo}; usando o Mock (sem LLM real).\n"
        "       Para LLM real: copie o .env.example para .env e preencha (veja o README, seção Provedores).",
        file=sys.stderr,
    )
    return mock


def _ollama_no_ar(base_url: str) -> bool:
    """O Ollama responde em base_url? (teste rápido, 2 s)"""
    try:
        urllib.request.urlopen(base_url.rstrip("/") + "/models", timeout=2)
        return True
    except OSError:
        return False


def obter_modelo(mock: Modelo, padrao: str = "mock") -> Modelo:
    """Devolve o Modelo do provedor escolhido. O Mock é passado por quem chama
    (cada exemplo tem o seu modelo_mock.py, com as respostas do seu cenário).

    `padrao` é o provedor usado quando PROVEDOR não está definido: os exemplos 09, 10 e 11 e os desafios passam "openai"
    (LLM real, como nas Aulas 4 e 5); os exemplos 01-08 ficam no "mock". PROVEDOR=mock sempre força o Mock.
    Se o provedor real não puder ser usado (sem chave, Ollama fora do ar), cai no Mock COM AVISO."""
    provedor = os.getenv("PROVEDOR", padrao).strip().lower()

    if provedor == "mock":
        return mock
    if provedor == "openai":
        chave = os.getenv("OPENAI_API_KEY")
        if not chave:
            return _cair_no_mock(mock, "OPENAI_API_KEY não está definida", provedor)
        return ModeloOpenAI(api_key=chave, modelo=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini"))
    if provedor == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        if not _ollama_no_ar(base_url):
            return _cair_no_mock(mock, f"o Ollama não responde em {base_url} (rode `ollama serve`)", provedor)
        return ModeloOpenAI(
            base_url=base_url,
            api_key="ollama",
            modelo=os.getenv("OLLAMA_MODEL", "llama3.1"),
            nome="ollama",
        )
    if provedor == "claude":
        if not os.getenv("ANTHROPIC_API_KEY"):
            return _cair_no_mock(mock, "ANTHROPIC_API_KEY não está definida", provedor)
        return ModeloClaude()
    raise SystemExit(f"PROVEDOR desconhecido: {provedor!r}. Use mock, openai, ollama ou claude.")


def obter_modelo_real() -> Modelo:
    """Devolve o Modelo REAL do provedor escolhido em PROVEDOR (padrão: openai). Para os desafios SEM Mock.

    Sem chave (ou com o Ollama fora do ar) o programa PARA com uma mensagem dizendo o que fazer: não há LLM de mentira.
    """
    ajuda = (
        "Configure um LLM real: copie o .env.example para .env e preencha.\n"
        "  - OpenAI: PROVEDOR=openai e OPENAI_API_KEY=...\n"
        "  - Ollama (grátis, local): PROVEDOR=ollama, `ollama serve` no ar e o modelo baixado (`ollama pull <modelo>`)."
    )
    provedor = os.getenv("PROVEDOR", "openai").strip().lower()
    if provedor == "mock":
        raise SystemExit("Este desafio não usa Mock: ele roda só com LLM real.\n" + ajuda)
    if provedor == "openai":
        chave = os.getenv("OPENAI_API_KEY")
        if not chave:
            raise SystemExit("PROVEDOR=openai exige OPENAI_API_KEY.\n" + ajuda)
        return ModeloOpenAI(api_key=chave, modelo=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini"))
    if provedor == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        if not _ollama_no_ar(base_url):
            raise SystemExit(f"PROVEDOR=ollama, mas o Ollama não responde em {base_url}. Rode `ollama serve`.\n" + ajuda)
        return ModeloOpenAI(base_url=base_url, api_key="ollama", modelo=os.getenv("OLLAMA_MODEL", "llama3.1"), nome="ollama")
    if provedor == "claude":
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise SystemExit("PROVEDOR=claude exige ANTHROPIC_API_KEY.\n" + ajuda)
        return ModeloClaude()
    raise SystemExit(f"PROVEDOR desconhecido: {provedor!r}. Use openai, ollama ou claude.\n" + ajuda)
