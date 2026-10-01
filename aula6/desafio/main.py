"""
DESAFIO -- Análise de solicitação de atendimento, como grafo.  (esqueleto em 10 PONTOS DE CONTROLE)

Você NÃO precisa montar o grafo inteiro de uma vez. São 10 pontos de controle: faça um, confira,
siga para o próximo. O grafo vai crescendo, e cada ponto tem um teste.

    PARTE A (pontos 1 a 7): o grafo de decisão e ciclo, com LLM e tools simples.
    PARTE B (pontos 8 a 10): cada nó ganha o seu TIPO: MCP (serviço externo), API (HTTP) e tool (função de cálculo),
                             além do LLM. O grafo não se importa com o tipo: só a ordem e as decisões são dele.

    python desafio\\conferir.py          # mostra quais pontos já passaram (✓) e qual é o próximo

JÁ PRONTO:  Estado, base de conhecimento, as 2 TOOLS, os PROMPTS (funções prompt_*), as funções que
            interpretam o LLM, executar() (devolve o caminho percorrido) e, para a Parte B, chamar_mcp() e
            buscar_feriados() (a tool somar_dias_uteis() é SUA, no ponto 10).
SEU:        os NÓS, os ROTEADORES e a MONTAGEM, dentro de construir_grafo().

Dica: a cada ponto, rode `python desafio\\main.py` e leia a linha "Caminho" de cada caso.

MODELO: `python <pasta>\\main.py` usa LLM REAL (OpenAI por padrão, como nas Aulas 4 e 5; Ollama com
        $env:PROVEDOR = "ollama"). Sem OPENAI_API_KEY ou com o Ollama fora do ar, AVISA e roda com o Mock.
        $env:PROVEDOR = "mock" força o Mock. Os TESTES (conferir.py) usam SEMPRE o Mock: são determinísticos.
"""
import sys                          # sys.path (achar provedor.py) e sys.executable (subir o MCP Server)
import asyncio                      # o cliente MCP é assíncrono; asyncio.run() o executa
import json                         # ler as respostas do MCP e da API (JSON)
import os                           # variáveis de ambiente (FERIADOS_OFFLINE) e os.devnull
import urllib.request               # chamada HTTP à API de feriados (biblioteca padrão)
from datetime import date, timedelta  # datas: DATA_PEDIDO e a conta de dias úteis
from pathlib import Path            # caminhos de arquivos (servidor MCP, pasta saida/)
from typing import TypedDict        # o tipo do Estado (um dicionário com campos conhecidos)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite importar provedor.py (escolhe o LLM)
sys.path.insert(0, str(Path(__file__).resolve().parent))      # permite importar modelo_mock.py (o LLM de mentira dos testes)

from langgraph.graph import END, START, StateGraph  # noqa: F401  StateGraph monta o grafo; START e END são a entrada e a saída

from mcp import ClientSession, StdioServerParameters  # cliente MCP: a conversa e os parâmetros para subir o servidor
from mcp.client.stdio import stdio_client             # fala com o servidor MCP por stdin/stdout

from modelo_mock import ModeloMock        # LLM de mentira (determinístico): usado pelos testes e como reserva
from provedor import obter_modelo         # escolhe o LLM real (OpenAI ou Ollama) pelo .env

MAX_TENTATIVAS = 3  # limite de vezes que o ciclo analisar -> validar -> revisar pode repetir (a CONDIÇÃO DE PARADA)

# PARTE B: constantes das integrações (MCP, API e tool)
# caminho do MCP Server da base de conhecimento (mcp_base.py), que chamar_mcp() sobe quando precisa
SERVER_MCP = str(Path(__file__).resolve().parent / "mcp_base.py")
# a "data de hoje" do cenário: calcular_prazo conta os dias úteis a partir dela (fixa, para os resultados serem reproduzíveis)
DATA_PEDIDO = date(2026, 9, 29)
# feriados nacionais de 2026 ("AAAA-MM-DD"): o PLANO B de buscar_feriados quando a API falha ou está offline
FERIADOS_2026 = [
    "2026-01-01", "2026-02-17", "2026-04-03", "2026-04-21", "2026-05-01", "2026-06-04",
    "2026-09-07", "2026-10-12", "2026-11-02", "2026-11-15", "2026-11-20", "2026-12-25",
]


class Estado(TypedDict):
    """O ESTADO do grafo: o que circula entre os nós. Cada nó lê daqui e devolve SÓ o que mudou."""
    solicitacao: str      # o texto que o usuário enviou (a entrada do grafo)
    urgencia: str         # escrito por classificar_urgencia: "urgente" (vai ao plantão) ou "normal" (pesquisa na base)
    informacao: str       # escrito por pesquisar: o texto da base; "" = o assunto não está na base (caminho sem_base)
    encaminhamento: str   # escrito por encaminhar: a confirmação de envio ao plantão (só no caminho urgente)
    analise: str          # escrito por analisar (LLM): os passos numerados para atender a solicitação
    valida: bool          # escrito por validar (LLM): True se a análise está boa; decide se o ciclo continua
    tentativas: int       # escrito por analisar: quantas análises já foram feitas; o roteador compara com MAX_TENTATIVAS
    feedback: str         # o motivo da reprovação: validar escreve, revisar reforça e analisar lê para corrigir
    resposta: str         # escrito por responder (LLM): a resposta final ao usuário
    # --- PARTE B (use a partir do ponto 8): os dados que o MCP, a API e a tool acrescentam ---
    prazo_dias: int       # pesquisar (MCP): prazo de entrega, em dias úteis (0 = sem prazo)
    feriados: list        # consultar_feriados (API): feriados do ano, "AAAA-MM-DD"
    prazo_final: str      # calcular_prazo (tool): data de entrega, "AAAA-MM-DD" ("" = sem prazo)


# ---------------------------------------------------------------- ferramentas
# A base de conhecimento LOCAL (assunto -> procedimento), usada na Parte A. Na Parte B a MESMA base passa a ser servida pelo
# MCP Server (base_conhecimento.csv, que acrescenta o prazo em dias úteis). Os textos são proposital e necessariamente os
# mesmos nos dois lugares: se mudar um, mude o outro (o teste test_base_igual_ao_csv avisa se divergirem).
BASE_CONHECIMENTO = {
    "segunda via": "Agendar atendimento; levar documento com foto; pagar a taxa de emissão.",
    "passaporte": "Preencher o formulário online; agendar a Polícia Federal; pagar a GRU.",
    "horário": "Atendimento de segunda a sexta, das 8h às 17h.",
}


def buscar_procedimentos(solicitacao: str) -> str:
    """TOOL comum (nenhuma IA aqui): procura na BASE_CONHECIMENTO o assunto citado na solicitação e devolve o procedimento.
    Devolve '' quando o assunto NÃO está na base (é isso que faz o grafo seguir pelo caminho sem_base)."""
    for assunto, texto in BASE_CONHECIMENTO.items():  # assunto: a palavra-chave; texto: o procedimento
        if assunto in solicitacao.lower():  # minúsculas, para não depender de maiúsculas
            return texto
    return ""


def encaminhar_plantao(solicitacao: str) -> str:
    """TOOL comum: simula o envio de um caso urgente ao plantão e devolve a confirmação (vai para estado["encaminhamento"])."""
    return "Caso encaminhado ao plantão 24h (prioridade máxima)."



# ------------------------------------ PARTE B: integrações e tools (os TIPOS de nó além do LLM)
def chamar_mcp(ferramenta: str, argumentos: dict) -> list:
    """(PRONTA) Chama uma tool do MCP Server (mcp_base.py) por stdio e devolve a lista de resultados (dicts)."""
    async def _chamar():  # o cliente MCP é assíncrono: a conversa inteira acontece aqui dentro
        params = StdioServerParameters(command=sys.executable, args=[SERVER_MCP])  # como subir o servidor: "python mcp_base.py"
        with open(os.devnull, "w") as silencio:  # descarta as mensagens de log do servidor
            async with stdio_client(params, errlog=silencio) as (leitura, escrita):  # sobe o servidor e abre o canal
                async with ClientSession(leitura, escrita) as sessao:  # a conversa MCP
                    await sessao.initialize()  # "aperto de mão" do protocolo
                    resposta = await sessao.call_tool(ferramenta, argumentos)  # chama a tool pelo NOME, com os parâmetros
                    if resposta.is_error:
                        raise RuntimeError(f"MCP {ferramenta}: {resposta.content}")
                    return [json.loads(item.text) for item in resposta.content]  # cada resultado chega como texto JSON

    return asyncio.run(_chamar())  # roda a conversa e devolve a lista de resultados


def buscar_feriados(ano: int) -> list[str]:
    """(PRONTA) API HTTP (BrasilAPI, sem chave): feriados nacionais do ano, como textos "AAAA-MM-DD".
    Se a API falhar (ou FERIADOS_OFFLINE=1) devolve a lista local e o grafo SEGUE: falha de API não derruba o grafo."""
    if os.getenv("FERIADOS_OFFLINE") != "1":  # FERIADOS_OFFLINE=1 pula a internet (testes e aula sem rede)
        try:
            pedido = urllib.request.Request(f"https://brasilapi.com.br/api/feriados/v1/{ano}",
                                            headers={"User-Agent": "curso-pcdf/1.0"})  # a BrasilAPI recusa (403) sem User-Agent
            with urllib.request.urlopen(pedido, timeout=5) as r:  # timeout: não deixa o grafo esperando a API para sempre
                return [f["date"] for f in json.load(r)]  # a API devolve [{date, name, type}]; guardamos só a data
        except (OSError, ValueError, KeyError) as erro:
            print(f"[aviso] API de feriados indisponível ({type(erro).__name__}): usando a lista local", file=sys.stderr)
    return list(FERIADOS_2026) if ano == 2026 else []  # plano B: a lista local (só existe para 2026)


def somar_dias_uteis(inicio: date, dias: int, feriados: list[str]) -> date:
    """TOOL local (PONTO 10): a data em que `dias` dias ÚTEIS contados a partir de `inicio` se completam.
    Dia útil = segunda a sexta que NÃO é feriado. `inicio` não conta; o 1º dia contado é o seguinte.

        somar_dias_uteis(date(2026, 9, 29), 5, FERIADOS_2026)   -> 2026-10-06
        somar_dias_uteis(date(2026, 9, 29), 10, FERIADOS_2026)  -> 2026-10-14   (pula o feriado de 12/10)
        somar_dias_uteis(date(2026, 10, 2), 1, [])              -> 2026-10-05   (pula o fim de semana)
        somar_dias_uteis(date(2026, 9, 29), 0, [])              -> 2026-09-29
    """
    # TODO (PONTO 10): escreva a tool. Ande um dia de cada vez a partir de `inicio` e conte só os dias úteis
    #                  (segunda a sexta, que NÃO estejam em `feriados`; feriados são textos "AAAA-MM-DD").
    #                  Dicas: date.weekday() é 0 (segunda) .. 6 (domingo); timedelta(days=1); data.isoformat().
    raise NotImplementedError("PONTO 10: escreva somar_dias_uteis()")


# ------------------------------------------------ prompts (prontos: use nos seus nós)
# Cada um devolve o TEXTO do prompt a partir do estado. Você os passa a modelo.gerar(...).
# (A 1ª linha "TAREFA: <nome>" é o que o Mock lê.)
def prompt_classificar(estado: Estado) -> str:
    """O prompt do nó classificar_urgencia: pede UMA palavra (urgente ou normal) para o roteador poder decidir."""
    return (
        "TAREFA: classificar_urgencia\n"
        "Classifique a solicitação como 'urgente' ou 'normal'.\n"
        "- urgente: risco à saúde ou à segurança, ou pedido de atendimento imediato.\n"
        "- normal: dúvida ou procedimento sem prazo crítico.\n"
        "Responda com UMA palavra: urgente ou normal.\n"
        f"Solicitação: {estado['solicitacao']}"
    )


def prompt_analisar(estado: Estado) -> str:
    """O prompt do nó analisar: usa SOMENTE a informação pesquisada (e o prazo, na Parte B) para evitar invenção."""
    # na revisão, o motivo da reprovação volta ao prompt para o LLM corrigir
    correcao = f"Correção solicitada: {estado['feedback']}\n" if estado["feedback"] else ""
    return (
        "TAREFA: analisar\n"
        "Analise a solicitação usando SOMENTE as informações pesquisadas e indique "
        "os passos numerados (1., 2., 3.) para atendê-la.\n"
        f"{correcao}"
        f"Solicitação: {estado['solicitacao']}\n"
        f"Informações: {estado['informacao']}"
        + (f"\nPrazo estimado de entrega: {estado['prazo_final']}" if estado.get("prazo_final") else "")  # Parte B: o prazo da tool entra no prompt
    )


def prompt_validar(estado: Estado) -> str:
    """O prompt do nó validar: o LLM só confere a FORMA da análise (passos numerados) e responde OK ou ERRO."""
    return (
        "TAREFA: validar\n"
        "A análise é válida se trouxer pelo menos três passos numerados e concretos. "
        "Responda apenas 'OK' ou 'ERRO: <motivo>'.\n"
        f"Análise: {estado['analise']}"
    )


def prompt_responder(estado: Estado) -> str:
    """Monta o contexto pelo que EXISTE no estado (quem decidiu o caminho foi o grafo, não o prompt)."""
    if estado["encaminhamento"]:  # caminho urgente: só informar o encaminhamento
        contexto = f"Encaminhamento: {estado['encaminhamento']}\n"
    elif not estado["informacao"]:  # sem base: admitir que não sabe (não inventar)
        contexto = "SEM_BASE: o assunto não consta na base; NÃO invente uma resposta.\n"
    else:  # com base: responder a partir da análise (e do prazo, se houver)
        contexto = f"Análise: {estado['analise']}\n"
        if estado.get("prazo_final"):
            contexto += f"Prazo estimado de entrega: {estado['prazo_final']} (dias úteis, já descontados os feriados)\n"
        if not estado["valida"]:  # o ciclo parou no limite sem validar: avisar o usuário
            contexto += "(análise não validada; avise o usuário)\n"
    return (
        "TAREFA: responder\n"
        "Escreva uma resposta curta e cordial ao usuário.\n"
        f"Solicitação: {estado['solicitacao']}\n"
        f"{contexto}"
    )


# ------------------------- interpretar a resposta do LLM (texto livre -> valor que o grafo entende)
def normalizar_urgencia(texto: str) -> str:
    """O LLM devolve texto livre; o roteador precisa de um rótulo exato.
    'Urgente.' / 'URGENTE' / 'é urgente' -> 'urgente'; qualquer outra coisa -> 'normal'."""
    return "urgente" if "urgente" in texto.lower() else "normal"


def analise_aprovada(texto: str) -> bool:
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
        1) escreva a função do ponto N  (Fase A)
        2) ligue o ponto N              (Fase B)
        3) rode  python desafio\\conferir.py   e só siga quando o ponto N estiver ✓

    ATENÇÕES:
      - As funções vão DENTRO de construir_grafo (mesma indentação dos placeholders): é ali que
        `modelo` existe. Fora dela dá NameError: name 'modelo' is not defined.
      - Para testar um ponto isolado, termine o grafo com `construtor.add_edge("<último nó>", END)`.
        Quando o ponto seguinte pedir, APAGUE essa linha (senão o nó termina o grafo e segue adiante ao mesmo tempo).
    ---------------------------------------------------------------------------------------------
    """

    # ==============================================================================================
    # FASE A -- AS FUNÇÕES
    # ==============================================================================================

    """
    FUNÇÃO PONTO 1 -- receber.
        receber devolve TODOS os 9 campos do Estado com valores iniciais
        {"solicitacao": estado["solicitacao"].strip(), "urgencia": "", "informacao": "",
                "encaminhamento": "", "analise": "", "valida": False, "tentativas": 0,
                "feedback": "", "resposta": ""}
    """
    #colocar a função 1 aqui
    # def receber(estado):

    """
    FUNÇÃO PONTO 2 -- classificar_urgencia. nó LLM: texto = modelo.gerar(prompt_classificar(estado)); devolva {"urgencia": normalizar_urgencia(texto)}
    """
    #colocar a função 2 aqui
    # def classificar_urgencia(estado):

    """
    FUNÇÃO PONTO 3 -- caminho URGENTE: encaminhar (tool), responder (LLM) e o roteador.
        encaminhar: tool -> {"encaminhamento": encaminhar_plantao(...)}
        responder:  nó LLM -> {"resposta": modelo.gerar(prompt_responder(estado))}
        rotear_apos_classificar(estado) -> "urgente" | "normal"   (só LÊ o estado)
    """
    #colocar a função 3 aqui
    # def encaminhar(estado):

    # def responder(estado):

    # def rotear_apos_classificar(estado):

    """
    FUNÇÃO PONTO 4 -- caminho SEM BASE: pesquisar (tool) e o roteador.
        pesquisar: tool -> {"informacao": buscar_procedimentos(...)}   ("" = não sabe)
        rotear_apos_pesquisar(estado) -> "com_base" | "sem_base"
    """
    #colocar a função 4 aqui
    # def pesquisar(estado):

    # def rotear_apos_pesquisar(estado):

    """
    FUNÇÃO PONTO 5 -- análise e validação: analisar e validar (nós LLM).
        analisar: LLM -> {"analise": ..., "tentativas": estado["tentativas"] + 1}  (prompt_analisar)
        validar:  LLM -> {"valida": analise_aprovada(texto), "feedback": "" se ok senão o texto}  (prompt_validar)
    """
    #colocar a função 5 aqui
    # def analisar(estado):

    #def validar(estado):

    """
    FUNÇÃO PONTO 6 -- o CICLO: revisar (nó) e o roteador de validar.
        revisar: devolve {"feedback": f"corrija — {estado['feedback']}"}
        rotear_apos_validar(estado) -> "ok" se estado["valida"], senão "erro"
    """
    #colocar a função 6 aqui
    # def revisar(estado):

    # def rotear_apos_validar(estado):

    """
    FUNÇÃO PONTO 7 -- a PARADA: não há função nova. EDITE rotear_apos_validar (a do ponto 6):
        se NÃO é válida e estado["tentativas"] >= MAX_TENTATIVAS -> devolva "desistir"
        ("desistir" é um RÓTULO do roteador, não uma função nem um nó)
        a condição de parada é lida do ESTADO, não de uma variável local
    """
    #no ponto 7 você só acrescenta duas linhas em rotear_apos_validar

    # ----------------------------------------------------------------------------------------------
    # PARTE B -- OS TIPOS DE NÓ (faça só depois que a Parte A passou nos 7 pontos)
    # Até aqui `pesquisar` era uma tool local. Agora o grafo ganha nós de tipos diferentes:
    #   LLM (você já tem), tool (função de cálculo), MCP (serviço externo) e API (HTTP).
    # ----------------------------------------------------------------------------------------------

    """
    FUNÇÃO PONTO 8 -- pesquisar vira um nó MCP (a base de conhecimento agora é um SERVIÇO: mcp_base.py).
        troque o corpo de `pesquisar` (ponto 4): em vez de buscar_procedimentos(...), chame o MCP Server:
            achados = chamar_mcp("consultar_base", {"solicitacao": estado["solicitacao"]})   # lista; vazia = não sabe
            achou   -> {"informacao": achados[0]["texto"], "prazo_dias": achados[0]["prazo_dias_uteis"]}
            não achou -> {"informacao": "", "prazo_dias": 0}
        e acrescente em `receber` os 3 campos novos: "prazo_dias": 0, "feriados": [], "prazo_final": ""
        (o grafo NÃO muda: o roteador continua olhando estado["informacao"])
    """
    #no ponto 8 você EDITA pesquisar e receber (não há função nova)

    """
    FUNÇÃO PONTO 9 -- consultar_feriados é um nó de API (HTTP, BrasilAPI).
        consultar_feriados: {"feriados": buscar_feriados(DATA_PEDIDO.year)}     (buscar_feriados já vem pronta e já
        trata a falha da API: o grafo segue)
    """
    #colocar a função 9 aqui
    # def consultar_feriados(estado):

    """
    FUNÇÃO PONTO 10 -- calcular_prazo é um nó de TOOL (cálculo local, sem IA).
        1) escreva a tool somar_dias_uteis() (no topo do arquivo, na seção PARTE B);
        2) calcular_prazo: se estado["prazo_dias"] for 0 devolva {"prazo_final": ""}; senão
           {"prazo_final": somar_dias_uteis(DATA_PEDIDO, estado["prazo_dias"], estado["feriados"]).isoformat()}
    """
    #colocar a função 10 aqui
    # def calcular_prazo(estado):

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
    PONTO 2 -- classificar_urgencia.  Grafo: START -> receber -> classificar_urgencia -> END
        dica: add_node("classificar_urgencia", ...)  e  add_edge("receber", "classificar_urgencia")
    """
    # construtor.add_node("classificar_urgencia", classificar_urgencia)
    # construtor.add_edge("receber", "classificar_urgencia")

    # teste isolado do ponto 2: construtor.add_edge("classificar_urgencia", END)   (apague no ponto 3)

    """
    PONTO 3 -- caminho URGENTE.  classificar_urgencia -> (urgente) encaminhar -> responder -> END
        dica: add_node de encaminhar e de responder;
              add_conditional_edges("classificar_urgencia", rotear_apos_classificar, {"urgente": "encaminhar", "normal": END})
              add_edge("encaminhar", "responder")  e  add_edge("responder", END)
        (até o ponto 4 existir, "normal" vai para END)
    """
    # construtor.add_node("encaminhar", encaminhar)
    # construtor.add_node("responder", responder)
    # construtor.add_conditional_edges(...)
    # construtor.add_edge("encaminhar", "responder")
    # construtor.add_edge("responder", END)

    # teste isolado do ponto 3: rode o conferir (o caminho urgente já fecha com END)

    """
    PONTO 4 -- caminho SEM BASE.  (normal) -> pesquisar -> (sem_base) responder
        dica: add_node("pesquisar", pesquisar)
              no ponto 3, troque "normal": END por "normal": "pesquisar"
              add_conditional_edges("pesquisar", rotear_apos_pesquisar, {"com_base": "responder", "sem_base": "responder"})
        (por ora "com_base" também vai para responder; o ponto 5 o troca por analisar)
    """
    # construtor.add_node("pesquisar", pesquisar)
    # construtor.add_conditional_edges(...)

    # teste isolado do ponto 4: rode o conferir (os dois rótulos já fecham em responder)

    """
    PONTO 5 -- análise e validação.  (com_base) -> analisar -> validar -> responder
        dica: add_node de analisar e de validar;
              no ponto 4, troque "com_base": "responder" por "com_base": "analisar"
              add_edge("analisar", "validar")
    """
    # construtor.add_node("analisar", analisar)
    # construtor.add_node("validar", validar)
    # construtor.add_edge("analisar", "validar")

    # teste isolado do ponto 5: construtor.add_edge("validar", "responder")   (apague no ponto 6)

    """
    PONTO 6 -- o CICLO.  validar -> (erro) revisar -> analisar
        dica: add_node("revisar", revisar)
              add_conditional_edges("validar", rotear_apos_validar, {"ok": "responder", "desistir": "responder", "erro": "revisar"})
              add_edge("revisar", "analisar")   <- o ciclo é UMA ARESTA do grafo (nada de while dentro de um nó!)
        o rótulo "desistir" já está no mapa, mas o roteador só o devolve no ponto 7
    """
    # construtor.add_node("revisar", revisar)
    # construtor.add_conditional_edges(...)
    # construtor.add_edge("revisar", "analisar")

    # teste do ponto 6: rode o conferir (sem a parada o ponto 7 ainda aparece como ✗)

    """
    PONTO 7 -- a PARADA.  não há ligação nova: o mapa do ponto 6 já leva "desistir" a responder.
        o que muda é o roteador (Fase A, ponto 7). Confira: o ciclo para em MAX_TENTATIVAS.
    """
    # ----------------------------------------------------------------------------------------------
    # PARTE B -- LIGAR OS NÓS NOVOS
    # ----------------------------------------------------------------------------------------------

    """
    PONTO 8 -- (MCP) nenhuma ligação nova: `pesquisar` está no mesmo lugar, só mudou o que ele faz por dentro.
        confira: o conferir diz se o MCP foi chamado e se o prazo chegou ao estado.
    """

    """
    PONTO 9 -- (API) normal/com_base -> pesquisar -> consultar_feriados -> analisar
        dica: add_node("consultar_feriados", consultar_feriados)
              no mapa de pesquisar, troque  "com_base": "analisar"  por  "com_base": "consultar_feriados"
              add_edge("consultar_feriados", "analisar")
        (só o caminho COM base passa pela API; o "sem_base" continua indo direto para responder)
    """
    # construtor.add_node("consultar_feriados", consultar_feriados)
    # construtor.add_edge("consultar_feriados", "analisar")

    """
    PONTO 10 -- (tool) pesquisar -> consultar_feriados -> calcular_prazo -> analisar
        dica: add_node("calcular_prazo", calcular_prazo)
              APAGUE o add_edge("consultar_feriados", "analisar") e ligue consultar_feriados -> calcular_prazo -> analisar
        no fim, rode `python desafio\\main.py`: ele mostra o grafo colorido pelos TIPOS de nó.
    """
    # construtor.add_node("calcular_prazo", calcular_prazo)
    # construtor.add_edge("consultar_feriados", "calcular_prazo")
    # construtor.add_edge("calcular_prazo", "analisar")

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
    """Roda o grafo e mostra, NÓ A NÓ, tudo o que aconteceu até a resposta ficar pronta.

    Para cada nó: o que ele escreveu no estado. No fim: o caminho, os fatos que decidiram o rumo
    (urgência, base, validação, tentativas) e como a resposta foi montada. Devolve (estado, caminho).
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
    print(f"      urgência   : {estado.get('urgencia')}")
    print(f"      base       : {'achou informação' if estado.get('informacao') else 'sem informação na base'}")
    print(f"      tentativas : {estado.get('tentativas')}  |  análise válida: {estado.get('valida')}")
    if estado.get("encaminhamento"):
        origem = "encaminhamento ao plantão (caminho urgente)"
    elif not estado.get("informacao"):
        origem = "SEM_BASE: o grafo impediu o LLM de inventar (a análise nem rodou)"
    elif estado.get("valida"):
        origem = f"análise validada após {estado.get('tentativas')} tentativa(s)"
    else:
        origem = "análise NÃO validada (parou em MAX_TENTATIVAS); a resposta avisa o usuário"
    print(f"COMO A RESPOSTA FOI MONTADA: a partir de {origem}")
    print(f"RESPOSTA: {estado.get('resposta')}")
    return estado, caminho


def mermaid_do_grafo(app, caminho=None) -> str:
    """Devolve o Mermaid do grafo. Se `caminho` for dado, os nós que executaram saem destacados."""
    texto = app.get_graph().draw_mermaid()  # o desenho do grafo em texto Mermaid
    if caminho:
        nos = ",".join(dict.fromkeys(caminho))  # sem repetir, na ordem em que rodaram
        texto += f"\tclassDef executado fill:#ffd166,stroke:#b8860b,stroke-width:2px,color:#000;\n\tclass {nos} executado;\n"
    return texto


def salvar_mermaid(app, caminho=None, nome: str = "grafo") -> None:
    """Imprime o Mermaid e salva saida/<nome>.mmd (cole em https://mermaid.live) e saida/<nome>.md (preview do VS Code)."""
    mermaid = mermaid_do_grafo(app, caminho)  # o texto Mermaid (com o caminho destacado, se houver)
    pasta = Path(__file__).resolve().parent / "saida"  # a pasta desafio/saida (criada logo abaixo)
    pasta.mkdir(exist_ok=True)
    (pasta / f"{nome}.mmd").write_text(mermaid, encoding="utf-8")
    (pasta / f"{nome}.md").write_text(f"# {nome}\n\n```mermaid\n{mermaid}\n```\n", encoding="utf-8")
    print("\nMERMAID (nós em amarelo = executaram):")
    print(mermaid)
    print(f"Salvo em desafio/saida/{nome}.mmd e desafio/saida/{nome}.md")


# ------------------------------------------------ os TIPOS de nó (PRONTO: não precisa mexer)
# Na Parte B cada nó do grafo tem um tipo. Para o grafo, tudo é "função que lê o estado e devolve uma atualização".
# TIPOS_DE_NO: nome do nó -> tipo (usado só para colorir o desenho).
TIPOS_DE_NO = {
    "receber": "função", "classificar_urgencia": "LLM", "encaminhar": "tool", "pesquisar": "MCP",
    "consultar_feriados": "API", "calcular_prazo": "tool", "analisar": "LLM", "validar": "LLM",
    "revisar": "função", "responder": "LLM",
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


def salvar_mermaid_por_tipo(app, nome: str = "grafo_por_tipo") -> None:
    """Imprime o Mermaid colorido por tipo e salva em saida/<nome>.mmd e .md (como salvar_mermaid)."""
    mermaid = mermaid_por_tipo(app)
    pasta = Path(__file__).resolve().parent / "saida"  # a pasta desafio/saida (criada logo abaixo)
    pasta.mkdir(exist_ok=True)
    (pasta / f"{nome}.mmd").write_text(mermaid, encoding="utf-8")
    (pasta / f"{nome}.md").write_text(f"# {nome}\n\n```mermaid\n{mermaid}\n```\n", encoding="utf-8")
    print("\nOS TIPOS DE NÓ: LLM (azul) | MCP (laranja) | API (verde) | tool (roxo) | função (cinza)")
    print(mermaid)
    print(f"Salvo em desafio/saida/{nome}.mmd e desafio/saida/{nome}.md")


# ------------------------------- 5 PERGUNTAS que testam o grafo por CAMINHOS diferentes (PRONTO: não precisa mexer)
# Rode:  python desafio\\main.py --perguntas      (confere o caminho de cada uma; vale para o grafo COMPLETO, Partes A e B)
# o INÍCIO do caminho de quem tem base de conhecimento (as perguntas 2, 3 e 4 compartilham esse começo)
CAMINHO_COM_BASE = ["receber", "classificar_urgencia", "pesquisar", "consultar_feriados", "calcular_prazo", "analisar"]
# cada item: a pergunta, o começo do caminho esperado, o prazo_final esperado e o que observar
PERGUNTAS_DE_TESTE = [
    {"pergunta": "Estou sem medicação e passando mal, preciso de atendimento agora",
     "caminho": ["receber", "classificar_urgencia", "encaminhar", "responder"], "prazo_final": "",
     "observe": "URGENTE: não pesquisa, não chama a API, não analisa. Vai direto ao plantão."},
    {"pergunta": "Preciso saber como solicitar uma segunda via de um documento",
     "caminho": CAMINHO_COM_BASE, "prazo_final": "2026-10-06",
     "observe": "COM BASE: MCP (prazo 5 dias úteis) -> API (feriados) -> tool (data) -> LLM analisa e valida."},
    {"pergunta": "Preciso renovar o passaporte",
     "caminho": CAMINHO_COM_BASE, "prazo_final": "2026-10-14",
     "observe": "O MESMO caminho, outro DADO: 10 dias úteis atravessam o feriado de 12/10, e a tool o pula."},
    {"pergunta": "Qual o horário de atendimento?",
     "caminho": CAMINHO_COM_BASE, "prazo_final": "",
     "observe": "COM BASE, SEM PRAZO (0 dias): calcular_prazo roda, mas devolve prazo_final vazio."},
    {"pergunta": "Qual o prazo de restituição do imposto de renda de 2031?",
     "caminho": ["receber", "classificar_urgencia", "pesquisar", "responder"], "prazo_final": "",
     "observe": "SEM BASE: o grafo admite que não sabe. Não chama a API, não analisa, não inventa."},
]


def rodar_perguntas(app) -> None:
    """Roda as 5 perguntas e mostra o caminho de cada uma, comparado com o esperado (✓ ou ✗)."""
    certas = 0  # quantas perguntas foram pelo caminho esperado e com o prazo esperado
    for i, caso in enumerate(PERGUNTAS_DE_TESTE, start=1):
        estado, caminho = executar(app, caso["pergunta"])
        esperado = caso["caminho"]  # o começo do caminho que o grafo deve percorrer
        caminho_ok = caminho[: len(esperado)] == esperado and caminho[-1] == "responder"  # começa como o esperado e termina em responder
        prazo_ok = estado.get("prazo_final", "") == caso["prazo_final"]  # a tool calculou a data certa (ou deixou vazio)
        certas += caminho_ok and prazo_ok
        print(f"\n[{i}] {caso['pergunta']}")
        print(f"    observe  : {caso['observe']}")
        print(f"    caminho  : {' -> '.join(caminho)}")
        print(f"    {'✓' if caminho_ok else '✗'} começa por: {' -> '.join(esperado)} ... e termina em responder")
        print(f"    {'✓' if prazo_ok else '✗'} prazo_final esperado {caso['prazo_final']!r}, obtido {estado.get('prazo_final', '')!r}")
    print(f"\n{certas} de {len(PERGUNTAS_DE_TESTE)} perguntas no caminho esperado.")


# as 3 solicitações que o main.py roda por padrão (urgente, com base e sem base)
CASOS = [
    "Estou sem medicação e passando mal, preciso de atendimento agora",
    "Preciso saber como solicitar uma segunda via de um documento",
    "Qual o prazo de restituição do imposto de renda de 2031?",
]

if __name__ == "__main__":
    # o LLM que será entregue ao grafo (e que os nós chamam por modelo.gerar):
    modelo = obter_modelo(ModeloMock(), padrao="openai")  # LLM REAL por padrão (OpenAI; Ollama com PROVEDOR=ollama); sem chave, cai no Mock com aviso
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
        print("Urgência   :", estado.get("urgencia"), "| tentativas:", estado.get("tentativas"),
              "| validada:", estado.get("valida"))
        print("Resposta   :", estado.get("resposta"), "\n")

    # No final: tudo o que aconteceu, nó a nó, e o desenho do grafo com o caminho destacado.
    print("\n\n" + "#" * 70)
    print("VISÃO COMPLETA DE UMA EXECUÇÃO (com o Mock este é o caso do ciclo de revisão; com LLM real o ciclo pode não aparecer)")
    print("#" * 70)
    estado, caminho = mostrar_execucao(app, CASOS[1])
    salvar_mermaid(app, caminho, nome="grafo_desafio1")

    # E o grafo colorido pelo TIPO de cada nó (Parte B).
    print("\n\n" + "#" * 70)
    print("OS TIPOS DE NÓ (cada cor é um tipo: LLM, MCP, API, tool, função)")
    print("#" * 70)
    salvar_mermaid_por_tipo(app)