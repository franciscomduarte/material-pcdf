"""Exemplo 07 (ponto de partida) -- dois agentes com privilégio mínimo (investigador e administrador).
Quem decide o que cada um pode fazer é uma lista dentro do código, e o administrador exclui sem ninguém aprovar."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agents import Agent, Runner, function_tool

from base.provedor import configurar

USUARIOS = {
    1: {"nome": "Ana", "email": "ana@exemplo.com"},
    2: {"nome": "Bruno", "email": "bruno@exemplo.com"},
    3: {"nome": "Carla", "email": "carla@exemplo.com"},
}
ACOES = []


@function_tool
def consultar_usuario(id: int) -> str:
    """Mostra os dados de um usuário."""
    ACOES.append(f"consultar_usuario({id})")
    return str(USUARIOS.get(id, "usuário não encontrado"))


@function_tool
def atualizar_usuario(id: int, email: str) -> str:
    """Troca o e-mail de um usuário."""
    ACOES.append(f"atualizar_usuario({id}, {email})")
    if id in USUARIOS:
        USUARIOS[id]["email"] = email
    return "e-mail atualizado"


@function_tool
def excluir_usuario(id: int) -> str:
    """Exclui um usuário do cadastro."""
    ACOES.append(f"excluir_usuario({id})")
    USUARIOS.pop(id, None)
    return "usuário excluído"


INSTRUCOES = "Você ajuda com o cadastro de usuários. Responda em português, de forma breve. Use as ferramentas."
TOOLS_POR_PAPEL = {  # a "política" mora aqui, misturada ao código
    "investigador": [consultar_usuario],
    "administrador": [consultar_usuario, atualizar_usuario, excluir_usuario],
}

modelo = configurar()
print(f"[modelo] {modelo}\n")
for papel, pedido in [("investigador", "Mostre os dados do usuário 1."),
                      ("administrador", "Apague o usuário 3, por favor.")]:
    agente = Agent(name=papel, instructions=INSTRUCOES, tools=TOOLS_POR_PAPEL[papel])
    print(f"[{papel}] {pedido}\n[resposta] {Runner.run_sync(agente, pedido, max_turns=6).final_output}\n")

print("AÇÕES EXECUTADAS:", *ACOES, sep="\n  ")
print("CADASTRO NO FINAL:", {i: u["nome"] for i, u in USUARIOS.items()})
