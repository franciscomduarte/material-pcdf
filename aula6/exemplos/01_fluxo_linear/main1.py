"""
Exemplo 01 -- versão com DECISÃO e VOLTA (o que o fluxo linear não tinha).

    receber -> classificar -> (simples?) -> responder
                           -> (complexa) -> analisar -> válido? -> responder
                                               ^____ não ____|   (até 3 vezes)

Rodar:
    python main1.py                      # solicitação complexa (mostra a volta)
    python main1.py "segunda via"        # solicitação simples (pula a análise)
"""

import sys

_chamadas_analisar = 0


def receber(texto):
    print("[receber] Recebendo solicitação...")
    return texto


def classificar(solicitacao):
    print("[classificar] Classificando solicitação...")
    categoria = "simples" if "segunda via" in solicitacao.lower() else "complexa"
    print(f"           -> categoria: {categoria}")
    return categoria


def analisar(solicitacao):
    global _chamadas_analisar
    _chamadas_analisar += 1
    print(f"[analisar] Analisando solicitação (execução {_chamadas_analisar})...")
    # Simula uma análise que só sai correta na 3ª execução.
    return "análise concluída" if _chamadas_analisar >= 3 else "análise incompleta"


def valido(resultado):
    ok = resultado == "análise concluída"
    print(f"[valido] '{resultado}' -> {'OK' if ok else 'INVÁLIDO, voltar e analisar de novo'}")
    return ok


def responder(conteudo):
    print("[responder] Gerando resposta...")
    return conteudo


texto = " ".join(sys.argv[1:]) or "Preciso contestar uma multa e revisar meu processo."

solicitacao = receber(texto)
categoria = classificar(solicitacao)

if categoria == "simples":
    resposta = responder(solicitacao)
else:
    resultado = analisar(solicitacao)
    tentativas = 0
    while not valido(resultado) and tentativas < 3:
        resultado = analisar(solicitacao)      # a "volta"
        tentativas += 1
    resposta = responder(resultado)

print("\nResposta final:", resposta)
