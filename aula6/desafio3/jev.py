"""
jev.py -- o cliente do JEV (Jev AI, da TypeSafe): decisões TIPADAS sobre um texto. JÁ VEM PRONTO.

O JEV não escreve texto. Ele responde a PERGUNTAS sobre um texto com valores que o código entende:

    "noul"   (sim/não)  -> um número de 0 a 1: a probabilidade de "sim"
    "choice" (escolha)  -> a opção escolhida, as probabilidades de cada uma e a CONFIANÇA (0 a 1)
    "score"  (escala)   -> um nível de uma escala ordenada

Várias perguntas vão em UMA chamada (até 64). Cada chamada gasta 1 crédito da conta.

    jev = obter_jev()
    respostas = jev.decidir("Estou passando mal agora", {
        "urgente": {"type": "noul", "instructions": "É urgente?"},
        "assunto": {"type": "choice", "instructions": "Qual o assunto?", "criteria": {"saude": "...", "outro": "..."}},
    })
    respostas["urgente"]["noul"]        # 0.98
    respostas["assunto"]["choice"]      # "saude"
    respostas["assunto"]["confidence"]  # 0.9

Duas implementações com a MESMA interface (como o LLM e o Mock nas outras aulas):
    JevReal  chama https://jev-ai.pro/api/v1/systemone (precisa de JEV_AI_API_KEY no .env; a chave NUNCA vai no código)
    JevMock  decisões determinísticas por palavras-chave: é o que os TESTES usam (sem internet, sem gastar créditos)

obter_jev(): o decisor REAL. JEV real (com JEV_AI_API_KEY) ou Laya local ($env:JEV = "laya"). Sem nenhum dos dois, o programa PARA
    e diz o que fazer: não há decisor de mentira nos exemplos (o JevMock existe só para os testes: conferir.py e test_pontos.py).
"""
import json
import os
import sys
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()

URL_JEV = "https://jev-ai.pro/api/v1/systemone"  # a única rota da API


class JevReal:
    """Chama a API do JEV. Cada decidir() = 1 requisição = 1 crédito."""

    nome = "jev-real"

    def __init__(self, chave: str, modelo: str = "jev-latest"):
        self.chave = chave        # vem de JEV_AI_API_KEY (nunca escreva a chave no código)
        self.modelo = modelo      # "jev-latest" = o modelo mais recente do System One

    def decidir(self, texto: str, perguntas: dict) -> dict:
        """Envia o texto e as perguntas; devolve o mapa de respostas, com a mesma chave de cada pergunta."""
        corpo = {"model": self.modelo, "state": texto, "questions": perguntas}
        pedido = urllib.request.Request(
            URL_JEV, data=json.dumps(corpo).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.chave}", "Content-Type": "application/json",
                     "Accept": "application/json", "User-Agent": "curso-pcdf/1.0"})
        try:
            with urllib.request.urlopen(pedido, timeout=30) as resposta:
                return json.load(resposta)["answers"]
        except urllib.error.HTTPError as erro:
            motivos = {401: "chave inválida ou revogada", 402: "sem créditos/tokens", 422: "corpo da requisição inválido",
                       429: "limite de requisições (aguarde e tente de novo)"}
            raise RuntimeError(f"JEV respondeu {erro.code}: {motivos.get(erro.code, 'erro do serviço')}") from erro


class LayaLocal:
    """Laya (open source, Apache 2.0): o MESMO tipo de decisão tipada do JEV, mas RODA NA SUA MÁQUINA.
    Sem API, sem chave, sem créditos. Mesma interface: decidir(texto, perguntas) -> mapa de respostas.
    Instalação: pip install laya  (baixa o modelo na 1ª vez; usa o checkpoint multilíngue para português)."""

    nome = "laya-local"

    def __init__(self):
        from laya import Router  # import tardio: só quem usa o Laya precisa do pacote (e do torch)
        self.router = Router()   # carrega o modelo uma vez (demora na 1ª execução)

    def decidir(self, texto: str, perguntas: dict) -> dict:
        return self.router.predict({"body": texto}, perguntas)["answers"]


class JevMock:
    """JEV de mentira, DETERMINÍSTICO: decide por palavras-chave. Usado nos testes (sem internet e sem créditos).
    Imita o formato das respostas do JEV real para as perguntas "urgente", "sensivel" e "assunto"."""

    nome = "jev-mock"

    ASSUNTOS = {"segunda_via": ("segunda via",), "passaporte": ("passaporte",), "horario": ("horário", "horario")}

    def decidir(self, texto: str, perguntas: dict) -> dict:
        t = texto.lower()
        respostas = {}
        if "urgente" in perguntas:  # risco ou pedido de atendimento imediato
            sinais = ("passando mal", "agora", "urgente", "emergência", "socorro")
            respostas["urgente"] = {"type": "noul", "noul": 0.98 if any(s in t for s in sinais) else 0.03}
        if "sensivel" in perguntas:  # dado pessoal sensível
            respostas["sensivel"] = {"type": "noul", "noul": 0.99 if any(s in t for s in ("cpf", "senha", "cartão")) else 0.02}
        if "assunto" in perguntas:  # o assunto e a CONFIANÇA nele
            achados = [a for a, palavras in self.ASSUNTOS.items() if any(p in t for p in palavras)]
            if len(achados) >= 2:  # ambíguo: a confiança é baixa
                probs = {"passaporte": 0.40, "segunda_via": 0.35, "horario": 0.0, "outro": 0.25}
                respostas["assunto"] = {"type": "choice", "choice": "passaporte", "confidence": 0.40, "probabilities": probs}
            elif achados:
                probs = {a: (1.0 if a == achados[0] else 0.0) for a in ("segunda_via", "passaporte", "horario", "outro")}
                respostas["assunto"] = {"type": "choice", "choice": achados[0], "confidence": 1.0, "probabilities": probs}
            else:
                probs = {"segunda_via": 0.0, "passaporte": 0.0, "horario": 0.0, "outro": 1.0}
                respostas["assunto"] = {"type": "choice", "choice": "outro", "confidence": 1.0, "probabilities": probs}
        return respostas


def obter_jev():
    """O decisor REAL: o Laya local (JEV=laya) ou o JEV (com JEV_AI_API_KEY). Sem nenhum dos dois, o programa PARA."""
    if os.getenv("JEV", "").strip().lower() == "laya":  # JEV=laya: o decisor local (sem chave, sem créditos)
        return LayaLocal()
    chave = os.getenv("JEV_AI_API_KEY")
    if not chave:
        raise SystemExit("Nenhum decisor real disponível. Escolha um:\n"
                         "  - JEV (API):  coloque JEV_AI_API_KEY no .env (cada pergunta gasta 1 crédito)\n"
                         "  - Laya (local, grátis):  pip install laya  e  $env:JEV = \"laya\"")
    return JevReal(chave)
