"""
DESAFIO 2 -- Despacho de viatura, como grafo.  (esqueleto em 8 PONTOS DE CONTROLE)

Leia o enunciado em README.md. Você NÃO monta o grafo de uma vez: são 8 pontos de controle.
Faça um, confira, siga para o próximo:

    python desafio2\\conferir.py          # mostra quais pontos já passaram (✓) e qual é o próximo

JÁ PRONTO:  Estado, BAIRROS, constantes, chamar_mcp() (cliente do MCP Server), buscar_chuva() (API do clima,
            já tolerante a falhas), os PROMPTS (prompt_*), as funções que interpretam o LLM e executar().
SEU:        os NÓS, os ROTEADORES e a MONTAGEM, dentro de construir_grafo().

O grafo completo:

    START -> receber -> extrair -> localizar ─┬─ ok ────────> buscar_unidades ─┬─ ok ──────> consultar_clima
                                              │                                │                   │
                                              └─ sem_local -> pedir_endereco   └─ sem_unidade      v
                                                                  │               │        calcular_tempo
                                                                  v               v                │
                                                                 END           escalar ─> END      ├─ normal ──┐
                                                                                                   └─ apoio    │
                                                                                                      │        │
                                                                                               acionar_apoio   │
                                                                                                      └───┬────┘
                                                                                                          v
                                                                                        ┌────────> gerar_ordem
                                                                                        │               │
                                                                                     revisar            v
                                                                                        ^            validar ─ fim ─> END
                                                                                        └─── erro ─────┘   (fim = válida OU tentativas >= MAX)

MODELO: este desafio NÃO usa Mock: roda só com LLM REAL (OpenAI por padrão, como nas Aulas 4 e 5; Ollama com
        $env:PROVEDOR = "ollama"). Sem OPENAI_API_KEY (ou com o Ollama fora do ar) o programa PARA e diz o que fazer.
        Os TESTES (conferir.py) também chamam o LLM real: conferem o CAMINHO do grafo, não o texto que o LLM escreve.
Sem internet, o clima fica indisponível e o grafo segue:          $env:CLIMA_OFFLINE = "1"
"""
import asyncio                      # o cliente MCP é assíncrono; asyncio.run() o executa
import json                         # ler as respostas do MCP, da API e do LLM (JSON)
import os                           # variáveis de ambiente (CLIMA_OFFLINE) e os.devnull
import sys                          # sys.path (achar provedor.py) e sys.executable (subir o MCP Server)
import urllib.request               # chamada HTTP à API do clima (biblioteca padrão)
from pathlib import Path            # caminhos de arquivos (servidor MCP, pasta saida/)
from typing import TypedDict        # o tipo do Estado (um dicionário com campos conhecidos)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # provedor.py

from langgraph.graph import END, START, StateGraph  # noqa: F401  StateGraph monta o grafo; START e END são a entrada e a saída

from mcp import ClientSession, StdioServerParameters  # cliente MCP: a conversa e os parâmetros para subir o servidor
from mcp.client.stdio import stdio_client             # fala com o servidor MCP por stdin/stdout

from provedor import obter_modelo_real    # escolhe o LLM REAL (OpenAI ou Ollama) pelo .env; sem ele, o programa para

MAX_TENTATIVAS = 3  # limite de vezes que o ciclo gerar_ordem -> validar -> revisar pode repetir (a CONDIÇÃO DE PARADA)
LIMITE_APOIO_MIN = 8      # gravidade alta + tempo de chegada acima disto (minutos) -> aciona apoio
VELOCIDADE_KMH = 40       # velocidade média da viatura: tempo = distância / velocidade
SERVER_MCP = str(Path(__file__).resolve().parents[0] / "mcp_unidades.py")

# BAIRROS: bairro (minúsculas) -> (latitude, longitude). É o "geocodificador" de mentira: em produção seria uma API.
BAIRROS = {
    "asa sul": (-15.8267, -47.9218),
    "asa norte": (-15.7633, -47.8829),
    "taguatinga": (-15.8330, -48.0570),
    "ceilândia": (-15.8190, -48.1070),
    "sobradinho": (-15.6500, -47.7900),
    "gama": (-16.0200, -48.0600),
}


class Estado(TypedDict):
    """O ESTADO do grafo: o que circula entre os nós. Cada nó lê daqui e devolve SÓ o que mudou."""
    solicitacao: str      # o texto da ocorrência (a entrada do grafo)
    tipo: str             # escrito por extrair (LLM): o tipo da ocorrência (ex.: assalto)
    gravidade: str        # escrito por extrair (LLM): "alta" | "baixa"; decide se aciona apoio
    bairro: str           # escrito por extrair (LLM): o bairro citado ("" = não citou)
    latitude: float       # escrito por localizar (tool): 0.0 = não localizou (caminho pedir_endereco)
    longitude: float      # escrito por localizar (tool)
    unidades: list        # escrito por buscar_unidades (MCP): da mais próxima para a mais distante ([] = nenhuma, caminho escalar)
    chuva_mm: float       # escrito por consultar_clima (API): chuva agora em mm; -1 = clima indisponível (o grafo segue)
    tempo_min: float      # escrito por calcular_tempo (tool): minutos até a unidade mais próxima chegar
    observacao: str       # escrito por calcular_tempo e acionar_apoio: apoio / clima, para constar da ordem
    ordem: str            # escrito por gerar_ordem (LLM), ou a mensagem de pedir_endereco / escalar: a SAÍDA do grafo
    valida: bool          # escrito por validar (LLM): True se a ordem cita a unidade; decide se o ciclo continua
    tentativas: int       # escrito por gerar_ordem: quantas ordens já foram geradas; o roteador compara com MAX_TENTATIVAS
    feedback: str         # o motivo da reprovação: validar escreve, revisar reforça e gerar_ordem lê para corrigir


# ----------------------------------------------- integrações (PRONTAS: não precisa mexer)
def chamar_mcp(ferramenta: str, argumentos: dict) -> list:
    """(PRONTA) Chama uma tool do MCP Server (mcp_unidades.py) por stdio e devolve a lista de resultados (dicts)."""
    async def _chamar():  # o cliente MCP é assíncrono: a conversa inteira acontece aqui dentro
        params = StdioServerParameters(command=sys.executable, args=[SERVER_MCP])  # como subir o servidor: "python mcp_unidades.py"
        with open(os.devnull, "w") as silencio:  # descarta as mensagens de log do servidor
            async with stdio_client(params, errlog=silencio) as (leitura, escrita):  # sobe o servidor e abre o canal
                async with ClientSession(leitura, escrita) as sessao:  # a conversa MCP
                    await sessao.initialize()  # "aperto de mão" do protocolo
                    resposta = await sessao.call_tool(ferramenta, argumentos)  # chama a tool pelo NOME, com os parâmetros
                    if resposta.is_error:
                        raise RuntimeError(f"MCP {ferramenta}: {resposta.content}")
                    return [json.loads(item.text) for item in resposta.content]  # cada resultado chega como texto JSON

    return asyncio.run(_chamar())  # roda a conversa e devolve a lista de resultados


def buscar_chuva(latitude: float, longitude: float) -> float:
    """(PRONTA) API HTTP Open-Meteo (sem chave). Devolve mm de chuva agora, ou -1 se a API falhar (o grafo SEGUE)."""
    if os.getenv("CLIMA_OFFLINE") == "1":  # CLIMA_OFFLINE=1 pula a internet (testes e aula sem rede)
        return -1.0
    url = (  # a consulta: coordenadas da ocorrência e o campo precipitation (chuva agora)
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}&current=precipitation"
    )
    try:
        with urllib.request.urlopen(url, timeout=5) as r:  # timeout: não deixa o grafo esperando a API para sempre
            return float(json.load(r)["current"]["precipitation"])  # a API devolve {"current": {"precipitation": mm}}
    except (OSError, ValueError, KeyError):  # sem rede, resposta inválida ou campo ausente
        return -1.0  # sinal de "clima indisponível": o grafo SEGUE (falha de API não derruba o grafo)


# ------------------------------------------------ prompts (prontos: use nos seus nós)
# Cada um devolve o TEXTO do prompt a partir do estado. Você o passa a modelo.gerar(...).
# (A 1ª linha "TAREFA: <nome>" só rotula o prompt.)
def prompt_extrair(estado: Estado) -> str:
    """O prompt do nó extrair: pede JSON com tipo, gravidade e bairro (null no que não aparece)."""
    return (
        "TAREFA: extrair\n"
        "Extraia da solicitação o tipo da ocorrência, a gravidade ('alta' ou 'baixa') e o bairro.\n"
        'Responda só com JSON: {"tipo": ..., "gravidade": ..., "bairro": ...}. '
        "Use null no que não estiver na solicitação.\n"
        f"Solicitação: {estado['solicitacao']}"
    )


def _fatos(estado: Estado) -> str:
    """Os FATOS que a ordem pode usar (todos vêm do estado). Se não está aqui, o LLM não pode citar."""
    return (
        f"Unidade: {estado['unidades'][0]['nome']}\n"
        f"Bairro: {estado['bairro']}\n"
        f"Tipo: {estado['tipo']}\n"
        f"Tempo: {estado['tempo_min']} min\n"
        f"Observação: {estado['observacao']}\n"
    )


def prompt_gerar_ordem(estado: Estado) -> str:
    """O prompt do nó gerar_ordem: usa SOMENTE os fatos do estado (e a correção pedida pela revisão, se houver)."""
    # na revisão, o motivo da reprovação volta ao prompt para o LLM corrigir
    correcao = f"Correção solicitada: {estado['feedback']}\n" if estado["feedback"] else ""
    return (
        "TAREFA: gerar_ordem\n"
        "Redija uma ordem de serviço de uma frase, usando SOMENTE os fatos abaixo.\n"
        f"{correcao}FATOS:\n{_fatos(estado)}"
    )


def prompt_validar(estado: Estado) -> str:
    """O prompt do nó validar: o LLM só confere se a ordem cita a unidade despachada e responde OK ou ERRO."""
    return (
        "TAREFA: validar\n"
        "A ordem é válida se citar a unidade despachada. Responda apenas 'OK' ou 'ERRO: <motivo>'.\n"
        f"Unidade: {estado['unidades'][0]['nome']}\n"
        f"Ordem: {estado['ordem']}"
    )


# ------------------------- interpretar a resposta do LLM (texto livre -> valor que o grafo entende)
def interpretar_extracao(texto: str) -> dict:
    """Do JSON do LLM para {"tipo", "gravidade", "bairro"} (gravidade só 'alta' ou 'baixa'; null vira '')."""
    try:
        dados = json.loads(texto[texto.index("{"): texto.rindex("}") + 1])  # pega só o trecho entre a 1ª { e a última }
    except ValueError:  # sem JSON na resposta: segue com campos vazios (o grafo decide o que fazer)
        dados = {}
    return {
        "tipo": dados.get("tipo") or "",  # null/ausente vira ""
        "gravidade": "alta" if dados.get("gravidade") == "alta" else "baixa",  # só dois valores: o roteador compara com "alta"
        "bairro": dados.get("bairro") or "",  # "" faz localizar não achar e o grafo pedir o endereço
    }


def ordem_aprovada(texto: str) -> bool:
    """Transforma a resposta do validador em True/False (é o que vai para estado['valida']).
    'OK' / 'ok.' -> True; 'ERRO: ...' -> False."""
    return texto.strip().upper().startswith("OK")


# ------------------------------------------------------------------ o grafo
def construir_grafo(modelo):
    """Monte e devolva o grafo COMPILADO. `modelo` tem um método: modelo.gerar(prompt) -> texto.

    ---------------------------------------------------------------------------------------------
    O desafio tem DUAS FASES (o arquivo está organizado assim):
        FASE A -- construir as FUNÇÕES (os nós e os roteadores), um bloco por ponto.
        FASE B -- LIGAR os pontos: add_node, add_edge e add_conditional_edges, um bloco por ponto.

    ORDEM DE TRABALHO, PONTO A PONTO (assim você recebe o ✓ logo):
        1) escreva as funções do ponto N  (Fase A)
        2) ligue o ponto N                (Fase B)
        3) rode  python desafio2\\conferir.py   e só siga quando o ponto N estiver ✓

    ATENÇÕES:
      - As funções vão DENTRO de construir_grafo (mesma indentação dos placeholders): é ali que
        `modelo` existe. Fora dela dá NameError: name 'modelo' is not defined.
      - Para testar um ponto isolado, termine o grafo com `construtor.add_edge("<último nó>", END)`.
        Quando o ponto seguinte pedir, APAGUE essa linha (senão o nó termina o grafo e segue adiante ao mesmo tempo).
      - Um nó devolve SÓ o que atualiza (um dict); um roteador só LÊ o estado e devolve um rótulo (texto).
    ---------------------------------------------------------------------------------------------
    """

    # ==============================================================================================
    # FASE A -- AS FUNÇÕES
    # ==============================================================================================

    """
    FUNÇÃO PONTO 1 -- receber (função).
        limpa a entrada e inicializa TODOS os 14 campos do Estado ("" / 0.0 / [] / False / 0),
        com uma exceção: chuva_mm começa em -1.0 (= clima indisponível)
        dica: {"solicitacao": estado["solicitacao"].strip(), "tipo": "", ...}
    """
    #colocar a função 1 aqui
    # def receber(estado):

    """
    FUNÇÃO PONTO 2 -- extrair (LLM).
        texto = modelo.gerar(prompt_extrair(estado))
        devolva interpretar_extracao(texto)   (já vem como {"tipo", "gravidade", "bairro"})
    """
    #colocar a função 2 aqui
    # def extrair(estado):

    """
    FUNÇÃO PONTO 3 -- localizar (tool local), pedir_endereco (função) e o roteador.
        localizar: BAIRROS.get(estado["bairro"].lower()) -> {"latitude": ..., "longitude": ...}  (0.0 e 0.0 se não achou)
        pedir_endereco: {"ordem": "Não consegui localizar a ocorrência. Informe o bairro (ex.: Asa Sul, Taguatinga)."}
        rotear_apos_localizar(estado) -> "ok" se estado["latitude"] (não zero), senão "sem_local"
    """
    #colocar as funções do ponto 3 aqui
    # def localizar(estado):

    # def pedir_endereco(estado):

    # def rotear_apos_localizar(estado):

    """
    FUNÇÃO PONTO 4 -- buscar_unidades (MCP), escalar (função) e o roteador.
        buscar_unidades: chamar_mcp("unidades_proximas", {"latitude": ..., "longitude": ..., "raio_km": 20, "limite": 2})
                         -> {"unidades": <lista devolvida>}
        escalar: {"ordem": f"Nenhuma unidade com viatura disponível em 20 km de {bairro}: ocorrência escalada ao comando."}
        rotear_apos_buscar(estado) -> "ok" se houver unidades, senão "sem_unidade"
    """
    #colocar as funções do ponto 4 aqui
    # def buscar_unidades(estado):

    # def escalar(estado):

    # def rotear_apos_buscar(estado):

    """
    FUNÇÃO PONTO 5 -- consultar_clima (API) e calcular_tempo (tool local).
        consultar_clima: {"chuva_mm": buscar_chuva(latitude, longitude)}   (-1 = indisponível; o grafo SEGUE)
        calcular_tempo: tempo = unidades[0]["distancia_km"] / VELOCIDADE_KMH * 60 (minutos); se chuva_mm > 0, multiplique por 1.5
                        observacao = "Clima indisponível: tempo sem ajuste por chuva." quando chuva_mm < 0 (senão "")
                        devolva {"tempo_min": round(tempo, 1), "observacao": observacao}
    """
    #colocar as funções do ponto 5 aqui
    # def consultar_clima(estado):

    # def calcular_tempo(estado):

    """
    FUNÇÃO PONTO 6 -- acionar_apoio, o roteador e gerar_ordem (LLM).
        acionar_apoio: acrescenta a observacao "Apoio: <nome da 2ª unidade>." (ou "Sem unidade de apoio no raio.")
        rotear_apos_tempo(estado) -> "apoio" se gravidade == "alta" E tempo_min > LIMITE_APOIO_MIN, senão "normal"
        gerar_ordem: {"ordem": modelo.gerar(prompt_gerar_ordem(estado)), "tentativas": estado["tentativas"] + 1}
    """
    #colocar as funções do ponto 6 aqui
    # def acionar_apoio(estado):

    # def rotear_apos_tempo(estado):

    # def gerar_ordem(estado):

    """
    FUNÇÃO PONTO 7 -- o CICLO: validar (LLM), revisar e o roteador de validar.
        validar: texto = modelo.gerar(prompt_validar(estado)); {"valida": ordem_aprovada(texto), "feedback": "" se ok senão o texto}
        revisar: {"feedback": f"corrija — {estado['feedback']}"}
        rotear_apos_validar(estado) -> "fim" se estado["valida"], senão "erro"
    """
    #colocar as funções do ponto 7 aqui
    # def validar(estado):

    # def revisar(estado):

    # def rotear_apos_validar(estado):

    """
    FUNÇÃO PONTO 8 -- a PARADA: não há função nova. EDITE rotear_apos_validar (a do ponto 7):
        se NÃO é válida e estado["tentativas"] >= MAX_TENTATIVAS -> devolva também "fim"
        a condição de parada é lida do ESTADO, não de uma variável local
    """
    #no ponto 8 você só acrescenta duas linhas em rotear_apos_validar

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
    PONTO 2 -- extrair.  Grafo: START -> receber -> extrair -> END
    """
    # construtor.add_node("extrair", extrair)
    # construtor.add_edge("receber", "extrair")

    # teste isolado do ponto 2: construtor.add_edge("extrair", END)   (apague no ponto 3)

    """
    PONTO 3 -- localizar.  extrair -> localizar -> (ok) ... | (sem_local) pedir_endereco -> END
        dica: add_node de localizar e de pedir_endereco; add_edge("extrair", "localizar")
              add_conditional_edges("localizar", rotear_apos_localizar, {"ok": ..., "sem_local": "pedir_endereco"})
              add_edge("pedir_endereco", END)
        (até o ponto 4 existir, "ok" vai para END)
    """
    # construtor.add_node("localizar", localizar)
    # construtor.add_node("pedir_endereco", pedir_endereco)
    # construtor.add_edge("extrair", "localizar")
    # construtor.add_conditional_edges(...)
    # construtor.add_edge("pedir_endereco", END)

    # teste isolado do ponto 3: rode o conferir ("sem_local" já fecha com END)

    """
    PONTO 4 -- buscar_unidades.  (ok) buscar_unidades -> (ok) ... | (sem_unidade) escalar -> END
        dica: no ponto 3, troque "ok": END por "ok": "buscar_unidades"
              add_node de buscar_unidades e de escalar
              add_conditional_edges("buscar_unidades", rotear_apos_buscar, {"ok": ..., "sem_unidade": "escalar"})
              add_edge("escalar", END)
        (até o ponto 5 existir, "ok" vai para END)
    """
    # construtor.add_node("buscar_unidades", buscar_unidades)
    # construtor.add_node("escalar", escalar)
    # construtor.add_conditional_edges(...)
    # construtor.add_edge("escalar", END)

    # teste isolado do ponto 4: rode o conferir ("sem_unidade" já fecha com END)

    """
    PONTO 5 -- clima e tempo.  (ok) consultar_clima -> calcular_tempo
        dica: no ponto 4, "ok" passa a ir para "consultar_clima"
              add_node de consultar_clima e de calcular_tempo; add_edge("consultar_clima", "calcular_tempo")
    """
    # construtor.add_node("consultar_clima", consultar_clima)
    # construtor.add_node("calcular_tempo", calcular_tempo)
    # construtor.add_edge("consultar_clima", "calcular_tempo")

    # teste isolado do ponto 5: construtor.add_edge("calcular_tempo", END)   (apague no ponto 6)

    """
    PONTO 6 -- apoio e ordem.  calcular_tempo -> (apoio) acionar_apoio -> gerar_ordem | (normal) gerar_ordem
        dica: add_node de acionar_apoio e de gerar_ordem
              add_conditional_edges("calcular_tempo", rotear_apos_tempo, {"apoio": "acionar_apoio", "normal": "gerar_ordem"})
              add_edge("acionar_apoio", "gerar_ordem")
    """
    # construtor.add_node("acionar_apoio", acionar_apoio)
    # construtor.add_node("gerar_ordem", gerar_ordem)
    # construtor.add_conditional_edges(...)
    # construtor.add_edge("acionar_apoio", "gerar_ordem")

    # teste isolado do ponto 6: construtor.add_edge("gerar_ordem", END)   (apague no ponto 7)

    """
    PONTO 7 -- o CICLO.  gerar_ordem -> validar -> (erro) revisar -> gerar_ordem | (fim) END
        dica: add_node de validar e de revisar; add_edge("gerar_ordem", "validar")
              add_conditional_edges("validar", rotear_apos_validar, {"fim": END, "erro": "revisar"})
              add_edge("revisar", "gerar_ordem")   <- o ciclo é UMA ARESTA do grafo (nada de while dentro de um nó!)
    """
    # construtor.add_node("validar", validar)
    # construtor.add_node("revisar", revisar)
    # construtor.add_edge("gerar_ordem", "validar")
    # construtor.add_conditional_edges(...)
    # construtor.add_edge("revisar", "gerar_ordem")

    """
    PONTO 8 -- a PARADA.  não há ligação nova: o mapa do ponto 7 já leva "fim" ao END.
        o que muda é o roteador (Fase A, ponto 8). Confira: o ciclo para em MAX_TENTATIVAS.
    """
    return construtor.compile()


# ------------------------------------------------------------------ execução
def executar(app, solicitacao: str):
    """Roda o grafo e devolve (estado_final, caminho). O caminho vem do stream de atualizações."""
    estado: dict = {"solicitacao": solicitacao}  # o estado acumulado: começa só com a solicitação
    caminho = []  # os nomes dos nós, na ordem em que rodaram
    # recursion_limit baixo: se o seu ciclo não tiver parada, o erro (GraphRecursionError) aparece em segundos
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
    """Roda o grafo e mostra, NÓ A NÓ, tudo o que aconteceu até a ordem (ou a mensagem final) ficar pronta.

    Para cada nó: o que ele escreveu no estado. No fim: o caminho, os fatos que decidiram o rumo
    (local, unidades, clima, tempo, apoio, validação) e como a saída foi montada. Devolve (estado, caminho).
    """
    print("=" * 70)
    print("SOLICITAÇÃO:", solicitacao)
    print("=" * 70)
    estado: dict = {"solicitacao": solicitacao}  # o estado acumulado: começa só com a solicitação
    caminho = []  # os nomes dos nós, na ordem em que rodaram
    for passo in app.stream(estado, {"recursion_limit": 40}, stream_mode="updates"):  # cada passo: {nome_do_nó: o que ele escreveu}
        for no, atualizacao in passo.items():
            caminho.append(no)
            print(f"\n[{len(caminho)}] {no}")
            if not atualizacao:
                print("      (não escreveu nada no estado)")
            for campo, valor in atualizacao.items():
                print(f"      escreveu  {campo:15} = {_curto(valor)}")
            estado.update(atualizacao)  # aplica a atualização ao estado, como o LangGraph faz

    print("\n" + "-" * 70)
    print("CAMINHO PERCORRIDO:", " -> ".join(caminho))
    print("FATOS QUE DECIDIRAM O RUMO:")
    print(f"      ocorrência : {estado.get('tipo')!r}, gravidade {estado.get('gravidade')!r}, bairro {estado.get('bairro')!r}")
    print(f"      localizada : {'sim' if estado.get('latitude') else 'não (sem coordenadas)'}")
    unidades = estado.get("unidades") or []
    print(f"      unidades   : {[u['nome'] for u in unidades] or 'nenhuma no raio'}")
    chuva = estado.get("chuva_mm", -1)
    print(f"      clima      : {'indisponível' if chuva < 0 else f'{chuva} mm'}  |  tempo estimado: {estado.get('tempo_min')} min")
    print(f"      tentativas : {estado.get('tentativas')}  |  ordem válida: {estado.get('valida')}")
    if not estado.get("latitude"):
        origem = "o bairro não foi localizado: o grafo pediu o endereço ao usuário"
    elif not unidades:
        origem = "não havia unidade com viatura no raio: o grafo escalou ao comando"
    elif "apoio" in caminho or "acionar_apoio" in caminho:
        origem = f"{estado.get('tentativas')} tentativa(s), COM apoio (gravidade alta e tempo acima de {LIMITE_APOIO_MIN} min)"
    else:
        origem = f"{estado.get('tentativas')} tentativa(s), sem apoio"
    print(f"COMO A SAÍDA FOI MONTADA: {origem}")
    print(f"ORDEM/MENSAGEM: {estado.get('ordem')}")
    return estado, caminho


def mermaid_do_grafo(app, caminho=None) -> str:
    """Devolve o Mermaid do grafo. Se `caminho` for dado, os nós que executaram saem destacados."""
    texto = app.get_graph().draw_mermaid()  # o desenho do grafo em texto Mermaid
    if caminho:
        nos = ",".join(dict.fromkeys(caminho))  # sem repetir, na ordem em que rodaram
        texto += f"\tclassDef executado fill:#ffd166,stroke:#b8860b,stroke-width:2px,color:#000;\n\tclass {nos} executado;\n"
    return texto


def salvar_mermaid(app, caminho=None, nome: str = "grafo", pasta_base=None) -> None:
    """Imprime o Mermaid e salva saida/<nome>.mmd (cole em https://mermaid.live) e saida/<nome>.md (preview do VS Code)."""
    mermaid = mermaid_do_grafo(app, caminho)  # o texto Mermaid (com o caminho destacado, se houver)
    pasta = Path(pasta_base or Path(__file__).resolve().parent) / "saida"  # a pasta desafio2/saida (criada logo abaixo)
    pasta.mkdir(exist_ok=True)
    (pasta / f"{nome}.mmd").write_text(mermaid, encoding="utf-8")
    (pasta / f"{nome}.md").write_text(f"# {nome}\n\n```mermaid\n{mermaid}\n```\n", encoding="utf-8")
    print("\nMERMAID (nós em amarelo = executaram):")
    print(mermaid)
    print(f"Salvo em desafio2/saida/{nome}.mmd e desafio2/saida/{nome}.md")


# ------------------------------------------------ os TIPOS de nó (PRONTO: não precisa mexer)
# Cada nó do grafo tem um tipo. Para o grafo, tudo é "função que lê o estado e devolve uma atualização".
# TIPOS_DE_NO: nome do nó -> tipo (usado só para colorir o desenho).
TIPOS_DE_NO = {
    "receber": "função", "extrair": "LLM", "localizar": "tool", "pedir_endereco": "função",
    "buscar_unidades": "MCP", "escalar": "função", "consultar_clima": "API", "calcular_tempo": "tool",
    "acionar_apoio": "função", "gerar_ordem": "LLM", "validar": "LLM", "revisar": "função",
}
# CORES_POR_TIPO: tipo -> cor de preenchimento no Mermaid.
CORES_POR_TIPO = {"LLM": "#cfe3ff", "MCP": "#ffe2b8", "API": "#d4f0c8", "tool": "#ead7ff", "função": "#ececec"}


def mermaid_por_tipo(app) -> str:
    """Mermaid do grafo com cada nó colorido pelo seu TIPO (LLM, MCP, API, tool ou função)."""
    grafo = app.get_graph()  # o grafo compilado, para listar os nós que existem
    texto = grafo.draw_mermaid()
    for i, (tipo, cor) in enumerate(CORES_POR_TIPO.items()):
        membros = [n for n, t in TIPOS_DE_NO.items() if t == tipo and n in grafo.nodes]
        if membros:
            texto += f"\tclassDef tipo{i} fill:{cor},stroke:#666,color:#000;\n\tclass {','.join(membros)} tipo{i};\n"
    return texto


def salvar_mermaid_por_tipo(app, nome: str = "grafo_por_tipo", pasta_base=None) -> None:
    """Imprime o Mermaid colorido por tipo e salva em saida/<nome>.mmd e .md (como salvar_mermaid)."""
    mermaid = mermaid_por_tipo(app)
    pasta = Path(pasta_base or Path(__file__).resolve().parent) / "saida"  # a pasta desafio2/saida (criada logo abaixo)
    pasta.mkdir(exist_ok=True)
    (pasta / f"{nome}.mmd").write_text(mermaid, encoding="utf-8")
    (pasta / f"{nome}.md").write_text(f"# {nome}\n\n```mermaid\n{mermaid}\n```\n", encoding="utf-8")
    print("\nOS TIPOS DE NÓ: LLM (azul) | MCP (laranja) | API (verde) | tool (roxo) | função (cinza)")
    print(mermaid)
    print(f"Salvo em desafio2/saida/{nome}.mmd e desafio2/saida/{nome}.md")


# ------------------------------- 5 PERGUNTAS que testam o grafo por CAMINHOS diferentes (PRONTO: não precisa mexer)
# Rode:  python desafio2\\main.py --perguntas      (confere o caminho de cada uma; vale para o grafo COMPLETO)
# o INÍCIO do caminho de quem tem local e unidade (as perguntas 1, 2 e 4 compartilham esse começo)
CAMINHO_ATE_TEMPO = ["receber", "extrair", "localizar", "buscar_unidades", "consultar_clima", "calcular_tempo"]
# cada item: a ocorrência, o começo do caminho esperado, o nó em que o caminho TERMINA e o que observar
PERGUNTAS_DE_TESTE = [
    {"pergunta": "Assalto em andamento em Taguatinga, preciso de uma viatura",
     "caminho": CAMINHO_ATE_TEMPO + ["gerar_ordem"], "termina_em": "validar",
     "observe": "GRAVIDADE ALTA, MAS PERTO: o tempo fica abaixo de 8 min, então NÃO aciona apoio. Passa pelo ciclo gerar_ordem -> validar."},
    {"pergunta": "Homem ferido em briga em Sobradinho",
     "caminho": CAMINHO_ATE_TEMPO + ["acionar_apoio", "gerar_ordem"], "termina_em": "validar",
     "observe": "GRAVIDADE ALTA E LONGE: tempo acima de 8 min, então aciona apoio (inclui a 2ª unidade, se houver) antes de gerar a ordem."},
    {"pergunta": "Tiro disparado no Gama",
     "caminho": ["receber", "extrair", "localizar", "buscar_unidades", "escalar"], "termina_em": "escalar",
     "observe": "NINGUÉM NO RAIO: o MCP devolve lista vazia, o grafo escala ao comando. Não consulta o clima, não gera ordem."},
    {"pergunta": "Barulho excessivo em festa na Asa Sul",
     "caminho": CAMINHO_ATE_TEMPO + ["gerar_ordem"], "termina_em": "validar",
     "observe": "GRAVIDADE BAIXA: mesmo caminho da pergunta 1, sem apoio. A decisão veio do DADO (gravidade), não de outro código."},
    {"pergunta": "Preciso de ajuda urgente",
     "caminho": ["receber", "extrair", "localizar", "pedir_endereco"], "termina_em": "pedir_endereco",
     "observe": "SEM BAIRRO: não localiza, não chama o MCP nem a API. O grafo pede o endereço e encerra."},
]


def rodar_perguntas(app) -> None:
    """Roda as 5 perguntas e mostra o caminho de cada uma, comparado com o esperado (✓ ou ✗)."""
    certas = 0  # quantas perguntas foram pelo caminho esperado
    for i, caso in enumerate(PERGUNTAS_DE_TESTE, start=1):
        estado, caminho = executar(app, caso["pergunta"])
        esperado = caso["caminho"]  # o começo do caminho que o grafo deve percorrer
        caminho_ok = caminho[: len(esperado)] == esperado and caminho[-1] == caso["termina_em"]  # começa como o esperado e termina onde deve
        certas += caminho_ok
        print(f"\n[{i}] {caso['pergunta']}")
        print(f"    observe  : {caso['observe']}")
        print(f"    caminho  : {' -> '.join(caminho)}")
        print(f"    {'✓' if caminho_ok else '✗'} começa por: {' -> '.join(esperado)} ... e termina em {caso['termina_em']}")
        print(f"    ordem    : {estado.get('ordem')}")
    print(f"\n{certas} de {len(PERGUNTAS_DE_TESTE)} perguntas no caminho esperado.")


# as 5 ocorrências que o main.py roda por padrão (as mesmas das PERGUNTAS_DE_TESTE)
CASOS = [caso["pergunta"] for caso in PERGUNTAS_DE_TESTE]

if __name__ == "__main__":
    # o LLM que será entregue ao grafo (e que os nós chamam por modelo.gerar):
    modelo = obter_modelo_real()  # LLM REAL (OpenAI por padrão; Ollama com PROVEDOR=ollama); sem chave, o programa para
    print(f"Modelo em uso: {modelo.nome}\n")
    app = construir_grafo(modelo)  # o grafo compilado, pronto para executar
    if "--perguntas" in sys.argv:
        rodar_perguntas(app)
        raise SystemExit
    for texto in CASOS:
        estado, caminho = executar(app, texto)
        print("=" * 70)
        print("Solicitação:", texto)
        print("Caminho    :", " -> ".join(caminho))
        print("Ordem      :", estado.get("ordem"), "\n")

    # No final: tudo o que aconteceu, nó a nó, e o desenho do grafo com o caminho destacado.
    print("\n\n" + "#" * 70)
    print("VISÃO COMPLETA DE UMA EXECUÇÃO (com LLM real o ciclo de revisão pode ou não aparecer)")
    print("#" * 70)
    estado, caminho = mostrar_execucao(app, CASOS[1])
    salvar_mermaid(app, caminho, nome="grafo_desafio2")

    # E o grafo colorido pelo TIPO de cada nó.
    print("\n\n" + "#" * 70)
    print("OS TIPOS DE NÓ (cada cor é um tipo: LLM, MCP, API, tool, função)")
    print("#" * 70)
    salvar_mermaid_por_tipo(app)
