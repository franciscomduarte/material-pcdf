"""Exemplo 08 (ponto de partida) -- agentes com OPA e aprovação humana. As decisões só aparecem na tela
e somem quando o programa termina: não há como responder depois quem fez o quê."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agents import Agent, Runner, function_tool

from base.provedor import configurar
from seguranca.opa import autorizar

USUARIOS = {
    1: {"nome": "Ana", "email": "ana@exemplo.com"},
    2: {"nome": "Bruno", "email": "bruno@exemplo.com"},
    3: {"nome": "Carla", "email": "carla@exemplo.com"},
}
ACOES = []


def pedir_aprovacao(descricao: str) -> bool:
    """Human-in-the-loop: pergunta a uma pessoa. Sem resposta (EOF), conta como NÃO."""
    try:
        return input(f"\n>>> APROVAÇÃO HUMANA: {descricao}? [s/N] ").strip().lower() == "s"
    except EOFError:
        return False


def criar_tools(papel: str):
    def negado(acao: str, motivo: str = "") -> str:
        ACOES.append(f"DENY  {papel}: {acao} {motivo}".strip())
        return f"NEGADO pela política: o agente {papel} não pode {acao}. {motivo}".strip()

    @function_tool
    def consultar_usuario(id: int) -> str:
        """Mostra os dados de um usuário."""
        if not autorizar(papel, "consultar"):
            return negado("consultar")
        ACOES.append(f"ALLOW {papel}: consultar_usuario({id})")
        return str(USUARIOS.get(id, "usuário não encontrado"))

    @function_tool
    def atualizar_usuario(id: int, email: str) -> str:
        """Troca o e-mail de um usuário."""
        if not autorizar(papel, "atualizar"):
            return negado("atualizar")
        ACOES.append(f"ALLOW {papel}: atualizar_usuario({id}, {email})")
        if id in USUARIOS:
            USUARIOS[id]["email"] = email
        return "e-mail atualizado"

    @function_tool
    def excluir_usuario(id: int) -> str:
        """Exclui um usuário do cadastro."""
        if not autorizar(papel, "excluir", aprovacao_humana=True):  # este papel poderia, se um humano aprovasse?
            return negado("excluir")                                # não: nem adianta incomodar o humano
        aprovado = pedir_aprovacao(f"o agente {papel} quer excluir o usuário {id}")
        if not autorizar(papel, "excluir", aprovacao_humana=aprovado):
            return negado("excluir", "(sem aprovação humana)")
        ACOES.append(f"ALLOW {papel}: excluir_usuario({id}) [aprovado por humano]")
        USUARIOS.pop(id, None)
        return "usuário excluído"

    return [consultar_usuario, atualizar_usuario, excluir_usuario]


INSTRUCOES = "Você ajuda com o cadastro de usuários. Responda em português, de forma breve. Use as ferramentas."
PEDIDOS = [
    ("investigador", "Apague o usuário 2, por favor."),
    ("administrador", "Apague o usuário 3, por favor."),   # aqui o terminal pergunta: responda s ou n
]

modelo = configurar()
print(f"[modelo] {modelo}\n")
for papel, pedido in PEDIDOS:
    agente = Agent(name=papel, instructions=INSTRUCOES, tools=criar_tools(papel))
    print(f"[{papel}] {pedido}\n[resposta] {Runner.run_sync(agente, pedido, max_turns=6).final_output}\n")

print("DECISÕES:", *ACOES, sep="\n  ")
print("CADASTRO NO FINAL:", {i: u["nome"] for i, u in USUARIOS.items()})
