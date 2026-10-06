# Aula 7 — Sistemas Multiagentes, Persistência e Human-in-the-Loop

Cenário único da aula: uma **equipe de agentes que analisa uma denúncia sobre uma
contratação pública** (Pregão 045/2026, dados fictícios). Todos os exemplos são
**evoluções do mesmo caso**: começa com um agente que faz tudo e termina com uma
equipe de especialistas, com estado salvo em disco e um **humano que aprova ou
manda revisar** antes de a recomendação valer.

> **Ideia central:** agentes especializados colaboram por meio de um **estado
> compartilhado**; o estado é **persistido** (checkpoint) para poder ser retomado;
> e, nos pontos críticos, **o humano decide**.

O conteúdo teórico está em [`aula-07.md`](aula-07.md).

## Objetivos

Ao final da aula você será capaz de:

- explicar por que um agente generalista não escala e como **especialistas** resolvem isso;
- distinguir **estado** (a execução atual) de **memória** (o que sobrevive entre execuções);
- persistir a execução com **checkpointer** (SQLite) e retomá-la com `thread_id`, até em outro processo;
- montar uma **equipe multiagente** como grafo, com um orquestrador, e **paralelizar** especialistas independentes;
- pausar o grafo com `interrupt()` e retomá-lo com `Command(resume=...)`;
- modelar **aprovação e revisão** com limite de tentativas;
- separar **erro técnico** (retomar) de **rejeição humana** (revisar).

## Pré-requisitos

- **Python 3.10 ou mais novo**; Aulas 1–6 (principalmente a 6: `StateGraph`, arestas condicionais e ciclos).
- **LLM real em tudo**: exemplos, exercícios e desafios chamam um modelo de verdade. Você precisa de **uma** destas opções: `OPENAI_API_KEY` (padrão, como nas Aulas 4 e 5) **ou** um **Ollama** local (grátis). Não há Mock.
- Sem Docker e sem banco externo (a persistência usa um arquivo SQLite local).

## Instalação

```powershell
git clone https://github.com/franciscomduarte/material-pcdf.git
cd material-pcdf\aula7
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Se o PowerShell bloquear a ativação, rode uma vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
> No `cmd`: `.venv\Scripts\activate.bat`. Em Linux/Mac: `source .venv/bin/activate`.

```powershell
python -c "import langgraph; print('langgraph OK')"
```

## Como funciona a aula: esqueletos para implementar

Cada exemplo (`exemplos/NN_.../main.py`) é um **esqueleto**: o professor e a turma o implementam juntos,
**etapa por etapa**. Cada etapa está marcada com `# ETAPA n` e um `raise NotImplementedError("ETAPA n: ...")`:
troque o `raise` pelo código da etapa e rode o arquivo. Os comentários da etapa dizem o que escrever.

- Rodar o esqueleto **antes** de terminar uma etapa mostra `NotImplementedError: ETAPA n`: é esperado, e diz onde você está.
- No começo do arquivo há a lista das etapas, na ordem.
- Quando todas as etapas estiverem escritas, o exemplo roda inteiro, como descrito abaixo.
- O `exercicio.md` de cada pasta continua valendo: use o **seu** `main.py` já implementado como ponto de partida.

## Execução

Rode **sempre a partir da pasta `aula7/`**:

```powershell
python exemplos\01_agente_generalista\main.py
python exemplos\07_aprovacao_revisao\main.py
```

Os exemplos 01–03 não usam LangGraph (só o LLM).

## Exemplos — uma única evolução

```
01_agente_generalista     O problema: um agente faz tudo, e não dá para saber quem fez o quê
        ↓
02_agentes_especializados Investigador, Jurídico e Analista: cada um faz UMA coisa
        ↓
03_estado_compartilhado   Um TypedDict que todos leem/escrevem; ESTADO x MEMÓRIA
        ↓
04_persistencia           LangGraph + SQLite: checkpoint, thread_id, retomar em outro processo
        ↓
05_equipe_multiagente     Especialistas como nós de um grafo, com orquestrador
        ↓
06_human_in_the_loop      interrupt() e Command(resume=...): o humano decide no meio do fluxo
        ↓
07_aprovacao_revisao      Rejeição com feedback, ciclo de revisão limitado, erro técnico x rejeição
        ↓
08_paralelismo            Jurídico e Risco em paralelo (fan-out/fan-in), com medição de tempo
        ↓
desafio                   Você implementa: parecer com aprovação humana condicionada ao risco
desafio2                  Você implementa: especialistas em paralelo + aprovação em dois níveis
```

Cada pasta de exemplo tem um **`exercicio.md`** para você fazer sozinho: copie o `main.py` para
`exercicio.py` e resolva lá, sem mexer no original.

### Comandos para rodar cada exemplo

Sempre a partir da pasta `aula7/`.

| Exemplo | Comando | O que mostra |
|---|---|---|
| 01 | `python exemplos\01_agente_generalista\main.py` | um agente faz tudo, sem separar responsabilidades |
| 02 | `python exemplos\02_agentes_especializados\main.py` | Investigador, Jurídico e Analista, um de cada vez |
| 03 | `python exemplos\03_estado_compartilhado\main.py` | `TypedDict` compartilhado; estado x memória |
| 04 | `python exemplos\04_persistencia\main.py` | roda até o breakpoint e **encerra** o processo |
| 04 | `python exemplos\04_persistencia\main.py --retomar` | **outro** processo lê o checkpoint e continua |
| 04 | `python exemplos\04_persistencia\main.py --historico` | lista os checkpoints da execução |
| 04 | `python exemplos\04_persistencia\main.py --auto` | tudo no mesmo processo (demonstração rápida) |
| 05 | `python exemplos\05_equipe_multiagente\main.py` | equipe como grafo, com orquestrador (log `[nó]`) |
| 06 | `python exemplos\06_human_in_the_loop\main.py --simples` | a versão ingênua, com `input()` |
| 06 | `python exemplos\06_human_in_the_loop\main.py` | pausa com `interrupt()` e encerra |
| 06 | `python exemplos\06_human_in_the_loop\main.py --retomar sim` | outro processo retoma com a decisão |
| 06 | `python exemplos\06_human_in_the_loop\main.py --auto sim` | pausa e retoma no mesmo processo |
| 07 | `python exemplos\07_aprovacao_revisao\main.py` | interativo: **você** é o humano |
| 07 | `python exemplos\07_aprovacao_revisao\main.py --auto sim` | aprova de primeira |
| 07 | `python exemplos\07_aprovacao_revisao\main.py --auto nao,sim` | rejeita 1x, depois aprova |
| 07 | `python exemplos\07_aprovacao_revisao\main.py --auto nao,nao,nao` | rejeita até o limite de 3 versões |
| 07 | `python exemplos\07_aprovacao_revisao\main.py --falha-tecnica` | simula erro técnico e para |
| 07 | `python exemplos\07_aprovacao_revisao\main.py --retomar --auto sim` | retoma depois do erro técnico, sem contar tentativa |
| 08 | `python exemplos\08_paralelismo\main.py` | mesmo trabalho em fila (~2 s) e em paralelo (~1 s) |

Estrutura de diretórios:

```
aula7/
├── README.md            # este arquivo
├── aula-07.md           # material teórico
├── provedor.py          # configura o SDK de agentes para o provedor (PROVEDOR no .env)
├── agentes.py           # os agentes prontos (Agent), usados a partir do exemplo 03
├── caso.py              # as denúncias (dados fictícios, com os fatos no texto)
├── prompts.py           # as instruções dos agentes e a montagem das entradas (prontas)
├── .env.example
├── requirements.txt
├── exemplos/            # 01..08, cada um com exercicio.md
├── desafio/             # enunciado, esqueleto e testes
└── desafio2/            # idem: paralelo + aprovação em dois níveis
```

## Conceitos-chave no LangGraph

| Conceito | Significado |
|---|---|
| `compile(checkpointer=SqliteSaver(...))` | salva o estado a cada passo |
| `config = {"configurable": {"thread_id": "..."}}` | identifica a execução; mesma id = mesma execução |
| `app.get_state(config)` | lê o estado salvo e o `next` (próximo nó pendente) |
| `interrupt_before=["no"]` | breakpoint **estático**: para antes do nó, sempre |
| `interrupt(valor)` | pausa **dentro** do nó e devolve `valor` ao chamador (`"__interrupt__"`) |
| `Command(resume=X)` | retoma do checkpoint; `interrupt()` devolve `X` |
| `invoke(None, config)` | retoma um checkpoint sem resposta (ex.: depois de um erro técnico) |

> **Atenção:** ao retomar, o nó que chamou `interrupt()` roda **de novo desde o início**.
> Por isso nada com efeito colateral (enviar e-mail, gravar, cobrar) vem antes do `interrupt()`.

## Agentes: `Agent` + `Runner`

Os agentes são os mesmos das Aulas 1 a 4: `Agent(name=..., instructions=...)`, executados por `Runner.run_sync(agente, entrada)`.
O texto que o agente respondeu está em `.final_output`.

```python
from agents import Agent, Runner

investigador = Agent(name="Investigador", instructions="Liste apenas os fatos verificáveis.")
fatos = Runner.run_sync(investigador, denuncia).final_output
```

- **Exemplos 01 e 02:** você escreve os agentes à mão.
- **Exemplo 03 em diante:** os agentes já vêm prontos em [`agentes.py`](agentes.py) (as instruções estão em [`prompts.py`](prompts.py)) e o foco passa a ser o **estado** e o **grafo**: cada nó do LangGraph roda um agente.
- O grafo roda os nós em threads e cada `Runner.run_sync()` cria o seu laço de eventos; por isso o `provedor.py` configura o cliente sem conexões persistentes.

## Provedores de LLM (todos REAIS)

Mesmo padrão das Aulas 4 e 5: a variável `PROVEDOR` (no `.env` ou no ambiente) escolhe o modelo em
[`provedor.py`](provedor.py), que configura o SDK de agentes (`Agent` + `Runner`). **Os agentes e o grafo não mudam**, só o provedor. **Não há Mock nesta aula.**

| `PROVEDOR` | O que é | Precisa de |
|---|---|---|
| `openai` (padrão) | OpenAI (`gpt-4o-mini`) | `OPENAI_API_KEY` |
| `ollama` | modelo local, grátis | `ollama serve` no ar + modelo baixado (`OLLAMA_MODEL`) |

Configuração: `copy .env.example .env` e preencha só o que for usar. O `.env` está no `.gitignore`:
**nunca coloque chaves no código nem faça commit delas.** Sem a chave (ou sem o Ollama no ar) o programa **para** e diz o que fazer.

```powershell
copy .env.example .env         # preencha OPENAI_API_KEY ... ou use o Ollama:
$env:PROVEDOR = "ollama"; $env:OLLAMA_MODEL = "llama3.1"
python exemplos\07_aprovacao_revisao\main.py --auto nao,sim
```

**O que muda com LLM real:**
- **Cada execução é diferente.** Os textos variam; o que a aula ensina (caminho do grafo, pausa, retomada, estado) não varia.
- **Os fatos vêm do texto.** As denúncias de `caso.py` já trazem os fatos; o Investigador só os extrai e o LLM é proibido de inventar (veja `prompts.py`).
- **Tempo.** Uma chamada leva segundos na OpenAI e de dezenas de segundos a minutos no Ollama em CPU (um exemplo chama o modelo de 3 a 8 vezes). Planeje o tempo.
- **Paralelismo (exemplo 08).** Com OpenAI o ganho é claro; com Ollama local o servidor pode atender uma requisição por vez.

## Desafio

Em `desafio/`: um grafo em que **só casos de alto risco chamam o humano**; os de baixo
risco são aprovados automaticamente. Veja [`desafio/README.md`](desafio/README.md). Para conferir:

```powershell
python -m unittest desafio.test_desafio -v
```

O **desafio 2** (`desafio2/`) reúne a aula toda: `juridico` e `risco` em **paralelo**, revisão
limitada e **duas** aprovações humanas (gestor sempre; diretor só se o risco for alto).
Veja [`desafio2/README.md`](desafio2/README.md):

```powershell
python -m unittest desafio2.test_desafio2 -v
```

## Troubleshooting

- **`ModuleNotFoundError: langgraph`** — ambiente virtual inativo; rode `.venv\Scripts\Activate.ps1`.
- **"PROVEDOR=openai exige OPENAI_API_KEY" ou "o Ollama não responde"** — configure o `.env` (veja Provedores de LLM).
- **`ModuleNotFoundError: langgraph.checkpoint.sqlite`** — falta `langgraph-checkpoint-sqlite`; rode `pip install -r requirements.txt`.
- **`Não há execução pausada`** — rode antes o exemplo sem `--retomar`; ele cria o `checkpoints.db`.
- **Caracteres estranhos no Windows** — `$env:PYTHONIOENCODING = "utf-8"`.
- **`ModuleNotFoundError: prompts` / `caso` / `provedor`** — rode a partir de `aula7/`.
- Os `checkpoints.db` são recriados a cada execução nova e estão no `.gitignore`; pode apagar.

## Checklist final

- [ ] Ambiente criado e `langgraph` importa
- [ ] Rodei 01 e 02 e expliquei por que especialistas são melhores que um generalista
- [ ] Rodei 03 e sei a diferença entre estado e memória
- [ ] Rodei 04 em dois processos (`--retomar`) e sei o que é `thread_id`
- [ ] Rodei 05 e li o log `[nó]` do caminho percorrido
- [ ] Rodei 06 e sei a diferença entre `interrupt_before` e `interrupt()`
- [ ] Rodei 07 com `--auto nao,sim` e `--auto nao,nao,nao` e sei qual é a condição de parada
- [ ] Rodei 07 com `--falha-tecnica` e sei por que isso não é uma rejeição
- [ ] Rodei 08 e sei quando dá (e quando não dá) para paralelizar
- [ ] Fiz o `exercicio.md` de cada exemplo
- [ ] Resolvi os desafios 1 e 2
