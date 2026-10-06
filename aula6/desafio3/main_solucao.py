"""
DESAFIO 3 -- SOLUÇÃO DE REFERÊNCIA (professor; esta pasta está no .gitignore).

Organização: dentro de construir_grafo(), FASE A (as funções: nós e roteador, um bloco por ponto) e
FASE B (ligar os pontos). Mesmo arquivo-base do esqueleto.

Rodar (a partir de aula6/):
    python desafio3\\solucao\\main.py
    $env:DESAFIO_DIR = "desafio3\\solucao"; python desafio3\\conferir.py
"""
import sys                          # sys.path: permite importar provedor.py (na pasta aula6/)
from pathlib import Path            # caminhos de arquivos (a pasta saida/)
from typing import TypedDict        # o tipo do Estado (um dicionário com campos conhecidos)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # provedor.py (escolhe o LLM)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # jev.py e modelo_mock.py (desta pasta)

from langgraph.graph import END, START, StateGraph  # noqa: F401  StateGraph monta o grafo; START e END são a entrada e a saída

from jev import obter_jev                 # o decisor REAL: JEV (com JEV_AI_API_KEY) ou Laya local (JEV=laya)
from provedor import obter_modelo_real    # escolhe o LLM REAL (OpenAI ou Ollama) pelo .env; sem ele, o programa para

# ---- LIMIARES: os números a partir dos quais o grafo muda de caminho (experimente mudá-los!) ----
LIMIAR_URGENTE = 0.8     # probabilidade de "urgente" a partir da qual o caso vai ao plantão
LIMIAR_SENSIVEL = 0.8    # probabilidade de "dado sensível" a partir da qual o grafo recusa e alerta
LIMIAR_CONFIANCA = 0.6   # confiança mínima no ASSUNTO; abaixo disso o grafo pede esclarecimento em vez de adivinhar

# ---- As perguntas que o grafo faz ao JEV (UMA chamada responde as 3 ao mesmo tempo) ----
PERGUNTAS_JEV = {
    "urgente": {"type": "noul",  # "noul" = sim/não: o JEV devolve a probabilidade de "sim" (0 a 1)
                "instructions": "A pessoa descreve risco à saúde ou à segurança, ou pede atendimento imediato?"},
    "sensivel": {"type": "noul",
                 "instructions": "O texto contém dado pessoal sensível, como CPF, senha ou número de cartão?"},
    "assunto": {"type": "choice",  # "choice" = escolha: o JEV devolve a opção, as probabilidades e a CONFIANÇA
                "instructions": "Qual é o assunto da solicitação?",
                "criteria": {"segunda_via": "pede segunda via de documento", "passaporte": "trata de passaporte",
                             "horario": "pergunta o horário de atendimento",
                             "outro": "qualquer outro assunto ou assunto indefinido"}},
}


class Estado(TypedDict):
    """O ESTADO do grafo: o que circula entre os nós. Cada nó lê daqui e devolve SÓ o que mudou."""
    solicitacao: str      # o texto que o usuário enviou (a entrada do grafo)
    p_urgente: float      # escrito por avaliar (JEV): probabilidade de ser urgente (0 a 1)
    p_sensivel: float     # escrito por avaliar (JEV): probabilidade de conter dado sensível (0 a 1)
    assunto: str          # escrito por avaliar (JEV): "segunda_via" | "passaporte" | "horario" | "outro"
    confianca: float      # escrito por avaliar (JEV): a confiança (0 a 1) na escolha do assunto
    informacao: str       # escrito por pesquisar: o procedimento do assunto; "" = não há (caminho sem_base)
    encaminhamento: str   # escrito por encaminhar: a confirmação de envio ao plantão (só no caminho urgente)
    resposta: str         # a resposta final ao usuário (escrita por responder, ou pelos nós que encerram o caso)


# ---------------------------------------------------------------- ferramentas
# A base de conhecimento (assunto -> procedimento). As CHAVES são os mesmos rótulos da pergunta "assunto" do JEV.
BASE_CONHECIMENTO = {
    "segunda_via": "Agendar atendimento; levar documento com foto; pagar a taxa de emissão.",
    "passaporte": "Preencher o formulário online; agendar a Polícia Federal; pagar a GRU.",
    "horario": "Atendimento de segunda a sexta, das 8h às 17h.",
}


def encaminhar_plantao(solicitacao: str) -> str:
    """TOOL comum: simula o envio de um caso urgente ao plantão e devolve a confirmação (vai para estado["encaminhamento"])."""
    return "Caso encaminhado ao plantão 24h (prioridade máxima)."


# ------------------------------------------------ prompt (pronto: use no nó responder)
def prompt_responder(estado: Estado) -> str:
    """O prompt do nó responder (LLM): monta o contexto pelo que EXISTE no estado. Quem decidiu o caminho foi o JEV."""
    if estado["encaminhamento"]:  # caminho urgente: só informar o encaminhamento
        contexto = f"Encaminhamento: {estado['encaminhamento']}\n"
    elif not estado["informacao"]:  # sem base: admitir que não sabe (não inventar)
        contexto = "SEM_BASE: o assunto não consta na base; NÃO invente uma resposta.\n"
    else:  # com base: responder a partir do procedimento
        contexto = f"Informação: {estado['informacao']}\n"
    return (
        "TAREFA: responder\n"
        "Escreva uma resposta curta e cordial ao usuário.\n"
        f"Solicitação: {estado['solicitacao']}\n"
        f"{contexto}"
    )


# ------------------------------------------------------------------ o grafo
def construir_grafo(modelo, jev):
    """O grafo COMPILADO. `modelo` escreve (modelo.gerar); `jev` decide (jev.decidir)."""
    # ==============================================================================================
    # FASE A -- AS FUNÇÕES
    # ==============================================================================================

    def receber(estado):
        """PONTO 1: começa o processo: limpa a entrada e inicializa TODOS os campos do estado."""
        return {"solicitacao": estado["solicitacao"].strip(), "p_urgente": 0.0, "p_sensivel": 0.0, "assunto": "",
                "confianca": 0.0, "informacao": "", "encaminhamento": "", "resposta": ""}

    def avaliar(estado):
        """PONTO 2 (JEV): UMA chamada responde as 3 perguntas; guardamos os NÚMEROS no estado, sem interpretar texto."""
        respostas = jev.decidir(estado["solicitacao"], PERGUNTAS_JEV)
        return {"p_urgente": respostas["urgente"]["noul"],                 # noul: probabilidade de "sim"
                "p_sensivel": respostas["sensivel"]["noul"],
                "assunto": respostas["assunto"]["choice"],                 # choice: a opção escolhida
                "confianca": respostas["assunto"]["confidence"]}           # e a confiança nela

    def encaminhar(estado):
        """PONTO 3 (tool): caminho urgente: envia o caso ao plantão e guarda a confirmação."""
        return {"encaminhamento": encaminhar_plantao(estado["solicitacao"])}

    def responder(estado):
        """PONTO 3 (LLM): escreve a resposta final com o que existir no estado (encaminhamento, sem base ou procedimento)."""
        return {"resposta": modelo.gerar(prompt_responder(estado))}

    def alertar_dado_sensivel(estado):
        """PONTO 4: o texto traz dado sensível: recusa, orienta e ENCERRA (nada vai para a base nem para o LLM)."""
        return {"resposta": "Por segurança, não envie CPF, senhas ou números de cartão por aqui. "
                            "Apague essas informações e descreva o seu pedido sem elas."}

    def pedir_esclarecimento(estado):
        """PONTO 5: a confiança no assunto é baixa: em vez de adivinhar, pede que a pessoa explique e ENCERRA."""
        return {"resposta": "Não consegui entender com segurança qual é o seu assunto. Pode explicar com outras palavras "
                            "(por exemplo: segunda via de documento, passaporte ou horário de atendimento)?"}

    def pesquisar(estado):
        """PONTO 6 (tool): procura o procedimento do assunto escolhido pelo JEV ("" se o assunto não está na base)."""
        return {"informacao": BASE_CONHECIMENTO.get(estado["assunto"], "")}

    def rotear_apos_avaliar(estado):
        """O roteador DECIDE PELOS NÚMEROS (só lê o estado): a ordem das regras é a prioridade dos caminhos."""
        if estado["p_urgente"] >= LIMIAR_URGENTE:  # 1º: risco vence tudo
            return "urgente"
        if estado["p_sensivel"] >= LIMIAR_SENSIVEL:  # 2º: dado sensível
            return "sensivel"
        if estado["confianca"] < LIMIAR_CONFIANCA:  # 3º: JEV pouco confiante no assunto: não adivinhar
            return "incerto"
        return "com_base" if estado["assunto"] in BASE_CONHECIMENTO else "sem_base"  # 4º: o assunto está na base?

    # ==============================================================================================
    # FASE B -- LIGAR OS PONTOS
    # ==============================================================================================
    construtor = StateGraph(Estado)
    construtor.add_node("receber", receber)                                      # PONTO 1
    construtor.add_edge(START, "receber")
    construtor.add_node("avaliar", avaliar)                                      # PONTO 2
    construtor.add_edge("receber", "avaliar")
    construtor.add_node("encaminhar", encaminhar)                                # PONTO 3
    construtor.add_node("responder", responder)
    construtor.add_node("alertar_dado_sensivel", alertar_dado_sensivel)          # PONTO 4
    construtor.add_node("pedir_esclarecimento", pedir_esclarecimento)            # PONTO 5
    construtor.add_node("pesquisar", pesquisar)                                  # PONTO 6
    construtor.add_conditional_edges("avaliar", rotear_apos_avaliar, {
        "urgente": "encaminhar", "sensivel": "alertar_dado_sensivel", "incerto": "pedir_esclarecimento",
        "com_base": "pesquisar", "sem_base": "responder"})
    construtor.add_edge("encaminhar", "responder")
    construtor.add_edge("pesquisar", "responder")
    construtor.add_edge("responder", END)
    construtor.add_edge("alertar_dado_sensivel", END)
    construtor.add_edge("pedir_esclarecimento", END)
    return construtor.compile()


# ------------------------------------------------------------------ execução
def executar(app, solicitacao: str):
    """Roda o grafo e devolve (estado_final, caminho). O caminho vem do stream de atualizações."""
    estado: dict = {"solicitacao": solicitacao}  # o estado acumulado: começa só com a solicitação
    caminho = []  # os nomes dos nós, na ordem em que rodaram
    for passo in app.stream(estado, {"recursion_limit": 40}, stream_mode="updates"):  # cada passo: {nome_do_nó: o que ele escreveu}
        for no, atualizacao in passo.items():
            caminho.append(no)
            estado.update(atualizacao)  # aplica a atualização ao estado, como o LangGraph faz
    return estado, caminho


# ------------------------------------------------ ver o que aconteceu (PRONTO: não precisa mexer)
def _curto(valor, limite: int = 110) -> str:
    """Encurta um valor longo para caber em uma linha do log."""
    texto = repr(valor)
    return texto if len(texto) <= limite else texto[: limite - 3] + "..."


def mostrar_execucao(app, solicitacao: str):
    """Roda o grafo e mostra, NÓ A NÓ, o que cada um escreveu no estado, e como o JEV decidiu o caminho."""
    print("=" * 70)
    print("SOLICITAÇÃO:", solicitacao)
    print("=" * 70)
    estado: dict = {"solicitacao": solicitacao}
    caminho = []
    for passo in app.stream(estado, {"recursion_limit": 40}, stream_mode="updates"):
        for no, atualizacao in passo.items():
            caminho.append(no)
            print(f"\n[{len(caminho)}] {no}")
            for campo, valor in atualizacao.items():
                print(f"      escreveu  {campo:15} = {_curto(valor)}")
            estado.update(atualizacao)
    print("\n" + "-" * 70)
    print("CAMINHO PERCORRIDO:", " -> ".join(caminho))
    print("COMO O MODELO DE DECISÃO DECIDIU:")
    print(f"      p_urgente  = {estado.get('p_urgente'):.2f}   (limiar {LIMIAR_URGENTE})")
    print(f"      p_sensivel = {estado.get('p_sensivel'):.2f}   (limiar {LIMIAR_SENSIVEL})")
    print(f"      assunto    = {estado.get('assunto')!r}, confiança {estado.get('confianca'):.2f}   (mínimo {LIMIAR_CONFIANCA})")
    print(f"RESPOSTA: {estado.get('resposta')}")
    return estado, caminho


def mermaid_do_grafo(app, caminho=None) -> str:
    """Devolve o Mermaid do grafo. Se `caminho` for dado, os nós que executaram saem destacados."""
    texto = app.get_graph().draw_mermaid()  # o desenho do grafo em texto Mermaid
    if caminho:
        nos = ",".join(dict.fromkeys(caminho))  # sem repetir, na ordem em que rodaram
        texto += f"\tclassDef executado fill:#ffd166,stroke:#b8860b,stroke-width:2px,color:#000;\n\tclass {nos} executado;\n"
    return texto


def _salvar(nome: str, mermaid: str) -> None:
    """Salva o Mermaid em saida/<nome>.mmd (mermaid.live) e saida/<nome>.md (preview do VS Code)."""
    pasta = Path(__file__).resolve().parent.parent / "saida"  # a pasta desafio3/saida (criada logo abaixo)
    pasta.mkdir(exist_ok=True)
    (pasta / f"{nome}.mmd").write_text(mermaid, encoding="utf-8")
    (pasta / f"{nome}.md").write_text(f"# {nome}\n\n```mermaid\n{mermaid}\n```\n", encoding="utf-8")
    print(f"Salvo em desafio3/saida/{nome}.mmd e desafio3/saida/{nome}.md")


def salvar_mermaid(app, caminho=None, nome: str = "grafo") -> None:
    """Imprime o Mermaid (caminho em amarelo) e salva em saida/."""
    mermaid = mermaid_do_grafo(app, caminho)
    print("\nMERMAID (nós em amarelo = executaram):")
    print(mermaid)
    _salvar(nome, mermaid)


# ------------------------------------------------ os TIPOS de nó (PRONTO: não precisa mexer)
# TIPOS_DE_NO: nome do nó -> tipo (usado só para colorir o desenho). Novidade: o tipo JEV (decisão tipada).
TIPOS_DE_NO = {
    "receber": "função", "avaliar": "modelo de decisão", "encaminhar": "tool", "alertar_dado_sensivel": "função",
    "pedir_esclarecimento": "função", "pesquisar": "tool", "responder": "LLM",
}
# CORES_POR_TIPO: tipo -> cor de preenchimento no Mermaid.
CORES_POR_TIPO = {"modelo de decisão": "#ffd6e7", "LLM": "#cfe3ff", "tool": "#ead7ff", "função": "#ececec"}


def mermaid_por_tipo(app) -> str:
    """Mermaid do grafo com cada nó colorido pelo seu TIPO (JEV, LLM, tool ou função)."""
    grafo = app.get_graph()  # o grafo compilado, para listar os nós que existem
    texto = grafo.draw_mermaid()
    for i, (tipo, cor) in enumerate(CORES_POR_TIPO.items()):
        membros = [n for n, t in TIPOS_DE_NO.items() if t == tipo and n in grafo.nodes]
        if membros:
            texto += f"\tclassDef tipo{i} fill:{cor},stroke:#666,color:#000;\n\tclass {','.join(membros)} tipo{i};\n"
    return texto


def salvar_mermaid_por_tipo(app, nome: str = "grafo_por_tipo") -> None:
    """Imprime o Mermaid colorido por tipo e salva em saida/."""
    mermaid = mermaid_por_tipo(app)
    print("\nOS TIPOS DE NÓ: modelo de decisão (rosa) | LLM (azul) | tool (roxo) | função (cinza)")
    print(mermaid)
    _salvar(nome, mermaid)


# ------------------------------- 5 PERGUNTAS que testam o grafo por CAMINHOS diferentes (PRONTO: não precisa mexer)
# Rode:  python desafio3\\main.py --perguntas      (confere o caminho de cada uma; gasta 5 créditos se usar o JEV real)
# cada item: a pergunta, o caminho COMPLETO esperado e o que observar
PERGUNTAS_DE_TESTE = [
    {"pergunta": "Estou sem medicação e passando mal, preciso de atendimento agora",
     "caminho": ["receber", "avaliar", "encaminhar", "responder"],
     "observe": "URGENTE: p_urgente ~0,98. O risco vence qualquer outra regra e vai ao plantão."},
    {"pergunta": "Meu CPF é 123.456.789-00 e a senha do portal é abc123, podem verificar meu pedido?",
     "caminho": ["receber", "avaliar", "alertar_dado_sensivel"],
     "observe": "SENSÍVEL: p_sensivel ~0,99. O grafo recusa e alerta; o texto nem chega ao LLM."},
    {"pergunta": "Quero o passaporte, ou melhor, a segunda via do documento, não sei qual",
     "caminho": ["receber", "avaliar", "pedir_esclarecimento"],
     "observe": "INCERTO: a CONFIANÇA no assunto é baixa (~0,33). Em vez de adivinhar, o grafo pergunta."},
    {"pergunta": "Preciso saber como solicitar uma segunda via de um documento",
     "caminho": ["receber", "avaliar", "pesquisar", "responder"],
     "observe": "COM BASE: assunto 'segunda_via' com confiança 1,0: pesquisa o procedimento e o LLM redige a resposta."},
    {"pergunta": "Qual o prazo de restituição do imposto de renda de 2031?",
     "caminho": ["receber", "avaliar", "responder"],
     "observe": "SEM BASE: assunto 'outro' (confiança alta): o grafo admite que não sabe, sem pesquisar nem inventar."},
]


def rodar_perguntas(app) -> None:
    """Roda as 5 perguntas e mostra o caminho de cada uma, comparado com o esperado (✓ ou ✗)."""
    certas = 0  # quantas perguntas foram pelo caminho esperado
    for i, caso in enumerate(PERGUNTAS_DE_TESTE, start=1):
        estado, caminho = executar(app, caso["pergunta"])
        ok = caminho == caso["caminho"]  # o caminho aqui é determinístico: não há ciclo
        certas += ok
        print(f"\n[{i}] {caso['pergunta']}")
        print(f"    observe  : {caso['observe']}")
        print(f"    modelo de decisão: urgente={estado.get('p_urgente', 0):.2f} sensível={estado.get('p_sensivel', 0):.2f} "
              f"assunto={estado.get('assunto')!r} (confiança {estado.get('confianca', 0):.2f})")
        print(f"    caminho  : {' -> '.join(caminho)}")
        print(f"    {'✓' if ok else '✗'} esperado : {' -> '.join(caso['caminho'])}")
    print(f"\n{certas} de {len(PERGUNTAS_DE_TESTE)} perguntas no caminho esperado.")


if __name__ == "__main__":
    modelo = obter_modelo_real(padrao="openai")  # o LLM REAL que escreve a resposta (OpenAI por padrão; Ollama com PROVEDOR=ollama)
    jev = obter_jev()  # o decisor REAL: JEV (JEV_AI_API_KEY) ou Laya local ($env:JEV = "laya"); sem nenhum dos dois, o programa para
    print(f"LLM em uso: {modelo.nome} | decisões: {jev.nome}\n")
    app = construir_grafo(modelo, jev)  # o grafo compilado, pronto para executar
    rodar_perguntas(app)
    if "--perguntas" in sys.argv:
        raise SystemExit
    # No final: tudo o que aconteceu, nó a nó, e os desenhos do grafo.
    print("\n\n" + "#" * 70)
    print("VISÃO COMPLETA DE UMA EXECUÇÃO (a pergunta com base)")
    print("#" * 70)
    estado, caminho = mostrar_execucao(app, PERGUNTAS_DE_TESTE[3]["pergunta"])
    salvar_mermaid(app, caminho, nome="grafo_desafio3")
    salvar_mermaid_por_tipo(app)
