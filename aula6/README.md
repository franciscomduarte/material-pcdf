# Aula 6 — Modelagem de Sistemas Baseados em Grafos (LangGraph)

Cenário único da aula: um **sistema de análise e tratamento de solicitações**.
Um usuário envia um pedido (ex.: *"Preciso saber como solicitar uma segunda via
de um documento"*) e o sistema recebe, classifica, pesquisa, analisa, valida,
revisa e responde. Todos os exemplos são **evoluções do mesmo processo**.

> **Ideia central:** um agente complexo pode ser entendido como um sistema de
> estados que percorre um grafo de execução.
>
> **LangGraph nos permite transformar o fluxo de execução de um sistema baseado
> em agentes em um grafo explícito de estados, nós e transições.**

Este README cobre o setup e o mapa da aula. O conteúdo teórico está em
[`aula-06.md`](aula-06.md).

## Objetivos

Ao final da aula você será capaz de:

- explicar por que um fluxo linear `A → B → C` deixa de ser suficiente;
- descrever nós, arestas, grafos direcionados, DAGs e ciclos;
- modelar um processo com **estado compartilhado** (`TypedDict`);
- implementar grafos com **LangGraph** (`StateGraph`, arestas condicionais, ciclos);
- garantir **condição de parada** em ciclos;
- colocar um **LLM dentro de um nó** sem acoplar o grafo a um provedor;
- enxergar um agente como um **grafo de execução**.

## Pré-requisitos

- **Python 3.10 ou mais novo**.
- Aulas 1–5 (LLMs, tools, agentes, A2A, MCP). A Aula 6 parte delas.
- **Nenhuma chave de API é necessária** para os conceitos fundamentais. Provedores reais
  (OpenAI, Ollama, Claude) são complementares (exemplos 09 e 10).
- Sem Docker, sem banco de dados, sem serviços externos.

## Instalação

PowerShell (Windows):

```powershell
git clone https://github.com/franciscomduarte/material-pcdf.git
cd material-pcdf\aula6
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Se o PowerShell bloquear a ativação (*"a execução de scripts foi desabilitada"*), rode
> uma vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. No `cmd`, use
> `.venv\Scripts\activate.bat`. Em Linux/Mac: `source .venv/bin/activate`.

Confirme a instalação:

```powershell
python -c "import langgraph; print('langgraph OK')"
```

## Execução

Cada exemplo é uma pasta com um `main.py`. Rode a partir da pasta do exemplo ou
informando o caminho:

```powershell
python exemplos\01_fluxo_linear\main.py
python exemplos\10_agente_completo\main.py
```

Os exemplos 01–03 são Python puro (não precisam nem do LangGraph).

## Exemplos — uma única evolução

```
01_fluxo_linear         O problema: A → B → C, sem decisão, sem volta
        ↓
02_grafo_conceitual     O mesmo processo como grafo (nós + arestas), em Python puro
        ↓
03_estado_compartilhado Um TypedDict que todos os nós leem e atualizam
        ↓
04_langgraph_basico     Primeiro StateGraph: START → receber → classificar → END
        ↓
05_multiplos_nos        Cadeia completa; nós devolvem só o que mudou
        ↓
06_fluxo_condicional    classificar decide: simples → responder | complexa → pesquisar
        ↓
07_dag                  Ramificação e convergência (sem ciclo)
        ↓
08_fluxo_ciclico        validar → revisar → analisar, com condição de parada
        ↓
09_llm_no_grafo         LLM como nó, atrás da abstração Modelo (Mock, OpenAI, Ollama ou Claude)
        ↓
10_agente_completo      Tudo junto: o agente como grafo de execução
        ↓
desafio                 Você implementa: análise de solicitação de atendimento
```

Estrutura de diretórios:

```
aula6/
├── README.md            # este arquivo
├── aula-06.md           # material teórico (perguntas e respostas da aula)
├── provedor.py          # escolhe o LLM (PROVEDOR no .env)
├── .env.example
├── requirements.txt
├── exemplos/            # 01..10
└── desafio/             # enunciado, esqueleto, Mock e casos de teste
```

## LangGraph

LangGraph **não substitui** LLM, Tools ou MCP. Ele fornece uma forma explícita de
modelar o **fluxo de execução** em torno deles.

| Conceito no LangGraph | Significado |
|---|---|
| `StateGraph(Estado)` | o grafo, parametrizado pelo tipo do estado |
| `add_node("nome", funcao)` | nó: função `estado -> atualização parcial do estado` |
| `add_edge(a, b)` | aresta fixa: depois de `a`, sempre `b` |
| `add_conditional_edges(a, roteador)` | aresta condicional: `roteador(estado)` escolhe o próximo nó |
| `START` / `END` | pontos de entrada e saída |
| `compile()` | valida o grafo e devolve o executável |
| `invoke(estado_inicial)` | executa e devolve o estado final |

Limite de segurança contra ciclos infinitos: `invoke(estado, {"recursion_limit": N})`.
Ao estourar, o LangGraph levanta `GraphRecursionError` (mostrado no exemplo 08).

## Provedores de LLM (Mock, OpenAI, Ollama, Claude)

Mesmo padrão da Aula 5: a variável `PROVEDOR` (no `.env` ou no ambiente) escolhe o
modelo, lida em [`provedor.py`](provedor.py). **O grafo não muda**, só o provedor.

| `PROVEDOR` | O que é | Precisa de |
|---|---|---|
| `mock` (padrão) | LLM de mentira, determinístico | nada (sem internet, sem chave) |
| `openai` | OpenAI | `OPENAI_API_KEY` |
| `ollama` | modelo local, grátis | Ollama rodando + modelo baixado |
| `claude` | Anthropic (opcional) | `ANTHROPIC_API_KEY` |

Configuração: `copy .env.example .env` e preencha só o que for usar. O `.env` está no
`.gitignore`: **nunca coloque chaves no código nem faça commit delas**.

### Mock

`ModeloMock` roda sem internet e sem chave, e é o padrão. Foi escrito para produzir um
fluxo realista, inclusive uma primeira análise reprovada na validação para que o ciclo
de revisão apareça na execução.

```powershell
python exemplos\10_agente_completo\main.py
```

### Ollama (local)

```powershell
ollama pull llama3.1                 # uma vez
$env:PROVEDOR = "ollama"
$env:OLLAMA_MODEL = "llama3.1"       # o nome do modelo que você baixou
python exemplos\10_agente_completo\main.py
```

Em CPU, modelos de 7-8B levam dezenas de segundos por chamada; o exemplo 10 faz de 2 a 8.

### OpenAI

```powershell
$env:PROVEDOR = "openai"
$env:OPENAI_API_KEY = "sua-chave"
python exemplos\10_agente_completo\main.py
```

### Claude (opcional)

```powershell
$env:PROVEDOR = "claude"
$env:ANTHROPIC_API_KEY = "sua-chave"
python exemplos\10_agente_completo\main.py
```

Para voltar ao Mock: `$env:PROVEDOR = "mock"`. Com LLM real, a 1ª análise pode passar
direto na validação e o ciclo de revisão não aparecer (é esperado).

## Desafio

Em `desafio/`: implemente o grafo de **análise de solicitação de atendimento**
(urgente/normal, validação, revisão com limite de tentativas, e o caso em que a
base não sabe responder). Há também um desafio conceitual: *o LLM sabe tudo?*
Veja [`desafio/README.md`](desafio/README.md). Para conferir:

```powershell
python -m unittest desafio.test_desafio -v
```

## Troubleshooting

- **`ModuleNotFoundError: langgraph`** — o ambiente virtual não está ativo; rode `.venv\Scripts\Activate.ps1`.
- **`GraphRecursionError`** — no exemplo 08 é intencional (demonstra o ciclo sem parada). Em outro lugar, seu ciclo não tem condição de parada.
- **Chave ausente** (`OPENAI_API_KEY`/`ANTHROPIC_API_KEY`) — o exemplo aborta com mensagem clara; use `PROVEDOR=mock` ou `ollama`.
- **Ollama lento ou sem resposta** — confira `ollama list` e se o modelo de `OLLAMA_MODEL` existe.

## Checklist final

- [ ] Ambiente criado e `langgraph` importa
- [ ] Rodei os exemplos 01 a 03 e expliquei por que o fluxo linear não basta
- [ ] Rodei 04 e 05 e sei o que um nó retorna (atualização parcial do estado)
- [ ] Rodei 06 e vi os dois caminhos (simples e complexa)
- [ ] Rodei 07 e sei por que é um DAG
- [ ] Rodei 08 e sei qual é a condição de parada do ciclo
- [ ] Rodei 09/10 com o Mock e li o log `[nó]` do caminho percorrido
- [ ] Rodei 10 com Ollama, OpenAI ou Claude sem alterar o grafo (opcional)
- [ ] Resolvi o desafio
