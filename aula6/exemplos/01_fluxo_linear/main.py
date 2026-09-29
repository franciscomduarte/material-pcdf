"""
Exemplo 01 -- FLUXO LINEAR (o problema).

Ponto de partida da aula. Um sistema recebe uma solicitação e a trata em
etapas fixas:

    receber -> classificar -> analisar -> responder

Funciona... enquanto o mundo for simples. Este exemplo existe para você
PERCEBER O QUE FALTA. Depois de rodar, responda:

  1. O fluxo tem decisão? (E se a solicitação for simples e não precisar de análise?)
  2. Dá para voltar a uma etapa anterior? (E se a análise estiver errada?)
  3. Onde está o "estado"? (Quem guarda a categoria calculada em classificar?)

Rodar:
    python main.py
"""


def receber(solicitacao):
    print("[receber] Recebendo solicitação...")
    return solicitacao


def classificar(solicitacao):
    print("[classificar] Classificando solicitação...")
    return "simples"


def analisar(solicitacao):
    print("[analisar] Analisando solicitação...")
    return "análise concluída"


def responder(resultado):
    print("[responder] Gerando resposta...")
    return resultado


solicitacao = receber("Preciso saber como solicitar uma segunda via.")

categoria = classificar(solicitacao)  # calculada... e nunca usada!

resultado = analisar(solicitacao)  # roda SEMPRE, seja qual for a categoria

resposta = responder(resultado)

print("\nResposta final:", resposta)

# ---------------------------------------------------------------------------
# O PROBLEMA
# - A ordem A -> B -> C -> D está fixa no código. Para pular 'analisar' quando
#   a categoria é "simples", precisaríamos de um if... e depois outro... e outro.
# - Para "voltar e revisar" precisaríamos de um while espalhado pelo script.
# - 'categoria' é uma variável solta; cada função recebe só o que lhe passamos.
#   Não existe um lugar único com "tudo o que sabemos sobre esta solicitação".
# Próximo passo: representar o PROCESSO como dado -> um grafo.
# ---------------------------------------------------------------------------
