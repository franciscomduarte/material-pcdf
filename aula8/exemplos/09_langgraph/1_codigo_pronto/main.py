"""Exemplo 09 (ponto de partida) -- classificar a pergunta e encaminhar para "consulta" ou "cálculo".
Funciona, mas o FLUXO está escondido num if/else: não dá para desenhar, nem ver o caminho percorrido."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agents import Agent, Runner

from base.provedor import configurar

TEMPERATURAS = {"brasília": 25, "são paulo": 22, "rio de janeiro": 28}  # dados fictícios

classificador = Agent(
    name="Classificador",
    instructions='Classifique a pergunta do usuário. Responda com UMA palavra: "consulta" (pergunta sobre temperatura de '
                 'cidade) ou "calculo" (conta matemática). Nada além da palavra.',
)


def consulta(pergunta: str) -> str:
    for cidade, graus in TEMPERATURAS.items():
        if cidade in pergunta.lower():
            return f"A temperatura em {cidade.title()} é {graus}°C."
    return "Não conheço essa cidade."


def calculo(pergunta: str) -> str:
    conta = re.search(r"(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)", pergunta)
    if not conta:
        return "Não entendi a conta."
    a, op, b = float(conta[1]), conta[2], float(conta[3])
    return f"{a:g} {op} {b:g} = {({'+': a + b, '-': a - b, '*': a * b, '/': a / b if b else float('nan')})[op]:g}"


modelo = configurar()
print(f"[modelo] {modelo}\n")
for pergunta in ["Qual a temperatura em Brasília?", "Quanto é 15 * 4?", "E em São Paulo?"]:
    categoria = Runner.run_sync(classificador, pergunta).final_output.strip().lower()
    if "calculo" in categoria or "cálculo" in categoria:   # <- o "fluxo" é este if/else
        resposta = calculo(pergunta)
    else:
        resposta = consulta(pergunta)
    print(f"[usuário] {pergunta}\n[categoria] {categoria}\n[resposta] {resposta}\n")
