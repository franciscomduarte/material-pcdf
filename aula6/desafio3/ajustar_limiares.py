"""
ajustar_limiares.py -- experimente os LIMIARES do desafio 3 sem rodar o grafo nem o LLM.

O decisor (Laya ou JEV) é chamado UMA vez por pergunta; o roteador é simulado aqui, com os limiares que você escolher.
Com o Laya ($env:JEV = "laya") não gasta crédito. Com o JEV real, 1 crédito por pergunta.

    python desafio3\\ajustar_limiares.py                              # os limiares originais
    python desafio3\\ajustar_limiares.py --confianca 0.1              # só o limiar de confiança
    python desafio3\\ajustar_limiares.py --sensivel 0.95 --confianca 0.1
    python desafio3\\ajustar_limiares.py --reescrever-sensivel        # a pergunta 'sensivel' mais específica
    python desafio3\\ajustar_limiares.py --texto "Preciso do horário de atendimento"   # um texto seu
"""
import argparse
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # provedor.py
sys.path.insert(0, str(Path(__file__).resolve().parent))      # jev.py, main.py (esqueleto: só as constantes)

from jev import obter_jev                                     # noqa: E402
from main import (BASE_CONHECIMENTO, LIMIAR_CONFIANCA, LIMIAR_SENSIVEL,  # noqa: E402
                  LIMIAR_URGENTE, PERGUNTAS_DE_TESTE, PERGUNTAS_JEV)

SENSIVEL_ESPECIFICA = ("O texto contém, escritos de forma explícita, um número de CPF, uma senha ou um número de cartão? "
                       "Responda sim só se o dado aparece no texto; mencionar documentos em geral não conta.")
OUTRO_ESPECIFICO = "qualquer assunto que não seja segunda via, passaporte ou horário de atendimento"


def rotear(n, lu, ls, lc):
    """O mesmo roteador do desafio 3 (a ordem das regras é a prioridade dos caminhos)."""
    if n["p_urgente"] >= lu:
        return "urgente"
    if n["p_sensivel"] >= ls:
        return "sensivel"
    if n["confianca"] < lc:
        return "incerto"
    return "com_base" if n["assunto"] in BASE_CONHECIMENTO else "sem_base"


def rotulo_esperado(caminho):
    for no, rotulo in (("encaminhar", "urgente"), ("alertar_dado_sensivel", "sensivel"),
                       ("pedir_esclarecimento", "incerto"), ("pesquisar", "com_base")):
        if no in caminho:
            return rotulo
    return "sem_base"


def numeros(jev, perguntas, texto):
    r = jev.decidir(texto, perguntas)
    return {"p_urgente": r["urgente"]["noul"], "p_sensivel": r["sensivel"]["noul"],
            "assunto": r["assunto"]["choice"], "confianca": r["assunto"]["confidence"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--urgente", type=float, default=LIMIAR_URGENTE, help=f"limiar de urgente (original {LIMIAR_URGENTE})")
    ap.add_argument("--sensivel", type=float, default=LIMIAR_SENSIVEL, help=f"limiar de dado sensível (original {LIMIAR_SENSIVEL})")
    ap.add_argument("--confianca", type=float, default=LIMIAR_CONFIANCA, help=f"confiança mínima no assunto (original {LIMIAR_CONFIANCA})")
    ap.add_argument("--reescrever-sensivel", action="store_true", help="usa uma pergunta 'sensivel' mais específica")
    ap.add_argument("--reescrever-outro", action="store_true", help="usa um critério mais específico para o assunto 'outro'")
    ap.add_argument("--texto", help="testa só este texto (sem esperado)")
    a = ap.parse_args()

    perguntas = copy.deepcopy(PERGUNTAS_JEV)
    if a.reescrever_sensivel:
        perguntas["sensivel"]["instructions"] = SENSIVEL_ESPECIFICA
    if a.reescrever_outro:
        perguntas["assunto"]["criteria"]["outro"] = OUTRO_ESPECIFICO

    jev = obter_jev()
    print(f"decisor: {jev.nome} | limiares: urgente {a.urgente}, sensível {a.sensivel}, confiança {a.confianca}\n")

    casos = [(a.texto, None)] if a.texto else [(c["pergunta"], rotulo_esperado(c["caminho"])) for c in PERGUNTAS_DE_TESTE]
    certas = 0
    for i, (texto, esperado) in enumerate(casos, start=1):
        n = numeros(jev, perguntas, texto)
        rota = rotear(n, a.urgente, a.sensivel, a.confianca)
        marca = ""
        if esperado:
            ok = rota == esperado
            certas += ok
            marca = f"  {'✓' if ok else '✗ esperado ' + esperado}"
        print(f"[{i}] {texto[:70]}")
        print(f"    urgente={n['p_urgente']:.2f}  sensível={n['p_sensivel']:.2f}  assunto={n['assunto']} (confiança {n['confianca']:.2f})")
        print(f"    caminho: {rota}{marca}\n")
    if not a.texto:
        print(f"{certas} de {len(casos)} perguntas no caminho esperado.")


if __name__ == "__main__":
    main()
