# Aula 6 — Modelagem de Sistemas Baseados em Grafos

Aula remota, síncrona, 5 horas, cerca de 70% prática. Linguagem: Python.
Framework: **LangGraph**. Modelo de demonstração: **Claude**, com **LLM Mock**
para rodar tudo sem API Key.

Cenário único: **sistema de análise e tratamento de solicitações**. Um usuário
envia, por exemplo:

> "Preciso saber quais são os procedimentos para solicitar uma segunda via de um documento."

O sistema precisa receber, classificar, analisar, eventualmente pesquisar,
validar, revisar (se houver erro) e responder. Todos os exemplos são
**evoluções do mesmo processo**; em cada um, o material diz *"no exemplo
anterior fizemos X; agora adicionamos Y"*.

> **Ideia central:** um agente complexo pode ser entendido como um sistema de
> estados que percorre um grafo de execução.

## Mapa da aula

| Bloco | Tema | Duração | Exemplos |
|---|---|---|---|
| 1 | Por que grafos? | 40 min | 01, 02 |
| 2 | Teoria aplicada (nós, arestas, DAG, ciclo) | 45 min | 02 (revisitado) |
| 3 | Estado compartilhado | 45 min | 03 |
| 4 | Primeiro LangGraph | 60 min | 04, 05 |
| 5 | Decisões e ciclos | 60 min | 06, 07, 08 |
| 6 | LLM e agente | 50 min | 09, 10 |
| 7 | Desafio | 40 min | desafio |

## Onde estamos no curso

```
AULAS ANTERIORES          A2A                      MCP

  AGENTE                AGENTE A                 AGENTE
    ↓                      ↓                        ↓
   LLM                  AGENTE B                   MCP
    ↓                      ↓                        ↓
  TOOL                 RESULTADO                  TOOL
    ↓                                                ↓
RESULTADO                                  SISTEMA / BANCO / API
```

Até aqui cada aula respondeu a uma pergunta: *como o agente pensa* (LLM), *o que
ele consegue fazer* (Tools), *com quem conversa* (A2A) e *como acessa sistemas*
(MCP). Falta uma: **em que ordem, com quais decisões e com quais repetições isso
tudo acontece?**

```
LANGGRAPH

              ┌──────────────┐
              │     LLM      │
              └──────┬───────┘
                     ↓
        ┌────────────┴────────────┐
        ↓                         ↓
      TOOL                       MCP
        ↓                         ↓
    SISTEMA                    SISTEMA
        └────────────┬────────────┘
                     ↓
                  ESTADO
                     ↓
                PRÓXIMO NÓ
```

**LangGraph não substitui LLM, Tools ou MCP.** Ele fornece uma forma explícita
de modelar o **fluxo de execução** ao redor deles. O grafo representa o
**controle de execução**.

---

# BLOCO 1 — Por que grafos? (Exemplos 01 e 02)

## Exemplo 01 — o fluxo linear

`exemplos/01_fluxo_linear/main.py` implementa o processo como quatro funções
chamadas em sequência:

```
receber → classificar → analisar → responder
```

Rode e observe: funciona. O problema aparece quando fazemos três perguntas.

| Pergunta | O que acontece no código linear |
|---|---|
| E se a solicitação for simples e não precisar de análise? | `analisar` roda mesmo assim; para evitar, precisamos de um `if` |
| E se a análise estiver errada e for preciso voltar? | Precisamos de um `while` espalhado pelo script |
| Onde está o estado? | Em variáveis soltas (`categoria` foi calculada e **nunca usada**) |

Cada `if` e cada `while` adicionado esconde o fluxo dentro da lógica. Com
dez etapas e cinco decisões, ninguém mais consegue *ver* o processo lendo o
código. **O fluxo de execução existe, mas não é explícito.**

Conclusão do bloco: precisamos **representar o processo como dado**, algo que
possamos desenhar, ler e alterar sem reescrever a lógica inteira.

## O que é um grafo?

Um **grafo** é uma estrutura formada por **nós** (também chamados vértices) e
**arestas** (as ligações entre eles). Grafos modelam qualquer coisa em que
"coisas" se relacionam: cidades e estradas, pessoas e amizades, páginas e links.

## O que é um nó?

Uma **etapa do processo**. Na nossa história: `receber`, `classificar`,
`analisar`, `responder`. Em LangGraph, um nó é uma **função Python**.

## O que é uma aresta?

Um **caminho entre duas etapas**: "depois de A, vem B". É a aresta que diz por
onde a execução pode seguir.

## O que é um grafo de execução?

É um grafo em que **nós são etapas de um programa** e **arestas são a ordem
(possível) de execução**. O grafo não guarda dados nem faz o trabalho: ele
representa o **controle de fluxo**.

## Exemplo 02 — o mesmo processo, agora como grafo

*No exemplo anterior o fluxo estava escondido na ordem das chamadas. Agora
o escrevemos como dado.*

```python
grafo = {
    "receber": ["classificar"],
    "classificar": ["analisar"],
    "analisar": ["responder"],
    "responder": [],
}
```

```
NÓ     = etapa do processo
ARESTA = caminho entre etapas

receber → classificar → analisar → responder
```

Mesma coisa que o exemplo 01, mas agora o processo é uma **estrutura
inspecionável**. E o mesmo formato aceita decisão: basta um nó com duas
arestas de saída.

```python
"classificar": ["responder", "pesquisar"]   # ponto de decisão
```

E aceita **caminho de volta** (`"revisar": ["analisar"]`), o que forma um ciclo.
O exemplo 02 inclui uma função que detecta isso. Rode-o e leia as três
saídas: linear e com decisão não têm ciclo; o terceiro grafo tem.

**Transição:** já sabemos *desenhar* um processo. Falta dar a ele algo para
carregar de etapa em etapa: o **estado**.

---

# BLOCO 2 — Teoria aplicada

## O que é um grafo direcionado?

Um grafo em que cada aresta tem **sentido**: `A → B` não significa `B → A`.
Em execução isso é natural: `classificar` acontece *antes* de `analisar`, não
o contrário. Todo grafo de execução é direcionado.

## Vocabulário

| Termo | Significado | Na nossa história |
|---|---|---|
| **Nó** | etapa | `analisar` |
| **Aresta** | ligação entre etapas | `analisar → validar` |
| **Direção** | sentido da aresta | `validar` vem depois de `analisar` |
| **Branch** (ramificação) | nó com mais de uma saída; alguém decide | `classificar` → `simples` ou `complexa` |
| **Merge** (convergência) | nó com mais de uma entrada | `responder` recebe de `classificar` e de `analisar` |
| **DAG** | grafo direcionado **sem ciclos** | fluxo com branch e merge, sem volta |
| **Ciclo** | caminho que volta a um nó já visitado | `analisar → validar → revisar → analisar` |

## O que é um DAG?

*Directed Acyclic Graph*: grafo direcionado **acíclico**. Não existe caminho
que saia de um nó e volte a ele. Um DAG sempre termina (há um número finito de
caminhos), e é a forma clássica de descrever pipelines. Pode ter ramificação e
convergência:

```
             classificar
                  ↓
          ┌───────┴────────┐
          ↓                ↓
       pesquisar         analisar
          ↓                ↓
          └───────┬────────┘
                  ↓
              consolidar
                  ↓
               responder
```

## O que é um ciclo?

Um caminho que **volta**. Em agentes, ciclos são úteis (*validar, falhou,
revisar, tentar de novo*), mas perigosos: sem condição de parada o sistema
executa `A → B → A → B → A → ...` para sempre. **Um ciclo em um sistema de
agentes precisa possuir uma condição de parada.** (Exemplo 08.)

---

# BLOCO 3 — Estado compartilhado (Exemplo 03)

## O que é estado?

**Tudo o que o sistema sabe, neste momento, sobre a solicitação em
andamento.** Ele começa com a entrada e vai sendo preenchido:

| Momento | Conteúdo |
|---|---|
| Estado de **entrada** | `solicitacao` |
| Estado **intermediário** | `categoria`, `informacao`, `analise` (crescem a cada nó) |
| Estado **final** | `resposta` |

## Por que compartilhar estado?

Sem estado, cada etapa só conhece o que a anterior lhe passou por argumento. E
se `responder` precisa da categoria calculada três nós antes? Cada função
teria que carregar e repassar tudo. Com um **estado compartilhado**:

- nenhum nó precisa conhecer os outros, só o formato do estado;
- dá para reordenar, remover ou inserir nós sem reescrever as assinaturas;
- a decisão de rota (branch) lê o estado;
- você consegue inspecionar, a qualquer momento, "onde estamos e o que já sabemos".

## Exemplo 03 — TypedDict

*No exemplo anterior o grafo dizia por onde ir, mas não o que circulava.
Agora adicionamos o estado.*

```python
from typing import TypedDict

class Estado(TypedDict):
    solicitacao: str
    categoria: str
    resultado: str
    resposta: str
```

`TypedDict` é um dicionário com **campos e tipos declarados**: continua sendo
um `dict` comum em tempo de execução, mas documenta e checa (com ferramentas
de tipos) o que existe no estado. É o formato que o LangGraph usa.

```
            ESTADO
              │
      ┌───────┼────────┐
      ↓       ↓        ↓
    nó 1     nó 2     nó 3
      │       │        │
      └───────┼────────┘
              ↓
        estado atualizado
```

Cada nó **recebe o estado** e **devolve a parte que quer atualizar**:

```python
def classificar(estado: Estado) -> dict:
    return {"categoria": "simples"}
```

Sem LangGraph ainda, o exemplo usa um "motor" de três linhas escrito por nós:

```python
for no in [receber, classificar, analisar, responder]:
    estado.update(no(estado))
```

Guarde essa ideia: **é exatamente o que o LangGraph vai fazer por nós**, com
a diferença de que ele também decide *qual* nó vem a seguir.

**Transição:** temos o grafo (exemplo 02) e o estado (exemplo 03). Falta um
motor que execute um pelo outro, e é para isso que existe o LangGraph.

---

# BLOCO 4 — Primeiro LangGraph (Exemplos 04 e 05)

## O que é LangGraph?

Uma biblioteca Python para **descrever e executar grafos de execução sobre um
estado**. Você declara o tipo do estado, registra os nós (funções) e liga as
arestas; o LangGraph executa, mescla as atualizações no estado e decide o
próximo nó.

## Qual problema o LangGraph resolve?

O problema do exemplo 01: o fluxo de execução escondido em `if`, `while` e
ordem de chamadas. Com LangGraph:

- o fluxo é **explícito** (nós e arestas declarados, e não deduzidos do código);
- o estado é **único e tipado**;
- decisões e ciclos são **elementos do grafo**, não gambiarras no script;
- o grafo pode ser **desenhado** (`draw_mermaid()`) e inspecionado.

Ele **não** substitui LLM, Tools ou MCP: são coisas que você chama *dentro* dos nós.

## Exemplo 04 — o menor grafo possível

*No exemplo 03 escrevemos à mão o motor `estado.update(no(estado))`. Agora o
LangGraph faz isso por nós.*

```
START → receber → classificar → END
```

```python
from langgraph.graph import StateGraph, START, END

construtor = StateGraph(Estado)                    # 1
construtor.add_node("receber", receber)            # 2
construtor.add_node("classificar", classificar)
construtor.add_edge(START, "receber")              # 3
construtor.add_edge("receber", "classificar")
construtor.add_edge("classificar", END)
app = construtor.compile()                         # 4
resultado = app.invoke({"solicitacao": "..."})     # 5
```

| Passo | O que faz |
|---|---|
| 1. `StateGraph(Estado)` | cria o construtor; o tipo do estado define os campos do grafo |
| 2. `add_node(nome, funcao)` | registra uma etapa. O **nome** é o rótulo usado nas arestas |
| 3. `add_edge(a, b)` | "depois de `a`, sempre `b`". `START` e `END` são nós especiais de entrada/saída |
| 4. `compile()` | valida o grafo (nó inexistente, nó inalcançável...) e devolve o executável |
| 5. `invoke(estado)` | roda de `START` até `END` e devolve o **estado final** |

Duas coisas para reforçar:

- `StateGraph` é o **construtor** (você monta); `compile()` devolve o **aplicativo** (você executa).
- `invoke` aceita um estado **parcial** na entrada: os campos que os nós vão preencher podem ser omitidos.

## Como um nó funciona?

Um nó é uma função `estado -> dict`. Ela lê o que precisar do estado, faz seu
trabalho (chamar um LLM, uma tool, calcular...) e devolve **apenas os campos
que quer atualizar**.

## Como o estado passa pelos nós?

O LangGraph guarda o estado, passa-o ao nó, e **mescla** o dicionário devolvido
(campo a campo) no estado guardado. O próximo nó já recebe a versão atualizada.

## Exemplo 05 — vários nós e atualização de estado

*No exemplo anterior tínhamos 2 nós. Agora a cadeia completa*
`receber → classificar → analisar → responder`, *e um conceito novo: o que o nó devolve.*

```python
return estado                     # devolve o estado inteiro (funciona, mas...)
return {"categoria": "simples"}   # devolve só a ATUALIZAÇÃO (forma recomendada)
```

Por que devolver só a atualização? Cada nó fica **responsável por campos
específicos** e é fácil ver quem escreve o quê. O exemplo 05 anota isso em cada
log (`escreve: categoria`, `lê: categoria`).

Para *ver* a diferença, o exemplo usa `app.stream(..., stream_mode="updates")`,
que emite o que cada nó devolveu:

```
receber      -> {'solicitacao': '...'}
classificar  -> {'categoria': 'simples'}
analisar     -> {'resultado': '...'}
responder    -> {'resposta': '...'}
```

**Experimento:** troque o retorno de `classificar` por `{}`. Resultado:
`KeyError: 'categoria'` em `analisar`, porque o campo nunca foi escrito. Os nós
**compartilham** estado, então um nó depende do que os anteriores escreveram.

**Transição:** o grafo ainda é uma linha reta, e o LangGraph só fez o papel do
laço. O ganho real vem quando o próximo nó **depende do estado**: decisões
(Bloco 5).

---

# BLOCO 5 — Decisões e ciclos (Exemplos 06, 07 e 08)

## Exemplo 06 — fluxo condicional

*No exemplo 05 o grafo era uma linha reta. Agora `classificar` decide o caminho.*

```
                 classificar
                      |
              ┌───────┴───────┐
              ↓               ↓
           simples         complexa
              ↓               ↓
          responder       pesquisar → analisar → responder
```

```python
def rotear_apos_classificar(estado):        # lê o estado, devolve um RÓTULO
    return estado["categoria"]              # "simples" ou "complexa"

construtor.add_conditional_edges(
    "classificar",                          # de onde sai a decisão
    rotear_apos_classificar,                # quem decide
    {"simples": "responder",                # rótulo -> nó de destino
     "complexa": "pesquisar"},
)
```

**Como funcionam as conditional edges?**

| Pergunta | Resposta |
|---|---|
| Quem toma a decisão? | A **função de roteamento**. Ela **não é um nó**: não altera o estado, só o lê. |
| O que ela retorna? | Uma **string** (rótulo do caminho). |
| Como o LangGraph escolhe o próximo nó? | Procura o rótulo no dicionário e segue para o nó correspondente. |
| Por que é diferente de executar todas as funções? | Só **um** caminho executa. Chamar tudo e filtrar depois gasta chamadas de LLM/tools e causa efeitos colaterais. |

Repare no log: na solicitação simples **não aparecem** `[pesquisar]` nem
`[analisar]`. A decisão é parte da estrutura do grafo, e não um `if` escondido
dentro de uma função. É a resposta às perguntas 1 do exemplo 01.

> A decisão pode vir de uma regra (como aqui, tamanho do texto) ou de um LLM.
> O roteador só precisa devolver o rótulo. No exemplo 10, o classificador é o LLM.

## Exemplo 07 — DAG

*No exemplo anterior escolhíamos UM caminho. Agora seguimos DOIS caminhos ao
mesmo tempo e os juntamos.*

```
             classificar
                  ↓
          ┌───────┴────────┐
          ↓                ↓
       pesquisar         analisar
          ↓                ↓
          └───────┬────────┘
                  ↓
              consolidar
                  ↓
               responder
```

Por que é um DAG?

- **Direcionado:** toda aresta tem sentido.
- **Acíclico:** nenhum caminho volta a um nó já visitado.
- **Branch:** `classificar` tem duas saídas, e as duas executam (dois `add_edge` saindo do mesmo nó).
- **Merge:** `consolidar` tem duas entradas. `add_edge(["pesquisar", "analisar"], "consolidar")`, com **lista**, significa "espere as duas terminarem".

| | Exemplo 06 | Exemplo 07 |
|---|---|---|
| Como ramifica | `add_conditional_edges` | dois `add_edge` do mesmo nó |
| Quantos caminhos executam | **um** (escolha) | **todos** (paralelo) |
| Como junta | caminhos se reencontram | `add_edge([a, b], destino)` |

Cuidados: os ramos paralelos devem escrever **campos diferentes** do estado
(`informacao` e `analise`), senão um sobrescreve o outro; e a ordem dos logs
entre eles não é garantida. O objetivo do exemplo é conceitual: mostrar
ramificação, convergência e ausência de ciclo.

## Exemplo 08 — fluxo cíclico

*No DAG o fluxo sempre avança. Agora adicionamos a volta:*

```
analisar
   ↓
validar
   ↓
 ┌─┴──────────────┐
 ↓                ↓
OK               ERRO
 ↓                ↓
responder       revisar
                  ↓
                  └────→ analisar
```

Estado novo: `tentativas: int` e `validada: bool`.

**Como representar loops?** Um loop é só uma **aresta que volta**
(`revisar → analisar`). Nada mais.

**Como evitar loops infinitos?**

> **Um ciclo em um sistema de agentes precisa possuir uma condição de parada.**

Sem ela, temos `A → B → A → B → A → ...` para sempre (ou até gastar todo o
orçamento de chamadas ao LLM). No exemplo, o roteador impõe a parada lendo o
**estado**:

```python
def rotear_apos_validar(estado):
    if estado["validada"]:
        return "ok"                              # sucesso
    if estado["tentativas"] >= MAX_TENTATIVAS:
        return "desistir"                        # PARADA: tentativas esgotadas
    return "revisar"                             # volta pelo ciclo
```

Por isso o **contador de tentativas faz parte do estado**: a condição de parada
só pode olhar o que está lá.

O arquivo roda três casos:

| Caso | Situação | Resultado |
|---|---|---|
| 1 | validação passa na 2ª tentativa | 1 revisão e resposta validada |
| 2 | validador reprova sempre | para em 3 tentativas e responde marcando "(sem validação)" |
| 3 | mesmo ciclo **sem** condição de parada | `GraphRecursionError` |

No caso 3, o LangGraph impõe um teto de passos (`recursion_limit`; o padrão
varia entre versões e na 1.2.12 é 10007, então definimos 12 explicitamente) e levanta `GraphRecursionError`. Ele é a **rede de
segurança**, não a sua lógica de parada: nunca dependa dele para encerrar o
fluxo normalmente.

**Transição:** já sabemos ramificar, juntar e repetir. Falta colocar algo
inteligente dentro dos nós: um **LLM** (Bloco 6).

---

# BLOCO 6 — LLM e agente (Exemplos 09 e 10)

## Como colocar um LLM dentro do grafo?

Um LLM é **mais uma capacidade chamada dentro de um nó**, exatamente como uma
tool ou uma chamada MCP. O nó monta um prompt a partir do estado, chama o
modelo e grava o texto devolvido em um campo do estado:

```
                 ┌──────────────┐
                 │     LLM      │
                 └──────┬───────┘
                        ↓
                    resultado      (texto)
                        ↓
                    próximo nó     (o texto virou campo do ESTADO)
```

O LangGraph **não substitui** o LLM: ele controla **a ordem, as decisões e as
repetições** ao redor dele.

## A abstração `Modelo` e o `provedor.py`

Não espalhamos chamadas de SDK pelo grafo. O grafo conhece só isto:

```python
class Modelo:
    def gerar(self, prompt: str) -> str: ...
```

`provedor.py` (mesmo padrão da Aula 5: variável `PROVEDOR` no `.env`) devolve
a implementação escolhida:

| `PROVEDOR` | Implementação | Requer |
|---|---|---|
| `mock` (padrão) | `ModeloMock` (um `modelo_mock.py` por exemplo) | nada: sem internet, sem chave |
| `openai` | `ModeloOpenAI` | `OPENAI_API_KEY`, `OPENAI_DEFAULT_MODEL` |
| `ollama` | `ModeloOpenAI` com `base_url` local | Ollama rodando + `OLLAMA_MODEL` |
| `claude` | `ModeloClaude` (opcional) | `ANTHROPIC_API_KEY` |

```python
modelo = obter_modelo(ModeloMock())     # única linha que "sabe" qual modelo é
texto = modelo.gerar(prompt)            # o resto do arquivo só usa isto
```

Ollama e OpenAI usam a mesma classe porque o Ollama expõe uma API compatível
com a da OpenAI: só o `base_url` muda.

**Cuidados ao usar LLM real em um nó:**

- O LLM devolve **texto livre**. O nó precisa **normalizar** para o que o grafo
  entende (`"complexa" if "complexa" in texto.lower() else "simples"`).
- Nós que decidem o caminho (classificar, validar) devem pedir resposta
  **curta e em formato fixo** (`"OK"` ou `"ERRO: <motivo>"`).
- Modelos diferentes respondem de forma diferente: o Mock é determinístico, os
  demais não. Com LLM real, a 1ª análise pode passar direto na validação e o
  ciclo de revisão simplesmente não aparecer. Isso é o comportamento correto.

## Exemplo 09 — LLM como nó

*No exemplo 08 dominamos o controle de fluxo, mas os nós eram funções simuladas.
Agora três nós chamam um LLM.*

```
START → receber → classificar(LLM) → analisar(LLM) → responder(LLM) → END
```

O grafo é linear **de propósito**: o foco é mostrar que trocar o modelo não
mexe no grafo. Rode com Mock, depois com Ollama (ou OpenAI/Claude), sem alterar
o arquivo:

```powershell
python exemplos\09_llm_no_grafo\main.py
$env:PROVEDOR = "ollama"; python exemplos\09_llm_no_grafo\main.py
```

```
GRAFO
  │
  └── não precisa saber qual LLM está sendo utilizado
```

## Como um agente pode ser representado como um grafo?

Um agente que percebe, decide, age, avalia e repete é exatamente um **grafo de
execução sobre um estado**:

| Ideia de agente | No grafo |
|---|---|
| memória / contexto | **estado** compartilhado |
| raciocínio | nós que chamam **LLM** |
| ação no mundo | nós que chamam **tools** (ou MCP, ou outro agente via A2A) |
| decisão | **conditional edges** |
| autocorreção | **ciclo** validar → revisar → analisar |
| limite de segurança | **condição de parada** (`tentativas`) |

> Um agente complexo pode ser entendido como um sistema de estados que percorre
> um grafo de execução.

## Exemplo 10 — o agente completo

*Juntamos tudo: estado (03), atualização parcial (05), decisão (06), ciclo com
parada (08) e LLM atrás de `Modelo` (09).*

```
START → receber → classificar(LLM) ─┬─ simples ──────────────────→ responder → END
                                    └─ complexa → pesquisar(tool)
                                                      ↓
                                     ┌──────→ analisar(LLM)
                                     │             ↓
                                  revisar ←─ ERRO ─ validar(LLM) ─ OK ─→ responder
                                     (para após 3 tentativas)
```

Estado:

```python
class Estado(TypedDict):
    solicitacao: str   # entrada
    categoria: str     # classificar
    informacao: str    # pesquisar
    analise: str       # analisar
    resposta: str      # responder
    valida: bool       # validar
    tentativas: int    # analisar (condição de parada)
    feedback: str      # validar -> revisar -> analisar
```

`pesquisar` é uma **tool comum** (uma função com uma base de conhecimento):
mostra que o grafo mistura LLM e tools. Num sistema real, esse nó chamaria um
MCP Server (Aula 5) ou outro agente (A2A).

Rode e leia o log `[nó]`:

```
Solicitação: Qual o horário de atendimento?
Caminho percorrido: receber -> classificar -> responder

Solicitação: Preciso saber quais são os procedimentos para solicitar uma segunda via...
Caminho percorrido: receber -> classificar -> pesquisar -> analisar -> validar
                    -> revisar -> analisar -> validar -> responder
```

**Atenção ao estado inicial.** `receber` inicializa **todos** os campos: o
caminho simples nunca passa por `pesquisar` nem `analisar`, mas `responder`
lê `analise`. Um campo nunca escrito é `KeyError`, o mesmo do experimento do exemplo 05.

**Troca de modelo sem alterar o grafo:**

```powershell
python exemplos\10_agente_completo\main.py                 # Mock
$env:PROVEDOR = "ollama"                                    # Ollama local
python exemplos\10_agente_completo\main.py "Qual o horário de atendimento?"
```

**Transição:** vocês já viram cada peça. Agora vão montar um grafo sozinhos (Bloco 7).

---

# BLOCO 7 — Desafio (pasta `desafio/`)

Agora é com vocês. O enunciado completo está em [`desafio/README.md`](desafio/README.md).

## O que construir

O grafo de um **sistema de atendimento** com três caminhos:

```
START → receber → classificar_urgencia (LLM) ─┬─ urgente → encaminhar (tool) ──────────────→ responder → END
                                              └─ normal  → pesquisar (tool) ─┬─ sem_base ──→ responder
                                                                             └─ com_base
                                                                                  ↓
                                                                        ┌──→ analisar (LLM)
                                                                        │        ↓
                                                                     revisar ← ERRO ← validar (LLM) ─ OK ─→ responder
                                                                     (para após 3 tentativas)
```

Cada peça do desafio é uma peça que vocês já usaram:

| Peça do desafio | De onde vem |
|---|---|
| `Estado` compartilhado, nós devolvendo só a atualização | exemplos 03 e 05 |
| `urgente` × `normal` (uma decisão, um caminho) | exemplo 06 |
| `revisar → analisar` com `tentativas` no estado | exemplo 08 |
| LLM atrás de `Modelo`, sem acoplar o grafo ao provedor | exemplo 09 |
| tool e LLM convivendo como nós | exemplo 10 |

Você escreve os **nós**, os **roteadores** e a **montagem** dentro de `construir_grafo()` em `desafio/main.py`. O `Estado`, as tools, o `executar()` e o Mock já vêm prontos.

## Como saber que deu certo

```powershell
python desafio\main.py
python -m unittest desafio.test_desafio -v
```

Os testes conferem o **caminho percorrido** em quatro casos: urgente, normal com uma revisão, pergunta fora da base e validador que reprova sempre (o ciclo tem que parar em 3 tentativas).

## O desafio conceitual: o LLM sabe tudo?

O Caso 3 pergunta o prazo de uma restituição de imposto de renda de 2031. **Nenhuma base tem essa informação, e um LLM responderia mesmo assim**, com confiança e sem fonte.

A resposta certa do sistema é: *"não encontrei essa informação; encaminhei a um atendente"*. E quem garante isso **não é o prompt**: é uma **aresta** do grafo. Se `pesquisar` volta vazio, o caminho leva a `responder` sem passar por `analisar`, e o LLM nunca recebe a chance de inventar.

> Um prompt pede ao modelo que se comporte. Um grafo **impede** que ele tenha a oportunidade de não se comportar.

Este é o mesmo argumento do início da aula: o que importa no fluxo (decisões, ciclos, limites) deve estar **visível e verificável na estrutura**, e não escondido dentro de uma função ou de um texto de prompt.

## Fechamento

Nesta aula vocês percorreram o caminho completo:

```
fluxo linear  →  grafo (nós e arestas)  →  estado compartilhado  →  LangGraph
     →  decisão (conditional edges)  →  DAG (branch e merge)  →  ciclo com parada
     →  LLM dentro do nó  →  agente = grafo de execução sobre um estado
```

**LangGraph não substitui LLM, Tools ou MCP.** Ele dá forma ao **controle de execução** em volta deles: em que ordem, com quais decisões e com quais repetições. Na prática, os nós de um grafo real chamam **MCP Servers** (Aula 5) para acessar sistemas e **outros agentes** (A2A, Aula 4), e o grafo decide quando.

## Checklist final

- [ ] Sei explicar por que um fluxo linear deixa de ser suficiente
- [ ] Sei o que são nó, aresta, direção, branch e merge
- [ ] Sei a diferença entre DAG e grafo com ciclo
- [ ] Sei modelar o estado compartilhado com `TypedDict`
- [ ] Sei que um nó devolve **só a atualização** do estado, e o que acontece se um campo nunca é escrito
- [ ] Sei montar um `StateGraph` (`add_node`, `add_edge`, `compile`, `invoke`)
- [ ] Sei usar `add_conditional_edges` e por que a função de roteamento **não é um nó**
- [ ] Sei por que todo ciclo precisa de condição de parada **lida do estado**, e o que é `GraphRecursionError`
- [ ] Sei colocar um LLM dentro de um nó sem acoplar o grafo ao provedor
- [ ] Sei explicar um agente como um grafo de execução sobre um estado
- [ ] Resolvi o desafio e os 4 testes passam
- [ ] Sei explicar por que "sem base" deve ser uma aresta e não um pedido no prompt
