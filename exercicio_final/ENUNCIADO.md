# Exercício Final: Assistente de Gestão de Pessoas

**Duração:** 5 horas. **Individual ou em dupla.** **Sem Docker e sem banco externo.**

## O problema

O servidor escreve um pedido em texto livre ("quero tirar férias de 12 a 26/04 e vender 10 dias", "vou a serviço a
Buenos Aires"...) e o sistema precisa:

1. **proteger** a entrada (dado de saúde, CPF, assunto fora do escopo, tentativa de manipulação);
2. **entender** o pedido (tipo, matrícula, datas, dias vendidos, destino);
3. **conferir** o cadastro do servidor, a **escala** da equipe e os **feriados**;
4. **analisar** o pedido com especialistas (Normas, Escala e Financeiro);
5. **redigir** o despacho (deferimento ou indeferimento) e **validá-lo**;
6. **pedir a aprovação da chefia**, que pode responder **dias depois**;
7. **registrar** a decisão sem duplicar, com **auditoria**;
8. deixar **rastro** de tudo o que aconteceu.

Você vai construir esse sistema **em etapas**. Cada etapa usa o que foi ensinado em uma ou mais aulas e diz **onde está o
exemplo parecido**. O domínio é novo (os exemplos das aulas falam de ocorrências e investigação), então você vai **adaptar**,
não copiar. Cada etapa também **aproveita o código da etapa anterior**. No fim, o sistema inteiro é um grafo LangGraph que
usa agentes, tools, APIs externas, um MCP Server seu, persistência e segurança.

> **🆕 Três itens usam um conceito já ensinado em um contexto que as aulas não usaram.** Não há exemplo pronto para eles:
> o mecanismo você já conhece, mas terá de adaptá-lo a um problema diferente.
>
> | Item | Onde | Conceito (aula) | Como foi usado em aula | Contexto novo no exercício |
> |---|---|---|---|---|
> | **🆕 A** | Etapa 2 | paralelismo fan-out/fan-in (Aula 7) | rodar especialistas **diferentes** ao mesmo tempo, para ganhar **tempo** | rodar a **mesma** extração 3 vezes e **votar**, para ganhar **confiabilidade** |
> | **🆕 B** | Etapa 6 | `RunHooks` (Aula 3) | **observar**: imprimir turnos e tools | **controlar**: barrar a execução quando um agente estoura o orçamento ou usa uma tool que não é dele |
> | **🆕 C** | Etapa 8 | human-in-the-loop com `interrupt()` (Aula 7) | **aprovar a saída** (o parecer final) | **decidir a entrada**: o guardrail ficou em dúvida, então um atendente do RH decide se o pedido segue |

```
START → receber → proteger_entrada ─┬─ bloqueado ────────────────────────────────→ recusar → END
                                    ├─ dúvida → triagem_humana (🆕 C) ─ não ──→ recusar
                                    │                └─ sim ─┐
                                    └─ ok ───────────────────┴→ extrair (🆕 A: 3 votos)
                                                                  ├─ incompleto/divergente → pedir_dados → END
                                                                  └─ ok → identificar_servidor (MCP)
                                                                            ├─ não encontrado → pedir_dados → END
                                                                            └─ ok → calcular_periodo (API feriados)
                                                                                     ┌─────────┼──────────┐   (em paralelo)
                                                                                  normas    escala    financeiro (API câmbio)
                                                                                     └─────────┼──────────┘
                                                                                           consolidar
                                                                     violação objetiva ┌───────┴───────┐ deferível
                                                                    (despacho de       ↓               ↓
                                                                     indeferimento) redigir_despacho ⇄ validar (máx. 3)
                                                                                               ↓
                                                         precisa da chefia? (N8) ── não ──────────────────────┐
                                                                  ↓ sim                                       │
                                     ┌── rejeitado (máx. 2) ── aprovacao_chefia (interrupt: pode durar dias)   │
                                     ↓                                  ↓ aprovado                            │
                              redigir_despacho                  registrar (MCP, idempotente, auditado) ←──────┘
                                                                        ↓
                                                                       END
```

## O que já vem pronto nesta pasta

| Arquivo | Para que serve |
|---|---|
| `dados/normas.md` | A **Norma Interna fictícia** com as regras N1 a N10 (férias, venda, início proibido, prazos, escala, abono, diária, aprovação, saúde, dados). **Leia antes de começar.** |
| `dados/servidores.csv` | Cadastro fictício: matrícula, equipe, saldo de férias, abonos restantes, salário-base e chefia imediata. |
| `dados/escala.csv` | Afastamentos já marcados (para conferir a regra N5). |
| `dados/diarias.csv` | Valor da diária por tipo de destino (capital, interior, exterior em USD). |
| `dados/feriados_2027.json` | Cópia local dos feriados nacionais de 2027, no formato da BrasilAPI (plano B quando a API cair). |
| `dados/casos.py` | 12 pedidos de teste, cada um com o **caminho esperado** no grafo. |
| `requirements.txt` | Dependências (as mesmas das Aulas 5 a 7). |
| `.env.example` | Modelo do `.env` (provedor e token de escrita). |

## Cronograma sugerido

| # | Etapa | Tempo | Relógio | Aulas |
|---|---|---|---|---|
| 0 | Preparação do ambiente e leitura da norma | 10 min | 0:00 – 0:10 | 1 |
| 1 | Primeiro agente com tool local | 15 min | 0:10 – 0:25 | 1, 4 |
| 2 | Extração estruturada do pedido + **🆕 A votação em paralelo** | 25 min | 0:25 – 0:50 | 2, 7 |
| 3 | Guardrails de entrada | 20 min | 0:50 – 1:10 | 2, 4, 8 |
| 4 | APIs externas com resiliência: feriados, câmbio, idempotência, limites | 20 min | 1:10 – 1:30 | 3, 6 |
| 5 | MCP Server do RH | 30 min | 1:30 – 2:00 | 5 |
| | *Intervalo* | 10 min | 2:00 – 2:10 | |
| 6 | Equipe de especialistas + **🆕 B hooks como controle** ⇒ **Marco mínimo** | 35 min | 2:10 – 2:45 | 2, 3, 4, 7 |
| 7 | O fluxo como grafo (LangGraph) | 45 min | 2:45 – 3:30 | 6, 7 |
| 8 | Persistência, aprovação da chefia + **🆕 C humano na entrada** | 35 min | 3:30 – 4:05 | 3, 7 |
| 9 | Segurança: privilégio mínimo, token e auditoria ⇒ **Marco completo** | 20 min | 4:05 – 4:25 | 5, 8 |
| 10 | Observabilidade | 15 min | 4:25 – 4:40 | 3, 5, 8 |
| 11 | Demonstração e entrega | 20 min | 4:40 – 5:00 | todas |

> **Estratégia:** não trave numa etapa. Se passar de 1,5× o tempo sugerido, deixe um `# TODO` explicando o que falta e siga.
> Uma etapa incompleta, mas que roda, vale mais do que um sistema perfeito que para na Etapa 4.

## Estrutura sugerida do seu projeto

```
exercicio_final/
├── dados/                  (já vem pronto)
├── provedor.py             copie de aula7/provedor.py
├── etapa1_agente.py ... etapa6_linear.py   um arquivo por etapa até a 6 (cada um importa o anterior)
├── ferramentas.py          tools locais: feriados, dias úteis, câmbio, protocolo
├── agentes.py              extratores, guardrail, Normas, Escala, Financeiro, Coordenador, Redator, Validador
├── mcp_rh.py               seu MCP Server
├── grafo.py                o grafo final (Etapas 7 a 10)
├── saidas/                 registros.json, auditoria.jsonl, metricas.jsonl, checkpoints.db
└── ENTREGA.md              o relatório da Etapa 11
```

---

## Etapa 0: Preparação e leitura da norma (10 min)

**Tarefa**

1. Crie e ative um ambiente virtual dentro de `exercicio_final/` e instale o `requirements.txt`.
2. Copie `.env.example` para `.env` e preencha o provedor (OpenAI ou Ollama).
3. Copie `aula7/provedor.py` para esta pasta (ele já trata OpenAI e Ollama e para com uma mensagem clara se faltar a chave).
4. Leia `dados/normas.md`. Para cada regra (N1 a N10), anote: **quem verifica**? Uma função Python (regra objetiva), um agente
   (interpretação) ou um humano (decisão)? Essa tabela vai guiar as próximas etapas.

**Pronto quando:** `python -c "import agents, langgraph, mcp; print('ok')"` imprime `ok`, e sua tabela N1–N10 está no `ENTREGA.md`.

**Onde olhar:** `aula1/provedor.py` (a ideia do `configurar()`), `aula7/README.md` (instalação), `aula7/provedor.py`.

---

## Etapa 1: Primeiro agente com tool local (15 min)

**Tarefa**

1. Crie um agente `AtendenteRH` que responde dúvidas do servidor em português, de forma breve.
2. Crie a tool `@function_tool` `consultar_servidor(matricula: str) -> str`, que lê `dados/servidores.csv` e devolve nome, equipe,
   saldo de férias e abonos restantes (**sem** o salário), ou `"matrícula não encontrada"`. Capriche na **docstring**: é ela que o LLM lê.
3. Rode o agente com duas perguntas: uma que **precisa** da tool ("Quantos dias de férias a matrícula 1002 ainda tem?") e uma que
   **não** precisa ("O que é abono pecuniário?").

**Pronto quando:** a tool é chamada só na primeira pergunta (imprima algo dentro da tool para provar).

**Onde olhar:** `aula1/segundo_agente.py` (agente com tool), `exercicios_resolvidos/aula4/ex10_function_tool.py`
(tool que consulta uma tabela), `aula8/exemplos/02_agente_tool/main.py`.

---

## Etapa 2: Extração estruturada do pedido e 🆕 votação em paralelo (25 min)

**Tarefa**

1. Modele com **Pydantic** a classe `Pedido` com: `tipo` (enum `ferias`, `abono`, `diaria`, `licenca_saude`, `outro`),
   `matricula` (ou `None`), `data_inicio` e `data_fim` (`AAAA-MM-DD` ou `None`), `dias_vendidos` (0 a 10), `destino` e
   `tipo_destino` (enum `capital`, `interior`, `exterior`, ou `None`), `justificativa`.
2. Use `Field(description=...)` para dizer ao LLM **o que** cada campo significa (ex.: "dias vendidos = abono pecuniário, N2").
3. Crie o agente `Extrator` com `output_type=Pedido` e rode-o nos casos `C1`, `C2`, `C5` e `C11` de `dados/casos.py`.

**Pronto quando:** `resultado.final_output` é um objeto `Pedido` (não texto); `C2` sai com `dias_vendidos=10`, `C11` com
`tipo_destino="exterior"` e `C5` com `matricula=None`.

**Onde olhar:** `aula2/agente_output.py` (o básico), `aula2/agente_output2.py` (**o mais parecido**: enums, listas e `Field(description=...)`).

### 🆕 A: Paralelismo para votar, não para ganhar tempo

**Conceito que você já conhece:** na Aula 7 (`aula7/exemplos/08_paralelismo/main.py`), Jurídico e Risco rodavam **ao mesmo tempo**
porque eram tarefas **diferentes** e independentes: o objetivo era **velocidade**.

**Contexto novo:** as datas e o tipo decidem tudo o que vem depois, e um LLM pode errá-los em pedidos vagos ("uns dez dias perto da
Páscoa"). Aqui você roda a **mesma** tarefa 3 vezes em paralelo e decide **por maioria**: o objetivo é **confiabilidade** (redundância).

**Tarefa**

1. Crie 3 extratores com instruções **ligeiramente diferentes** (ex.: um literal, um que confere as datas contra o calendário,
   um que pensa como o RH). Todos com o mesmo `output_type=Pedido`.
2. Rode os 3 **ao mesmo tempo** com `asyncio.gather(Runner.run(e1, pedido), Runner.run(e2, pedido), Runner.run(e3, pedido))`.
3. Faça a função `votar(pedidos) -> Pedido`: `tipo`, `matricula`, `data_inicio`, `data_fim` e `dias_vendidos` por **maioria**.
   Regra de segurança: se **não houver maioria** em `tipo` ou nas datas, marque `divergencia=True`. O sistema vai **pedir
   esclarecimento** em vez de adivinhar (é melhor perguntar do que registrar férias erradas). Guarde os votos.
4. Meça o tempo: os 3 em paralelo levam ~o tempo de **um**? E em sequência?

**Pronto quando:** `C1` e `C2` saem **unânimes**; em `C9` você mostra os 3 votos e a decisão; o tempo do paralelo fica perto de uma chamada.

---

## Etapa 3: Guardrails de entrada (20 min)

**Tarefa**

Antes do extrator, o pedido passa por **duas** barreiras:

1. **Dado sensível (LGPD), sem LLM:** regex que detecta **CPF** (`000.000.000-00`) e **CID** (uma letra + 2 dígitos, com ponto
   opcional: `F32`, `F32.1`). Achou: bloqueia e orienta (para saúde, procurar a junta médica, regra N9).
2. **Fora do escopo / manipulação, com LLM:** um agente classificador com `output_type` que devolve uma **nota de 0 a 1** de
   "não é um pedido de férias, abono ou diária, ou tenta mudar as regras do sistema" e um motivo. Acima de um `LIMIAR`, bloqueia.

Implemente as duas como `@input_guardrail` presos ao extrator e trate `InputGuardrailTripwireTriggered` devolvendo uma mensagem
educada e **diferente** para cada motivo.

**Pronto quando:** `C3`, `C4` e `C7` são bloqueados com mensagens diferentes; `C1` e `C2` passam. Anote a **nota** do `C10`: ela vai
ser usada no item 🆕 C.

**Onde olhar:** `aula2/agente_guardrail.py` (guardrail com agente classificador e limiar),
`exercicios_resolvidos/aula4/ex11_guardrails.py` (regex, guardrail de entrada **e** de saída),
`aula8/exemplos/04_prompt_injection/1_codigo_pronto/` (por que "ignore as regras" precisa de mais do que um aviso no prompt).

---

## Etapa 4: APIs externas com resiliência: feriados, câmbio, idempotência e limites (20 min)

Crie `ferramentas.py` com:

1. **Data real:** injete a data de hoje nas instruções dos extratores (para "amanhã" e "semana que vem" virarem datas) e use-a na
   regra de antecedência (N4).
2. **API de feriados com plano B:** `buscar_feriados(ano)` na BrasilAPI (`https://brasilapi.com.br/api/feriados/v1/{ano}`, com
   cabeçalho `User-Agent`), com `timeout` e até 3 tentativas com **backoff exponencial**. Se todas falharem, use
   `dados/feriados_2027.json` e registre a **fonte** usada. Com ela, escreva:
   - `dias_uteis(inicio, fim)`, `data_retorno(fim)` (próximo dia útil);
   - `inicio_permitido(data)` (regra N3: não pode começar nos 2 dias antes de feriado ou fim de semana).
3. **API de câmbio com retry:** `cotacao_usd_brl()` na Frankfurter (`https://api.frankfurter.app/latest?from=USD&to=BRL`), com o
   mesmo retry. Se falhar, a diária no exterior fica "a calcular" (o sistema **segue**, não inventa o câmbio).
4. **Protocolo idempotente:** `gerar_protocolo(matricula, tipo, data_inicio, data_fim)` = os 8 primeiros caracteres de um SHA-256
   dos campos normalizados. O mesmo pedido gera o **mesmo** protocolo.
5. **Limites:** toda chamada de `Runner` passa `max_turns` e roda dentro de `asyncio.wait_for(..., timeout=...)`. Trate
   `MaxTurnsExceeded` e `TimeoutError` separadamente.

**Pronto quando:** `inicio_permitido("2027-04-30")` é `False` (C12) e `inicio_permitido("2027-04-12")` é `True` (C2); com a internet
desligada, os feriados vêm do arquivo local após 3 tentativas visíveis no log; `gerar_protocolo` devolve o mesmo valor para `C1` e `C8`.

**Onde olhar:** `aula3/agente_retry.py` (injetar a data), `aula3/agente_retry2.py` (**retry com backoff**, erro de negócio x erro
técnico), `aula3/agente_retry4.py` (**a mesma API de câmbio**, Frankfurter), `aula6/exemplos/11_grafo_real/main.py`
(**a mesma API de feriados**, BrasilAPI, com plano B local), `aula3/agente_retry3.py` (**idempotência com hash**),
`aula3/agente_parada3.py` (timeout x `max_turns`).

---

## Etapa 5: MCP Server do RH (30 min)

Tire os dados de dentro do agente e coloque num **MCP Server** seu, `mcp_rh.py`, que lê os arquivos de `dados/` e grava as decisões
em `saidas/registros.json` (ou SQLite).

**Tools do server**

| Tool | Tipo | O que faz |
|---|---|---|
| `consultar_servidor(matricula)` | leitura | cadastro **sem** salário |
| `consultar_escala(equipe, inicio, fim)` | leitura | afastamentos da equipe no período e o **limite** da N5 (30%, mínimo 1) |
| `consultar_normas(tema)` | leitura | as regras de `normas.md` daquele tema (`ferias`, `abono`, `diaria`...) |
| `tabela_diarias(tipo_destino)` | leitura | moeda e valor da diária |
| `consultar_remuneracao(matricula)` | leitura **restrita** | salário-base (só o Financeiro precisa, ver item 🆕 B e Etapa 9) |
| `registrar_decisao(protocolo, matricula, tipo, inicio, fim, decisao, aprovador, despacho)` | **escrita** | grava; se o protocolo já existir, **não duplica** e avisa |

**Tarefa**

1. Implemente o server com `MCPServer` e `@mcp.tool()`, com **docstrings e tipos** caprichados.
2. Teste-o **sem agente** no MCP Inspector: `npx @modelcontextprotocol/inspector python mcp_rh.py`.
3. Ligue o server ao `AtendenteRH` com `MCPServerStdio` (troque a tool local da Etapa 1) e pergunte:
   "A equipe Cartório tem alguém de férias entre 12 e 26/07/2027?".
4. Escreva também a função `chamar_mcp(tool, argumentos)` (cliente MCP direto, sem agente): ela será usada pelos **nós** do grafo
   na Etapa 7.

**Pronto quando:** o Inspector lista as 6 tools; o agente responde a pergunta usando o server; registrar `C1` duas vezes gera um
único registro.

**Onde olhar:** `aula5/exemplos/03_mcp_parametros/server.py` (tool com parâmetros), `aula5/exemplos/05_multiplas_tools/server.py`
(várias tools no mesmo server), `aula5/exemplos/04_agente_mcp/agente.py` (`MCPServerStdio`),
`aula6/desafio2/mcp_unidades.py` (**MCP Server lendo CSV, o mais parecido**), `aula6/desafio2/main.py` (`chamar_mcp` dentro de um nó).

---

## Etapa 6: Equipe de especialistas, em fluxo linear, e 🆕 hooks como controle (35 min) ⇒ Marco mínimo

**Tarefa**

1. Crie, em `agentes.py`, especialistas com **uma responsabilidade cada** e **só as tools de que precisam**:
   - `Normas`: confere o pedido contra as regras (tool `consultar_normas`) e lista as regras cumpridas e violadas;
   - `Escala`: confere a N5 (tool `consultar_escala`) e, se houver conflito, **sugere** outro período;
   - `Financeiro`: calcula o valor da venda de férias (N2) ou das diárias (N7), usando `tabela_diarias`, `consultar_remuneracao`
     e a cotação da Etapa 4;
   - `Redator`: escreve o despacho (deferimento ou indeferimento) **usando só os fatos recebidos**, sem CPF nem dado de saúde (N10).
2. Crie um `Coordenador` que usa `Normas`, `Escala` e `Financeiro` **como tools** (`as_tool`) e monta um parecer único.
3. Monte `etapa6_linear.py`, um fluxo **em Python puro** (sem LangGraph), que encadeia tudo:
   guardrails → extração → MCP (servidor) → feriados → coordenador → redator → protocolo → MCP (registrar).

**Pronto quando:** `C1`, `C2` e `C11` chegam a um registro gravado com protocolo, `C6` vira um **indeferimento** com sugestão de
datas, e você consegue dizer **qual agente escreveu cada parte**.

**Onde olhar:** `aula4/ex03_agente_as_tool.py` (**agentes como tools, o mais parecido**), `aula2/agente_handoff2.py`,
`aula4/ex02_handoff_roteamento.py` (handoff, para comparar), `aula7/exemplos/02_agentes_especializados/main.py` (especialistas com
uma responsabilidade), `aula6/exemplos/01_fluxo_linear/main.py` (o fluxo linear e seus limites).

### 🆕 B: Hooks para controlar, não só para observar

**Conceito que você já conhece:** na Aula 3 (`aula3/agente_hook2.py`, `aula3/agente_loop.py`), os `RunHooks` só **imprimiam**:
"turno 2", "chamou a ferramenta X". Eles **assistiam** ao loop do agente.

**Contexto novo:** o mesmo gancho, que roda **antes** de cada tool (`on_tool_start`) e **antes** de cada chamada ao modelo
(`on_llm_start`), pode **barrar** a execução. Use-o como uma camada de **governança** da equipe:

1. **Lista de permissões por agente:** `{"Normas": {"consultar_normas"}, "Escala": {"consultar_escala"},
   "Financeiro": {"tabela_diarias", "consultar_remuneracao"}, "Coordenador": {...}}`. Se um agente tentar uma tool fora da sua
   lista (ex.: o `Coordenador` chamando `consultar_remuneracao` direto), a execução para. **O salário só passa pelo Financeiro.**
2. **Orçamento de chamadas:** no máximo `MAX_TOOLS` (ex.: 6) chamadas de tool por execução.
3. **Orçamento de turnos do modelo:** no máximo N chamadas ao LLM (complementa o `max_turns` da Etapa 4, mas com a **sua** mensagem
   e o **seu** registro).

Para barrar, lance uma exceção sua (ex.: `class LimiteExcedido(Exception)`) dentro do hook e trate-a em volta do `Runner`,
devolvendo uma mensagem clara e registrando o motivo. Como `on_tool_start` roda **antes** da tool, ela **não executa**.

**Pronto quando:** dando de propósito a tool `consultar_remuneracao` ao `Coordenador` e pedindo "qual o salário da 1002?", a execução
é barrada **antes** da tool rodar (prove com um `print` dentro da tool); com `MAX_TOOLS = 1`, o `C2` é parado antes do segundo
especialista; com os limites normais, tudo funciona. Na Etapa 10 você vai usar o **mesmo** hook para observabilidade: um mecanismo,
dois papéis.

> **Marco mínimo:** um sistema que, a partir do pedido, protege a entrada, extrai, consulta o MCP e as APIs, analisa e registra.
> Se você chegou aqui, já está aprovado. As próximas etapas transformam o "script" em um **sistema**.

---

## Etapa 7: O fluxo como grafo (LangGraph) (45 min)

Reescreva o fluxo da Etapa 6 como o grafo do início deste enunciado, em `grafo.py`. **Reaproveite** as funções e os agentes:
cada nó só chama o que já existe e devolve **o que mudou** no estado.

**Tarefa**

1. Defina o `Estado` (`TypedDict`) com, no mínimo: `texto`, `bloqueado`, `motivo_bloqueio`, `pedido`, `servidor`, `periodo`
   (dias úteis, feriados, retorno, fonte), `parecer_normas`, `parecer_escala`, `parecer_financeiro`, `violacoes`, `despacho`,
   `tentativas`, `erro_validacao`, `decisao`, `protocolo`, `caminho`.
   Use um **reducer** (`Annotated[list[str], operator.add]`) para `caminho` e para `violacoes`, para que cada nó só acrescente o seu.
2. **Arestas condicionais:** `proteger_entrada` (bloqueado/ok), `extrair` (incompleto/ok), `identificar_servidor`
   (não encontrado/ok) e `consolidar` (violação objetiva/deferível).
3. **Paralelismo:** `normas`, `escala` e `financeiro` rodam no **mesmo passo** (fan-out) e `consolidar` espera os três
   (fan-in por lista). Cada um escreve **só no seu campo**. Nesta etapa os especialistas viram **nós** (o grafo controla a ordem),
   e não mais tools do Coordenador.
4. **Ciclo com parada:** `validar` (LLM ou regra) aprova o despacho se ele citar a **matrícula**, o **período** e a **decisão**, e
   não contiver CPF nem CID. Se não, volta a `redigir_despacho` com o motivo. Máximo de **3 tentativas**, contadas no estado.
   Use também `recursion_limit`.
5. Imprima o `caminho` no fim e gere o diagrama com `app.get_graph().draw_mermaid()` (cole em mermaid.live e salve a imagem).

**Pronto quando:** rodando `C1`, `C2`, `C5`, `C6`, `C11` e `C12`, cada um percorre o caminho esperado em `dados/casos.py`, e no log
`normas`, `escala` e `financeiro` aparecem no mesmo passo.

**Onde olhar:** `aula6/exemplos/05_multiplos_nos/main.py` (nós devolvem só o que mudou), `aula6/exemplos/06_fluxo_condicional/main.py`,
`aula6/exemplos/07_dag/main.py` (ramifica e converge), `aula6/exemplos/08_fluxo_ciclico/main.py` (**ciclo com parada**),
`aula6/exemplos/10_agente_completo/main.py`, `aula6/exemplos/11_grafo_real/main.py` (**nós de LLM, MCP, API de feriados e tool**),
`aula6/desafio2/main.py` (LLM + MCP + API + ciclo), `aula7/exemplos/08_paralelismo/main.py` (**fan-out/fan-in**),
`aula7/exemplos/05_equipe_multiagente/main.py` (especialistas como nós), `aula8/exemplos/10_agentes_e_grafo/1_codigo_pronto/main.py`
(agente decide, grafo controla), `aula6/exemplos/04_langgraph_basico/main.py` (`draw_mermaid`).

---

## Etapa 8: Persistência, aprovação da chefia e 🆕 humano na entrada (35 min)

Aqui a persistência deixa de ser demonstração: a chefia **não responde na hora**. O pedido fica pausado até ela decidir, talvez
no dia seguinte, em outro processo.

**Tarefa**

1. Compile o grafo com um **checkpointer SQLite** (`saidas/checkpoints.db`) e use o **protocolo** como `thread_id`.
2. Crie o nó `aprovacao_chefia`, que só roda quando a N8 exige. Ele chama `interrupt()` com um **resumo** para a chefia (servidor,
   período, pareceres, valor, despacho proposto) e recebe `{"aprovado": bool, "aprovador": str, "motivo": str}`.
3. **Aprovado** → `registrar`. **Rejeitado** → volta a `redigir_despacho` com o motivo como feedback (máximo de **2 rejeições**;
   depois disso, registra como "indeferido pela chefia").
4. Faça o script aceitar `--pendentes` (lista os `thread_id` pausados e onde cada um parou), `--retomar <thread_id> sim <matricula_chefia>`
   e `--retomar <thread_id> "nao:motivo" <matricula_chefia>`, para que **outro processo** retome a execução.
5. **Regra de ouro:** nada com efeito colateral (gravar, notificar) **antes** do `interrupt()`: o nó roda de novo na retomada.

**Pronto quando:** `C2` pausa e o processo **termina**; `--pendentes` mostra o `C2` parado em `aprovacao_chefia`; um segundo comando
retoma e registra; `C1` registra sem pausar; `C6` e `C12` registram o indeferimento sem pausar.

**Onde olhar:** `aula7/exemplos/04_persistencia/main.py` (checkpoint, `thread_id`, retomar em outro processo, histórico),
`aula7/exemplos/06_human_in_the_loop/main.py` (`interrupt()` e `Command(resume=...)`),
`aula7/exemplos/07_aprovacao_revisao/main.py` (**o mais parecido**: rejeição com feedback e limite de tentativas),
`aula7/desafio2/` (aprovação em dois níveis), `aula3/agente_human.py` (a versão com `needs_approval` do Agents SDK, para comparar).

### 🆕 C: O humano decide a entrada, não só a saída

**Conceito que você já conhece:** na Aula 7 (`aula7/exemplos/06_human_in_the_loop/` e `aula7/exemplos/07_aprovacao_revisao/`), o
`interrupt()` pausava o grafo **no fim**, para o humano **aprovar o parecer** já pronto (como a chefia acima).

**Contexto novo:** o guardrail da Etapa 3 dá uma **nota** de 0 a 1, e você a cortava num único limiar. Mas um pedido como o `C10`
("meu pai foi internado, não sei se peço férias ou abono") não é nem "claramente um pedido válido" nem "claramente fora do escopo":
fala de saúde de terceiro e não tem tipo definido. Em vez de o sistema **adivinhar**, um **atendente do RH** decide, **no começo** do fluxo.

**Tarefa**

1. No nó `proteger_entrada`, troque o limiar único por **duas faixas**: nota `< LIMIAR_OK` (ex.: 0,4) → segue;
   nota `>= LIMIAR_BLOQUEIO` (ex.: 0,8) → bloqueia; entre os dois → **dúvida**.
2. Crie o nó `triagem_humana`, que chama `interrupt()` com o texto, a nota e o motivo do classificador, e recebe
   `{"segue": bool, "orientacao": str}`. **Sim** → `extrair` (com a orientação do atendente anexada ao texto); **não** → `recusar`
   com a orientação. A decisão vai para o estado e para a auditoria da Etapa 9.
3. Use o mesmo `--pendentes`/`--retomar`. Agora um mesmo pedido pode pausar **duas vezes** (na entrada e na chefia), e por
   **pessoas diferentes**: confira com `get_state(config).next` onde ele está.
4. Imprima a nota de cada caso e **calibre** as faixas para que `C1` e `C2` passem direto, `C4` bloqueie e `C10` pause.

**Pronto quando:** `C10` pausa em `triagem_humana`; retomar com "sim" leva à extração e com "nao" leva a `recusar`; `C1` não pausa
nenhuma vez e `C2` pausa só na chefia.

---

## Etapa 9: Segurança: privilégio mínimo, token e auditoria (20 min) ⇒ Marco completo

**Tarefa**

1. **Privilégio mínimo:** nenhum **agente** recebe `registrar_decisao`. Quem grava é o **nó** `registrar` do grafo. Só o
   `Financeiro` vê `consultar_remuneracao`.
2. **Autorização no server:** `registrar_decisao` exige o `TOKEN_REGISTRO` (lido do ambiente pelo **server**) e confere a N8:
   quando a decisão é um deferimento que precisa de chefia, o `aprovador` tem de ser a **chefia** daquele servidor no cadastro, e
   **nunca** o próprio servidor. Sem token ou com aprovador errado, o **server** nega, não o agente. Valide também `decisao`
   contra um conjunto fechado (`deferido`, `indeferido`, `indeferido_pela_chefia`).
3. **Auditoria:** toda tentativa de escrita, **permitida ou negada**, vira uma linha em `saidas/auditoria.jsonl` com: quando,
   `thread_id`, quem pediu, tool, protocolo, decisão (`ALLOW`/`DENY`) e motivo. As decisões da `triagem_humana` também entram.
4. **Guardrail de saída:** antes de gravar, confira que o despacho não contém CPF nem CID (N10). Se falhar, não grava.
5. Rode `C7` com o guardrail de entrada **desligado** e mostre que, mesmo assim, nada é aprovado e a auditoria registra `DENY`.
   Tente também retomar o `C2` com `--retomar <thread_id> sim 1002` (o próprio servidor aprovando): `DENY`.

**Pronto quando:** `saidas/auditoria.jsonl` tem linhas `ALLOW` (C1, C2 aprovado pela 1010) e `DENY` (C7 e a autoaprovação do C2).

**Onde olhar:** `aula5/exemplos/10_seguranca/server_seguro.py` (**o mais parecido**: token de supervisor, enum, auditoria no server),
`aula5/exemplos/10_seguranca/agente_seguranca.py` (os 4 cenários de teste), `aula8/exemplos/06_excessive_agency/1_codigo_pronto/main.py`
(o problema de dar tools demais), `aula8/exemplos/05_guardrail_saida/1_codigo_pronto/main.py` (guardrail de saída).

> **Marco completo:** grafo com decisões, paralelismo, ciclo, aprovação persistida que sobrevive ao fim do processo, e escrita
> protegida e auditada.

---

## Etapa 10: Observabilidade (15 min)

**Tarefa**

1. Reaproveite o hook do item 🆕 B para **também** registrar, para cada agente: início, cada tool chamada (com argumentos) e o resultado.
2. Para cada **nó** do grafo, meça o tempo e, quando houver agente, os **tokens** (`resultado.context_wrapper.usage`). Grave uma
   linha por nó em `saidas/metricas.jsonl`, com o mesmo `thread_id` da auditoria. Registre também a **fonte** dos feriados
   (API ou arquivo local) e se o câmbio veio da API.
3. No fim de cada execução, imprima um resumo: nós percorridos, tempo total, nó mais lento, tokens totais.

**Pronto quando:** você responde, para `C2`, **onde o tempo foi gasto**, **quantos tokens** custou e **quanto a votação do 🆕 A
custou a mais**, só olhando os arquivos.

**Onde olhar:** `aula3/agente_hook2.py` e `aula3/agente_hook3.py` (`RunHooks`), `aula5/exemplos/11_observabilidade/agente_observavel.py`
(ler `result.new_items`), `aula8/exemplos/03_observabilidade/1_codigo_pronto/passo1_trace.py` (traces; o Langfuse do passo 2 é **opcional**).

---

## Etapa 11: Demonstração e entrega (20 min)

1. Rode os **12 casos** de `dados/casos.py` e preencha, no `ENTREGA.md`, uma tabela:
   caso | caminho percorrido | resultado (bloqueado / pediu dados / triagem humana / indeferido / pausou na chefia / registrado
   + protocolo) | bateu com o esperado?
2. Cole o diagrama Mermaid do seu grafo e a tabela N1–N10 da Etapa 0, agora com a coluna "onde foi implementada".
3. Responda, em até 3 linhas cada:
   - Quem decide o caminho no seu sistema: o LLM, o grafo, as regras ou um humano? Dê um exemplo de cada.
   - Se o guardrail de entrada falhar, o que ainda impede uma autoaprovação?
   - Por que o nó da chefia não pode gravar nada antes do `interrupt()`?
   - Qual dado veio do **MCP**, qual de **API externa** e qual de **tool local**? Por que essa divisão?
   - 🆕 A: votar triplica o custo da extração. Em que pedidos vale a pena?
   - 🆕 B: hook, guardrail e regra no server (Etapa 9) podem barrar uma ação. Qual a diferença de **onde** cada um atua?
   - 🆕 C: o que muda quando o humano decide a **entrada** em vez da **saída**? Quem é consultado em cada pausa?
   - O que você mudaria para colocar este sistema em produção?
4. Faça commit do código (sem o `.env`!) e entregue o link ou o `.zip`.

---

## Critérios de avaliação (100 pontos)

| Etapa | Pontos | O que conta |
|---|---|---|
| 0 a 2 | 8 | tabela N1–N10; agente com tool; saída Pydantic com enums e descrições |
| **🆕 A** | 5 | 3 extratores em paralelo, votação por maioria, divergência vira pedido de esclarecimento, tempo medido |
| 3 | 8 | dois guardrails distintos (regex CPF/CID e LLM), bloqueios com mensagens claras |
| 4 | 8 | duas APIs com retry e plano B, N3 calculada com feriados, protocolo idempotente, limites |
| 5 | 12 | MCP Server com 6 tools bem descritas, testado no Inspector e usado por um agente |
| 6 | 8 | especialistas com uma responsabilidade e só as tools necessárias; coordenador com `as_tool` |
| **🆕 B** | 5 | hook que barra por lista de permissões e por orçamento, antes de a tool rodar |
| 7 | 15 | grafo com 4 decisões, fan-out/fan-in de 3 ramos, ciclo com parada e `caminho` correto |
| 8 | 9 | checkpoint, `interrupt()` da chefia, `--pendentes`, retomada em outro processo, limite de rejeições |
| **🆕 C** | 5 | duas faixas no guardrail, `triagem_humana` com `interrupt()`, faixas calibradas |
| 9 | 8 | privilégio mínimo, token e N8 no server, auditoria ALLOW/DENY, guardrail de saída |
| 10 a 11 | 9 | métricas por nó, 12 casos demonstrados, respostas de reflexão |

**Faixas:** até a Etapa 6 (Marco mínimo) ≈ 55 pontos; até a Etapa 9 (Marco completo) ≈ 90; o resto, Etapas 10–11 e bônus.
Os itens 🆕 não bloqueiam os marcos: se travar num deles, siga com a etapa sem o item e volte depois.

## Bônus (para quem terminar antes; até +10 pontos, sem passar de 100)

| Bônus | Onde olhar |
|---|---|
| Publicar `rh/afastamento/registrado` via **MQTT** e um assinante que mantém o **painel de ausências por equipe** | `aula4/ex04_mqtt_pub.py`, `aula4/ex06_mqtt_estatistica.py` |
| **Contract Net** para cobrir a escala: quando um afastamento é registrado, os colegas da equipe "propõem" cobrir o plantão e o coordenador escolhe quem tem menos plantões no mês | `aula4/ex08_fipa_acl.py`, `exercicios_resolvidos/aula4/ex12_cnp_coordenador.py`, `exercicios_resolvidos/aula4/ex12_cnp_viatura.py` |
| Expor o sistema com **FastAPI**: `POST /pedidos`, `GET /pendentes` e `POST /pedidos/{thread_id}/decisao` (a chefia aprova pela API) | `aula2/main.py` |
| Subir o MCP Server via **HTTP com token Bearer** em vez de stdio | `aula5/exemplos/14_mcp_http_basico/`, `aula5/exemplos/16_mcp_http_autenticado/` |
| **Memória** da conversa com o servidor (`SQLiteSession`): "e se eu mudar para a semana seguinte?" | `aula2/agente_memoria.py`, `aula2/agente_sessao2.py` |
| Trocar a decisão do guardrail por um decisor **tipado com confiança** (JEV) | `aula6/desafio3/` |

## Regras

- Use **dados fictícios**. Nunca coloque CPF, CID, nomes ou matrículas reais nos testes.
- A chave da API fica **só** no `.env`, que não vai para o git.
- As datas dos casos são de 2027 (a N4 exige antecedência). Se precisar de outro ano, ajuste os casos e a cópia local dos feriados.
- Como o LLM varia, **compare estado e caminho, não texto**: "foi bloqueado?", "pausou?", "gerou protocolo?".
- Pode consultar todo o material das aulas, a documentação oficial e os colegas. Explique no `ENTREGA.md` o que veio de onde.
