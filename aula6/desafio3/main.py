"""
DESAFIO 3 -- Decisões TIPADAS com o JEV: o grafo decide por PROBABILIDADE.  (esqueleto em 6 PONTOS DE CONTROLE)

No desafio 1 o LLM também decidia o caminho (urgente ou normal): você pedia "responda com UMA palavra" e depois
interpretava o texto. Aqui a decisão vem do JEV, um modelo que NÃO escreve texto: ele responde perguntas sobre o texto
com NÚMEROS (probabilidades) e com a CONFIANÇA da resposta. O grafo usa esses números para escolher entre 5 caminhos:

    START -> receber -> avaliar (JEV) ─┬─ urgente  ──> encaminhar ──> responder (LLM) ──> END
                                       ├─ sensivel ──> alertar_dado_sensivel ───────────> END
                                       ├─ incerto  ──> pedir_esclarecimento ────────────> END
                                       ├─ com_base ──> pesquisar ──> responder (LLM) ───> END
                                       └─ sem_base ──────────────> responder (LLM) ─────> END

LLM para ESCREVER, JEV para DECIDIR. Faça um ponto, confira, siga para o próximo:

    python desafio3\\conferir.py          # mostra quais pontos já passaram (✓), o próximo e DESENHA o grafo

JÁ PRONTO:  jev.py (o cliente do JEV: JevReal e JevMock), as PERGUNTAS_JEV, os LIMIARES, o Estado, a base, as tools,
            o prompt e executar().
SEU:        os NÓS, o ROTEADOR (que decide pelos números) e a MONTAGEM, dentro de construir_grafo().

ATENÇÃO: cada pergunta ao JEV REAL gasta 1 crédito da conta. Os testes (conferir.py) usam o JevMock: não gastam nada.
         `python desafio3\\main.py` usa decisor e LLM REAIS: o JEV (JEV_AI_API_KEY no .env) ou o Laya local ($env:JEV = "laya").
         Sem nenhum dos dois, o programa para e diz o que fazer: não há decisor nem LLM de mentira.
         A chave NUNCA vai no código nem no git.
"""
import sys                          # sys.path: permite importar provedor.py (na pasta aula6/)
from pathlib import Path            # caminhos de arquivos (a pasta saida/)
from typing import TypedDict        # o tipo do Estado (um dicionário com campos conhecidos)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # provedor.py (escolhe o LLM)
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))  # jev.py e modelo_mock.py (desta pasta)

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
    """Monte e devolva o grafo COMPILADO. `modelo` escreve (modelo.gerar(prompt)); `jev` decide (jev.decidir(texto, perguntas)).

    ---------------------------------------------------------------------------------------------
    O desafio tem DUAS FASES (o arquivo está organizado assim):
        FASE A -- construir as FUNÇÕES (os nós e o roteador), um bloco por ponto.
        FASE B -- LIGAR os pontos: add_node, add_edge e add_conditional_edges, um bloco por ponto.

    ORDEM DE TRABALHO, PONTO A PONTO (assim você recebe o ✓ logo):
        1) escreva a função do ponto N  (Fase A)
        2) ligue o ponto N              (Fase B)
        3) rode  python desafio3\\conferir.py   e só siga quando o ponto N estiver ✓

    ATENÇÕES:
      - As funções vão DENTRO de construir_grafo (mesma indentação dos placeholders): é ali que `modelo` e `jev` existem.
      - Para testar um ponto isolado, termine o grafo com `construtor.add_edge("<último nó>", END)`.
        Quando o ponto seguinte pedir, APAGUE essa linha.
      - Um nó devolve SÓ o que atualiza (um dict); o roteador só LÊ o estado e devolve um rótulo (texto).
    ---------------------------------------------------------------------------------------------
    """

    # ==============================================================================================
    # FASE A -- AS FUNÇÕES
    # ==============================================================================================

    """
    FUNÇÃO PONTO 1 -- receber.
        limpa a entrada e inicializa TODOS os 8 campos do Estado ("" / 0.0)
        dica: {"solicitacao": estado["solicitacao"].strip(), "p_urgente": 0.0, "p_sensivel": 0.0, "assunto": "", ...}
    """
    #colocar a função 1 aqui
    # def receber(estado):

    """
    FUNÇÃO PONTO 2 -- avaliar (nó do JEV: a decisão TIPADA).
        respostas = jev.decidir(estado["solicitacao"], PERGUNTAS_JEV)       # UMA chamada, 3 perguntas
        devolva os NÚMEROS, sem interpretar texto:
            "p_urgente":  respostas["urgente"]["noul"]            (probabilidade de "sim", 0 a 1)
            "p_sensivel": respostas["sensivel"]["noul"]
            "assunto":    respostas["assunto"]["choice"]          (a opção escolhida)
            "confianca":  respostas["assunto"]["confidence"]      (a confiança nela, 0 a 1)
    """
    #colocar a função 2 aqui
    # def avaliar(estado):

    """
    FUNÇÃO PONTO 3 -- o caminho URGENTE: encaminhar (tool), responder (LLM) e o ROTEADOR.
        encaminhar: {"encaminhamento": encaminhar_plantao(estado["solicitacao"])}
        responder:  {"resposta": modelo.gerar(prompt_responder(estado))}
        rotear_apos_avaliar(estado): se estado["p_urgente"] >= LIMIAR_URGENTE devolva "urgente"; senão "outros"
        (é o roteador que DECIDE PELOS NÚMEROS; ele só LÊ o estado)
    """
    #colocar as funções do ponto 3 aqui
    # def encaminhar(estado):

    # def responder(estado):

    # def rotear_apos_avaliar(estado):

    """
    FUNÇÃO PONTO 4 -- o DADO SENSÍVEL: alertar_dado_sensivel e EDITE o roteador.
        alertar_dado_sensivel: {"resposta": "Por segurança, não envie CPF, senhas ou números de cartão por aqui. ..."}  (e encerra)
        no roteador, DEPOIS da regra do urgente: se estado["p_sensivel"] >= LIMIAR_SENSIVEL devolva "sensivel"
        (a ORDEM das regras é a prioridade dos caminhos: risco à vida vem antes de dado sensível)
    """
    #colocar a função 4 aqui
    # def alertar_dado_sensivel(estado):

    """
    FUNÇÃO PONTO 5 -- o INCERTO: pedir_esclarecimento e EDITE o roteador.
        pedir_esclarecimento: {"resposta": "Não consegui entender com segurança qual é o seu assunto. Pode explicar ...?"}  (e encerra)
        no roteador, depois das regras anteriores: se estado["confianca"] < LIMIAR_CONFIANCA devolva "incerto"
        (o JEV devolve a CONFIANÇA: com ela o grafo pode NÃO adivinhar)
    """
    #colocar a função 5 aqui
    # def pedir_esclarecimento(estado):

    """
    FUNÇÃO PONTO 6 -- COM BASE e SEM BASE: pesquisar (tool) e a regra final do roteador.
        pesquisar: {"informacao": BASE_CONHECIMENTO.get(estado["assunto"], "")}      ("" se o assunto não está na base)
        roteador, regra final: "com_base" se estado["assunto"] está em BASE_CONHECIMENTO, senão "sem_base"
        (o assunto "outro" não está na base: o grafo admite que não sabe e o LLM NÃO inventa)
    """
    #colocar a função 6 aqui
    # def pesquisar(estado):

    # ==============================================================================================
    # FASE B -- LIGAR OS PONTOS
    # ==============================================================================================

    """
    PONTO 1 -- receber.  Grafo: START -> receber -> END
        dica: construtor.add_node("receber", receber)  e  construtor.add_edge(START, "receber")
    """
    construtor = StateGraph(Estado)
    # construtor.add_node("receber", receber)
    # construtor.add_edge(START, "receber")

    # teste isolado do ponto 1: construtor.add_edge("receber", END)   (apague no ponto 2)

    """
    PONTO 2 -- avaliar (JEV).  Grafo: START -> receber -> avaliar -> END
        dica: add_node("avaliar", avaliar)  e  add_edge("receber", "avaliar")
    """
    # construtor.add_node("avaliar", avaliar)
    # construtor.add_edge("receber", "avaliar")

    # teste isolado do ponto 2: construtor.add_edge("avaliar", END)   (apague no ponto 3)

    """
    PONTO 3 -- urgente.  avaliar -> (urgente) encaminhar -> responder -> END ;  (outros) -> END
        dica: add_node de encaminhar e de responder;
              add_conditional_edges("avaliar", rotear_apos_avaliar, {"urgente": "encaminhar", "outros": END})
              add_edge("encaminhar", "responder")  e  add_edge("responder", END)
    """
    # construtor.add_node("encaminhar", encaminhar)
    # construtor.add_node("responder", responder)
    # construtor.add_conditional_edges(...)
    # construtor.add_edge("encaminhar", "responder")
    # construtor.add_edge("responder", END)

    """
    PONTO 4 -- dado sensível.  avaliar -> (sensivel) alertar_dado_sensivel -> END
        dica: add_node("alertar_dado_sensivel", alertar_dado_sensivel); add_edge("alertar_dado_sensivel", END)
              no mapa de add_conditional_edges acrescente  "sensivel": "alertar_dado_sensivel"
    """
    # construtor.add_node("alertar_dado_sensivel", alertar_dado_sensivel)
    # construtor.add_edge("alertar_dado_sensivel", END)

    """
    PONTO 5 -- incerto.  avaliar -> (incerto) pedir_esclarecimento -> END
        dica: add_node("pedir_esclarecimento", pedir_esclarecimento); add_edge("pedir_esclarecimento", END)
              no mapa acrescente  "incerto": "pedir_esclarecimento"
    """
    # construtor.add_node("pedir_esclarecimento", pedir_esclarecimento)
    # construtor.add_edge("pedir_esclarecimento", END)

    """
    PONTO 6 -- com base e sem base.  avaliar -> (com_base) pesquisar -> responder ;  (sem_base) -> responder
        dica: add_node("pesquisar", pesquisar); add_edge("pesquisar", "responder")
              no mapa: TROQUE  "outros": END  por  "com_base": "pesquisar"  e  "sem_base": "responder"
              (o mapa final tem 5 rótulos: urgente, sensivel, incerto, com_base e sem_base)
    """
    # construtor.add_node("pesquisar", pesquisar)
    # construtor.add_edge("pesquisar", "responder")
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
    pasta = Path(__file__).resolve().parent / "saida"  # a pasta desafio3/saida (criada logo abaixo)
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
