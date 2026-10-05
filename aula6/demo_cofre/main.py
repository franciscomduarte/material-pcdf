"""
DEMONSTRAÇÃO AO VIVO -- O cofre: um grafo mínimo com decisão e ciclo.  (esqueleto em 5 PONTOS DE CONTROLE)

A ideia: uma pessoa tenta abrir um cofre digitando a senha. Acertou: libera. Errou: tenta de novo.
Errou 3 vezes: bloqueia. É o menor processo que tem as três peças de um grafo:

    ESTADO (o que o processo sabe) · DECISÃO (para onde ir) · CICLO COM PARADA (repetir, mas com limite)

    START -> receber -> tentar ─┬─ ok ──────> liberar ──> END
                          ^     ├─ bloquear -> bloquear -> END      (errou MAX_TENTATIVAS vezes)
                          └─ erro ─┘                                (errou, ainda tem tentativa: tenta de novo)

Não há LLM aqui de propósito: um nó é só uma função. Um nó com LLM (desafios 1 e 2) é a mesma coisa.

Faça um ponto, confira, siga para o próximo:

    python demo_cofre\\conferir.py          # mostra quais pontos já passaram (✓), o próximo e DESENHA o grafo

JÁ PRONTO:  Estado, constantes, executar() e as funções para ver o que aconteceu.
SEU:        os NÓS, o ROTEADOR e a MONTAGEM, dentro de construir_grafo().
"""
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph  # noqa: F401  (você vai usar)

SENHA = "1234"
MAX_TENTATIVAS = 3


class Estado(TypedDict):
    entradas: list[str]   # as senhas que a pessoa "digita", na ordem (simuladas)
    tentativas: int       # quantas vezes já tentou (condição de parada do ciclo)
    acertou: bool         # a última senha estava certa?
    status: str           # "" | "liberado" | "bloqueado"


# ------------------------------------------------------------------ o grafo
def construir_grafo():
    """Monte e devolva o grafo COMPILADO.

    ---------------------------------------------------------------------------------------------
    O desafio tem DUAS FASES (o arquivo está organizado assim):
        FASE A -- construir as FUNÇÕES (os nós e o roteador), um bloco por ponto.
        FASE B -- LIGAR os pontos: add_node, add_edge e add_conditional_edges, um bloco por ponto.

    ORDEM DE TRABALHO, PONTO A PONTO (assim você recebe o ✓ logo):
        1) escreva a função do ponto N  (Fase A)
        2) ligue o ponto N              (Fase B)
        3) rode  python demo_cofre\\conferir.py   e só siga quando o ponto N estiver ✓

    ATENÇÕES:
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
        inicializa o estado do processo: {"tentativas": 0, "acertou": False, "status": ""}
        (as "entradas" já vêm de fora; o nó só devolve o que ELE inicializa)
    """
    #colocar a função 1 aqui
    # def receber(estado):
    def receber(estado):
        return {"tentativas": 0, "acertou": False, "status": ""}

    """
    FUNÇÃO PONTO 2 -- tentar.
        pega a senha da vez: estado["entradas"][estado["tentativas"]]  ("" se as entradas acabaram)
        devolve {"acertou": senha == SENHA, "tentativas": estado["tentativas"] + 1}
    """
    #colocar a função 2 aqui
    # def tentar(estado):
    def tentar(estado):
        i, entradas = estado["tentativas"], estado["entradas"]
        senha = entradas[i] if i < len(entradas) else ""
        return {"acertou": senha == SENHA, "tentativas": i + 1}

    """
    FUNÇÃO PONTO 3 -- liberar e o roteador.
        liberar: {"status": "liberado"}
        rotear_apos_tentar(estado) -> "ok" se estado["acertou"], senão "erro"     (só LÊ o estado)
    """
    #colocar as funções do ponto 3 aqui
    # def liberar(estado):
    def liberar(estado):
        return {"status": "liberado"}

    # def rotear_apos_tentar(estado):
    def rotear_apos_tentar(estado):
        return "ok" if estado["acertou"] else "erro"

    def rotear_apos_tentar(estado):
        return "ok" if estado["acertou"] else ("bloqueio" if estado["tentativas"] >= MAX_TENTATIVAS else "erro")

    """
    FUNÇÃO PONTO 4 -- o CICLO: não há função nova.
        o rótulo "erro" volta para o próprio nó `tentar` (é uma aresta, não um while!)
    """
    #no ponto 4 só a ligação muda

    """
    FUNÇÃO PONTO 5 -- a PARADA: bloquear, e EDITE rotear_apos_tentar (a do ponto 3):
        bloquear: {"status": "bloqueado"}
    """
    #colocar a função 5 aqui
    # def bloquear(estado):
    def bloquear(estado):
        return {"status": "bloqueado"}
    

    # ==============================================================================================
    # FASE B -- LIGAR OS PONTOS
    # ==============================================================================================

    """
    PONTO 1 -- receber.  Grafo: START -> receber -> END
        dica: construtor.add_node("receber", receber)  e  construtor.add_edge(START, "receber")
    """
    construtor = StateGraph(Estado)
    construtor.add_node("receber", receber)
    construtor.add_edge(START, "receber")

    # teste isolado do ponto 1: construtor.add_edge("receber", END)   (apague no ponto 2)

    """
    PONTO 2 -- tentar.  Grafo: START -> receber -> tentar -> END
        dica: add_node("tentar", tentar)  e  add_edge("receber", "tentar")
    """
    construtor.add_node("tentar", tentar)
    construtor.add_edge("receber", "tentar")
    

    # teste isolado do ponto 2: construtor.add_edge("tentar", END)   (apague no ponto 3)

    """
    PONTO 3 -- o caminho feliz.  tentar -> (ok) liberar -> END
        dica: add_node("liberar", liberar)
              add_conditional_edges("tentar", rotear_apos_tentar, {"ok": "liberar", "erro": END})
              add_edge("liberar", END)
        (até o ponto 4 existir, "erro" vai para END)
    """
    construtor.add_node("liberar", liberar)
    construtor.add_conditional_edges("tentar", rotear_apos_tentar, {"ok": "liberar", "erro": "tentar", "bloqueio": "bloquear"})

    """
    PONTO 4 -- o CICLO.  tentar -> (erro) tentar
        dica: no ponto 3, troque  "erro": END  por  "erro": "tentar"   <- um nó que volta para si mesmo
    """
    # ajustado no código do ponto 3

    """
    PONTO 5 -- a PARADA.  tentar -> (bloquear) bloquear -> END
        dica: add_node("bloquear", bloquear); add_edge("bloquear", END)
              acrescente ao mapa do ponto 3:  "bloquear": "bloquear"
    """
    construtor.add_node("bloquear", bloquear)
    construtor.add_edge("bloquear", END)
    return construtor.compile()


# ------------------------------------------------------------------ execução
def executar(app, entradas: list[str]):
    """Roda o grafo com as senhas digitadas e devolve (estado_final, caminho)."""
    estado: dict = {"entradas": entradas}
    caminho = []
    # recursion_limit baixo: se o seu ciclo não tiver parada, o erro (GraphRecursionError) aparece em segundos
    for passo in app.stream(estado, {"recursion_limit": 40}, stream_mode="updates"):
        for no, atualizacao in passo.items():
            caminho.append(no)
            estado.update(atualizacao)
    return estado, caminho


# ------------------------------------------------ ver o que aconteceu (PRONTO: não precisa mexer)
def mostrar_execucao(app, entradas: list[str]):
    """Roda o grafo e mostra, NÓ A NÓ, o que cada um escreveu no estado, e o resultado final."""
    print("=" * 70)
    print("SENHAS DIGITADAS:", entradas, "(a senha certa é", SENHA + ")")
    print("=" * 70)
    estado: dict = {"entradas": entradas}
    caminho = []
    for passo in app.stream(estado, {"recursion_limit": 40}, stream_mode="updates"):
        for no, atualizacao in passo.items():
            caminho.append(no)
            print(f"\n[{len(caminho)}] {no}")
            for campo, valor in atualizacao.items():
                print(f"      escreveu  {campo:11} = {valor!r}")
            estado.update(atualizacao)
    print("\n" + "-" * 70)
    print("CAMINHO PERCORRIDO:", " -> ".join(caminho))
    print(f"RESULTADO: {estado.get('status')} após {estado.get('tentativas')} tentativa(s)")
    return estado, caminho


def mermaid_do_grafo(app, caminho=None) -> str:
    """Devolve o Mermaid do grafo. Se `caminho` for dado, os nós que executaram saem destacados."""
    texto = app.get_graph().draw_mermaid()
    if caminho:
        nos = ",".join(dict.fromkeys(caminho))
        texto += f"\tclassDef executado fill:#ffd166,stroke:#b8860b,stroke-width:2px,color:#000;\n\tclass {nos} executado;\n"
    return texto


def salvar_mermaid(app, caminho=None, nome: str = "grafo") -> None:
    """Imprime o Mermaid e salva saida/<nome>.mmd (mermaid.live) e saida/<nome>.md (preview do VS Code)."""
    mermaid = mermaid_do_grafo(app, caminho)
    pasta = Path(__file__).resolve().parent / "saida"
    pasta.mkdir(exist_ok=True)
    (pasta / f"{nome}.mmd").write_text(mermaid, encoding="utf-8")
    (pasta / f"{nome}.md").write_text(f"# {nome}\n\n```mermaid\n{mermaid}\n```\n", encoding="utf-8")
    print("\nMERMAID (nós em amarelo = executaram):")
    print(mermaid)
    print(f"Salvo em demo_cofre/saida/{nome}.mmd e demo_cofre/saida/{nome}.md")


CASOS = [
    ["1234"],                     # acerta de primeira
    ["0000", "1234"],             # erra uma vez, depois acerta (o ciclo)
    ["0", "1", "2", "1234"],      # erra 3 vezes: bloqueia (a parada), nem chega a usar a 4ª senha
]

if __name__ == "__main__":
    app = construir_grafo()
    for entradas in CASOS:
        estado, caminho = executar(app, entradas)
        print("=" * 70)
        print("Senhas  :", entradas)
        print("Caminho :", " -> ".join(caminho))
        print("Resultado:", estado.get("status"), "| tentativas:", estado.get("tentativas"), "\n")

    # No final: tudo o que aconteceu, nó a nó, e o desenho do grafo com o caminho destacado.
    print("\n\n" + "#" * 70)
    print("VISÃO COMPLETA DE UMA EXECUÇÃO (erra uma vez e acerta: o ciclo)")
    print("#" * 70)
    estado, caminho = mostrar_execucao(app, CASOS[1])
    salvar_mermaid(app, caminho, nome="grafo_cofre")
