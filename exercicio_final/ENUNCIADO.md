# Exercício Final: Delegacia Virtual Inteligente

**Duração:** 5 horas. **Individual ou em dupla.** **Sem Docker e sem banco externo.**

## O problema

O cidadão escreve um relato em texto livre ("fui assaltado em Taguatinga...") e o sistema precisa:

1. **proteger** a entrada (dado pessoal, assunto fora do escopo, tentativa de manipulação);
2. **entender** o relato (tipo, gravidade, bairro, data, envolvidos);
3. **encontrar a delegacia competente** e se ela tem viatura;
4. **analisar** o caso com especialistas (jurídico e investigação);
5. **redigir** o registro e **validá-lo**;
6. **pedir aprovação humana** quando o caso for grave;
7. **registrar** a ocorrência sem duplicar, com **auditoria**;
8. deixar **rastro** de tudo o que aconteceu.

Você vai construir esse sistema **em etapas**. Cada etapa usa o que foi ensinado em uma ou mais aulas, e diz
**onde está o exemplo parecido**. Cada etapa também **aproveita o código da etapa anterior**. No fim, o sistema inteiro é um
grafo LangGraph que usa agentes, tools, um MCP Server seu, persistência e segurança.

```
START → receber → proteger_entrada ─┬─ bloqueado ─────────────────────────────→ recusar → END
                                    └─ ok → extrair ─┬─ sem_local ────────────→ pedir_local → END
                                                     └─ ok → localizar_delegacia (MCP)
                                                               ├─ sem_viatura ─→ escalar → END
                                                               └─ ok ─┬→ juridico ─────┐   (em paralelo)
                                                                      └→ investigador ─┴→ consolidar
                                                                                             ↓
                                                     ┌──────────── erro (máx. 3) ──── redigir_registro ⇄ validar
                                                     │                                       ↓ ok
                                                     │                       gravidade alta? ┴ baixa ─────────┐
                                                     │                             ↓                          │
                                                     └─ rejeitado (máx. 2) ── aprovacao_humana (interrupt)    │
                                                                                   ↓ aprovado                 │
                                                                             registrar (MCP, idempotente) ←───┘
                                                                                   ↓
                                                                                  END
```

## O que já vem pronto nesta pasta

| Arquivo | Para que serve |
|---|---|
| `dados/delegacias.csv` | Delegacias fictícias (bairro, coordenadas, viaturas disponíveis, especialidade). Fonte do seu MCP Server. |
| `dados/bairros.py` | Dicionário `BAIRROS` (bairro → latitude/longitude), o mesmo do desafio 2 da Aula 6. |
| `dados/casos.py` | 8 relatos de teste, cada um com o **caminho esperado** no grafo. |
| `requirements.txt` | Dependências (as mesmas das Aulas 5 a 7). |
| `.env.example` | Modelo do `.env` (provedor e token de escrita). |

## Cronograma sugerido

| # | Etapa | Tempo | Relógio | Aulas |
|---|---|---|---|---|
| 0 | Preparação do ambiente | 10 min | 0:00 – 0:10 | 1 |
| 1 | Primeiro agente com tool local | 20 min | 0:10 – 0:30 | 1, 4 |
| 2 | Extração estruturada do relato | 20 min | 0:30 – 0:50 | 2 |
| 3 | Guardrails de entrada | 20 min | 0:50 – 1:10 | 2, 4, 8 |
| 4 | Resiliência: data real, retry, idempotência, limites | 20 min | 1:10 – 1:30 | 3 |
| 5 | MCP Server da delegacia | 35 min | 1:30 – 2:05 | 5 |
| | *Intervalo* | 10 min | 2:05 – 2:15 | |
| 6 | Equipe de especialistas (fluxo linear) ⇒ **Marco mínimo** | 25 min | 2:15 – 2:40 | 2, 4, 7 |
| 7 | O fluxo como grafo (LangGraph) | 45 min | 2:40 – 3:25 | 6, 7 |
| 8 | Persistência e aprovação humana | 30 min | 3:25 – 3:55 | 3, 7 |
| 9 | Segurança: privilégio mínimo, token e auditoria ⇒ **Marco completo** | 25 min | 3:55 – 4:20 | 5, 8 |
| 10 | Observabilidade | 15 min | 4:20 – 4:35 | 3, 5, 8 |
| 11 | Demonstração e entrega | 25 min | 4:35 – 5:00 | todas |

> **Estratégia:** não trave numa etapa. Se passar de 1,5× o tempo sugerido, deixe um `# TODO` explicando o que falta e siga.
> Uma etapa incompleta, mas que roda, vale mais do que um sistema perfeito que para na Etapa 4.

## Estrutura sugerida do seu projeto

```
exercicio_final/
├── dados/                  (já vem pronto)
├── provedor.py             copie de aula7/provedor.py
├── etapa1_agente.py ... etapa6_linear.py   um arquivo por etapa até a 6 (cada um importa o anterior)
├── ferramentas.py          tools locais: data, clima com retry, protocolo
├── agentes.py              extrator, guardrail, jurídico, investigador, redator, validador
├── mcp_delegacia.py        seu MCP Server
├── grafo.py                o grafo final (Etapas 7 a 10)
├── saidas/                 auditoria.jsonl, metricas.jsonl, checkpoints.db
└── ENTREGA.md              o relatório da Etapa 11
```

---

## Etapa 0: Preparação (10 min)

**Tarefa**

1. Crie e ative um ambiente virtual dentro de `exercicio_final/` e instale o `requirements.txt`.
2. Copie `.env.example` para `.env` e preencha o provedor (OpenAI ou Ollama).
3. Copie `aula7/provedor.py` para esta pasta (ele já trata OpenAI e Ollama e para com uma mensagem clara se faltar a chave).

**Pronto quando:** `python -c "import agents, langgraph, mcp; print('ok')"` imprime `ok`.

**Onde olhar:** `aula1/provedor.py` (a ideia do `configurar()`), `aula7/README.md` (instalação), `aula7/provedor.py`.

---

## Etapa 1: Primeiro agente com tool local (20 min)

**Tarefa**

1. Crie um agente `Atendente` com instruções de atendimento ao cidadão (responde em português, de forma breve).
2. Crie a tool `@function_tool` `localizar_bairro(bairro: str) -> str`, que consulta o dicionário `BAIRROS`
   (`dados/bairros.py`) e devolve as coordenadas, ou `"bairro desconhecido"`. Escreva uma **docstring** boa: é ela que o LLM lê.
3. Rode o agente com duas perguntas: uma que **precisa** da tool ("Onde fica Taguatinga?") e uma que **não** precisa ("O que é um boletim de ocorrência?").

**Pronto quando:** a tool é chamada só na primeira pergunta (imprima algo dentro da tool para provar).

**Onde olhar:** `aula1/segundo_agente.py` (agente com tool), `exercicios_resolvidos/aula4/ex10_function_tool.py`
(tool que consulta uma tabela), `aula8/exemplos/02_agente_tool/main.py`.

---

## Etapa 2: Extração estruturada do relato (20 min)

**Tarefa**

1. Modele com **Pydantic** a classe `Ocorrencia` com: `tipo`, `gravidade` (enum `alta`/`baixa`), `bairro` (ou `None`),
   `data_fato`, `envolvidos` (lista de `Envolvido` com `nome` e `papel`: vítima, suspeito, testemunha, comunicante), `objetos` e `resumo`.
2. Use `Field(description=...)` para dizer ao LLM **o que** cada campo significa. Defina `gravidade="alta"` para violência
   contra pessoa, arma ou risco à vida.
3. Crie o agente `Extrator` com `output_type=Ocorrencia` e rode-o nos casos `C1`, `C2` e `C5` de `dados/casos.py`.

**Pronto quando:** `resultado.final_output` é um objeto `Ocorrencia` (não texto), `C2` sai com gravidade `alta` e `C5` sai com `bairro=None`.

**Onde olhar:** `aula2/agente_output.py` (o básico), `aula2/agente_output2.py` (**o mais parecido**: ocorrência, envolvidos, enum de papéis).

---

## Etapa 3: Guardrails de entrada (20 min)

**Tarefa**

Antes do `Extrator`, a entrada passa por **duas** barreiras:

1. **Dado pessoal (LGPD), sem LLM:** uma regex que detecta CPF (`000.000.000-00`) e RG. Achou: bloqueia.
2. **Fora do escopo / manipulação, com LLM:** um agente classificador com `output_type` que devolve uma nota de 0 a 1 de
   "não é um relato de ocorrência ou tenta mudar as regras do sistema" e um motivo. Acima de um `LIMIAR`, bloqueia.

Implemente as duas como `@input_guardrail` presos ao `Extrator`, e trate `InputGuardrailTripwireTriggered`
devolvendo uma mensagem educada ao cidadão.

**Pronto quando:** `C3`, `C4` e `C7` são bloqueados com mensagens diferentes; `C1` e `C2` passam.

**Onde olhar:** `aula2/agente_guardrail.py` (guardrail com agente classificador e limiar),
`exercicios_resolvidos/aula4/ex11_guardrails.py` (regex de RG, guardrail de entrada **e** de saída),
`aula8/exemplos/04_prompt_injection/1_codigo_pronto/` (por que "nunca revele" no prompt não basta).

---

## Etapa 4: Resiliência: data real, retry, idempotência e limites (20 min)

Crie `ferramentas.py` com:

1. **Data real:** injete a data de hoje nas instruções do `Extrator` para que "ontem" e "agora há pouco" virem uma data de verdade.
2. **API externa com retry:** `consultar_clima(latitude, longitude)` na Open-Meteo, com `timeout`, até 3 tentativas e
   **backoff exponencial**. Se todas falharem, devolve `"indisponível"` (o sistema **segue**, não quebra).
   O clima entra no registro final ("chovia no momento do registro").
3. **Protocolo idempotente:** `gerar_protocolo(tipo, bairro, data_fato, resumo)` = os 8 primeiros caracteres de um
   SHA-256 dos campos normalizados. O mesmo relato gera o **mesmo** protocolo.
4. **Limites:** toda chamada de `Runner` passa `max_turns` e roda dentro de `asyncio.wait_for(..., timeout=...)`.
   Trate `MaxTurnsExceeded` e `TimeoutError` separadamente.

**Pronto quando:** com a internet desligada (ou URL errada) o clima vira `"indisponível"` após 3 tentativas visíveis no log;
`gerar_protocolo` devolve o mesmo valor para `C1` e `C8`.

**Onde olhar:** `aula3/agente_retry.py` (injetar a data), `aula3/agente_retry2.py` (**retry com backoff**, erro de negócio x erro
técnico), `aula3/agente_retry3.py` (**idempotência com hash**), `aula3/agente_parada3.py` (timeout x `max_turns`),
`aula6/desafio2/main.py` (`buscar_chuva`, API tolerante a falhas).

---

## Etapa 5: MCP Server da delegacia (35 min)

Tire os dados de dentro do agente e coloque num **MCP Server** seu, `mcp_delegacia.py`, que lê `dados/delegacias.csv` e grava
os registros em `saidas/registros.json` (ou SQLite).

**Tools do server**

| Tool | Tipo | O que faz |
|---|---|---|
| `listar_bairros()` | leitura | os bairros atendidos (para o agente **descobrir** valores válidos, sem adivinhar) |
| `delegacia_competente(bairro, especialidade="geral")` | leitura | a delegacia do bairro (ou a especializada), com `viaturas_disponiveis` |
| `consultar_registro(protocolo)` | leitura | um registro já gravado |
| `registrar_ocorrencia(protocolo, delegacia, tipo, gravidade, texto)` | **escrita** | grava; se o protocolo já existir, **não duplica** e avisa |

**Tarefa**

1. Implemente o server com `MCPServer` e `@mcp.tool()`, com **docstrings e tipos** caprichados.
2. Teste-o **sem agente** no MCP Inspector: `npx @modelcontextprotocol/inspector python mcp_delegacia.py`.
3. Ligue o server ao agente `Atendente` com `MCPServerStdio` e pergunte: "Qual delegacia atende a Asa Sul e quantas viaturas ela tem?".
4. Escreva também uma função `chamar_mcp(tool, argumentos)` (cliente MCP direto, sem agente): ela será usada pelos **nós** do grafo na Etapa 7.

**Pronto quando:** o Inspector lista as 4 tools; o agente responde a pergunta usando o server; registrar `C1` duas vezes gera um único registro.

**Onde olhar:** `aula5/exemplos/03_mcp_parametros/server.py` (tool com parâmetros), `aula5/exemplos/05_multiplas_tools/server.py`
(várias tools, tool de "descoberta"), `aula5/exemplos/04_agente_mcp/agente.py` (`MCPServerStdio`),
`aula6/desafio2/mcp_unidades.py` (**MCP Server lendo CSV, o mais parecido**), `aula6/desafio2/main.py` (`chamar_mcp` dentro de um nó).

---

## Etapa 6: Equipe de especialistas, em fluxo linear (25 min) ⇒ Marco mínimo

**Tarefa**

1. Crie, em `agentes.py`, agentes com **uma responsabilidade cada**:
   - `Juridico`: enquadramento legal provável (tipo penal e artigo), em até 3 linhas;
   - `Investigador`: 2 ou 3 diligências iniciais;
   - `Redator`: redige o registro **usando só os fatos recebidos** (ocorrência, delegacia, clima, pareceres).
2. Crie um `Coordenador` que usa `Juridico` e `Investigador` **como tools** (`as_tool`) e decide se o caso vai para uma
   delegacia **especializada** (violência contra a mulher ou crime cibernético) ou para a geral.
3. Monte `etapa6_linear.py`, um fluxo **em Python puro** (sem LangGraph), que encadeia tudo:
   guardrails → extração → clima → MCP (delegacia) → coordenador → redator → protocolo → MCP (registrar).

**Pronto quando:** `C1` e `C2` chegam a um registro gravado com protocolo, e você consegue dizer **qual agente escreveu cada parte**.

**Onde olhar:** `aula4/ex02_handoff_roteamento.py` (handoff), `aula4/ex03_agente_as_tool.py` (**agentes como tools, o mais parecido**),
`aula2/agente_handoff2.py`, `aula7/exemplos/02_agentes_especializados/main.py` (especialistas com uma responsabilidade),
`aula6/exemplos/01_fluxo_linear/main.py` (o fluxo linear e seus limites).

> **Marco mínimo:** um sistema que, a partir do relato, protege a entrada, extrai, consulta o MCP e registra.
> Se você chegou aqui, já está aprovado. As próximas etapas transformam o "script" em um **sistema**.

---

## Etapa 7: O fluxo como grafo (LangGraph) (45 min)

Reescreva o fluxo da Etapa 6 como o grafo do início deste enunciado, em `grafo.py`. **Reaproveite** as funções e os agentes:
cada nó só chama o que já existe e devolve **o que mudou** no estado.

**Tarefa**

1. Defina o `Estado` (`TypedDict`) com, no mínimo: `relato`, `bloqueado`, `motivo_bloqueio`, `ocorrencia`, `delegacia`,
   `clima`, `parecer_juridico`, `diligencias`, `registro`, `tentativas`, `erro_validacao`, `protocolo`, `caminho`.
   Use um **reducer** (`Annotated[list[str], operator.add]`) para `caminho`, para que cada nó só acrescente o próprio nome.
2. **Arestas condicionais:** `proteger_entrada` (bloqueado/ok), `extrair` (sem_local/ok) e `localizar_delegacia` (sem_viatura/ok).
3. **Paralelismo:** `juridico` e `investigador` rodam no **mesmo passo** (fan-out) e `consolidar` espera os dois (fan-in por lista).
   Cada um escreve **só no seu campo**.
4. **Ciclo com parada:** `validar` (LLM ou regra) aprova o registro se ele citar a **delegacia** e o **tipo**, e não contiver
   CPF. Se não, volta a `redigir_registro` com o motivo. Máximo de **3 tentativas**, contadas no estado. Use também `recursion_limit`.
5. Imprima o `caminho` no fim e gere o diagrama com `app.get_graph().draw_mermaid()` (cole em mermaid.live e salve a imagem).

**Pronto quando:** rodando `C1`, `C2`, `C3`, `C5` e `C6`, cada um percorre o caminho esperado em `dados/casos.py`, e no log
`juridico` e `investigador` aparecem no mesmo passo.

**Onde olhar:** `aula6/exemplos/05_multiplos_nos/main.py` (nós devolvem só o que mudou), `aula6/exemplos/06_fluxo_condicional/main.py`,
`aula6/exemplos/07_dag/main.py` (ramifica e converge), `aula6/exemplos/08_fluxo_ciclico/main.py` (**ciclo com parada**),
`aula6/exemplos/10_agente_completo/main.py`, `aula6/exemplos/11_grafo_real/main.py` (nós de LLM, MCP, API e tool),
`aula6/desafio2/main.py` (**o mais parecido**: despacho com LLM + MCP + API + ciclo),
`aula7/exemplos/08_paralelismo/main.py` (**fan-out/fan-in**), `aula8/exemplos/10_agentes_e_grafo/1_codigo_pronto/main.py`
(agente decide, grafo controla), `aula6/exemplos/04_langgraph_basico/main.py` (`draw_mermaid`).

---

## Etapa 8: Persistência e aprovação humana (30 min)

**Tarefa**

1. Compile o grafo com um **checkpointer SQLite** (`saidas/checkpoints.db`) e use um `thread_id` por relato.
2. Crie o nó `aprovacao_humana`, que só roda quando a gravidade é **alta**. Ele chama `interrupt()` com um **resumo** para o
   humano (tipo, delegacia, registro proposto) e recebe `{"aprovado": bool, "motivo": str}`.
3. **Aprovado** → `registrar`. **Rejeitado** → volta a `redigir_registro` com o motivo como feedback (máximo de **2 rejeições**;
   depois disso, encerra como "não registrado").
4. Faça o script aceitar `--retomar <thread_id> sim` e `--retomar <thread_id> "nao:motivo"`, para que **outro processo** retome
   a execução pausada.
5. **Regra de ouro:** nada com efeito colateral (gravar, publicar) **antes** do `interrupt()`: o nó roda de novo na retomada.

**Pronto quando:** `C2` pausa e o processo **termina**; um segundo comando retoma e registra; `C1` registra sem pausar;
`get_state(config).next` mostra onde cada execução parou.

**Onde olhar:** `aula7/exemplos/04_persistencia/main.py` (checkpoint, `thread_id`, retomar em outro processo),
`aula7/exemplos/06_human_in_the_loop/main.py` (`interrupt()` e `Command(resume=...)`),
`aula7/exemplos/07_aprovacao_revisao/main.py` (**o mais parecido**: rejeição com feedback e limite de tentativas),
`aula3/agente_human.py` (a versão com `needs_approval` do Agents SDK, para comparar).

---

## Etapa 9: Segurança: privilégio mínimo, token e auditoria (25 min) ⇒ Marco completo

**Tarefa**

1. **Privilégio mínimo:** nenhum **agente** recebe a tool `registrar_ocorrencia`. Os especialistas só têm tools de leitura
   (ou nenhuma). Quem grava é o **nó** `registrar` do grafo, e só depois da aprovação.
2. **Autorização no server:** `registrar_ocorrencia` exige o `TOKEN_REGISTRO` (lido do ambiente pelo **server**). Sem token
   válido, o **server** nega, não o agente. Valide também `gravidade` contra um conjunto fechado de valores.
3. **Auditoria:** toda tentativa de escrita, **permitida ou negada**, vira uma linha em `saidas/auditoria.jsonl` com: quando,
   `thread_id`, quem pediu, tool, protocolo, decisão (`ALLOW`/`DENY`) e motivo.
4. **Guardrail de saída:** antes de gravar, confira que o registro não contém CPF e cita a delegacia. Se falhar, não grava.
5. Rode `C7` com o guardrail de entrada **desligado** e mostre que, mesmo assim, nada é alterado e a auditoria registra `DENY`.

**Pronto quando:** `saidas/auditoria.jsonl` tem linhas `ALLOW` (C1, C2) e `DENY` (C7, ou uma chamada sem token feita por você no Inspector).

**Onde olhar:** `aula5/exemplos/10_seguranca/server_seguro.py` (**o mais parecido**: token de supervisor, enum, auditoria no server),
`aula5/exemplos/10_seguranca/agente_seguranca.py` (os 4 cenários de teste), `aula8/exemplos/06_excessive_agency/1_codigo_pronto/main.py`
(o problema de dar tools demais), `aula8/exemplos/08_auditoria/1_codigo_pronto/main.py` (log estruturado),
`aula8/exemplos/05_guardrail_saida/1_codigo_pronto/main.py` (guardrail de saída).

> **Marco completo:** grafo com decisões, paralelismo, ciclo, aprovação humana persistida e escrita protegida e auditada.

---

## Etapa 10: Observabilidade (15 min)

**Tarefa**

1. Crie um `RunHooks` que registra, para cada agente: início, cada tool chamada (com argumentos) e o resultado.
2. Para cada **nó** do grafo, meça o tempo e, quando houver agente, os **tokens** (`resultado.context_wrapper.usage`).
   Grave uma linha por nó em `saidas/metricas.jsonl`, com o mesmo `thread_id` da auditoria.
3. No fim de cada execução, imprima um resumo: nós percorridos, tempo total, nó mais lento, tokens totais.

**Pronto quando:** você responde, para `C2`, **onde o tempo foi gasto** e **quantos tokens** custou, só olhando os arquivos.

**Onde olhar:** `aula3/agente_hook2.py` e `aula3/agente_hook3.py` (`RunHooks`), `aula5/exemplos/11_observabilidade/agente_observavel.py`
(ler `result.new_items`), `aula8/exemplos/03_observabilidade/1_codigo_pronto/` (traces e métricas; Langfuse/Prometheus são **opcionais**).

---

## Etapa 11: Demonstração e entrega (25 min)

1. Rode os **8 casos** de `dados/casos.py` e preencha, no `ENTREGA.md`, uma tabela:
   caso | caminho percorrido | resultado (bloqueado / pediu local / escalado / pausou / registrado + protocolo) | bateu com o esperado?
2. Cole o diagrama Mermaid do seu grafo.
3. Responda, em até 3 linhas cada:
   - Quem decide o caminho no seu sistema: o LLM, o grafo ou as regras? Dê um exemplo de cada.
   - Se o guardrail de entrada falhar, o que ainda protege o cadastro?
   - Por que o nó de aprovação não pode gravar nada antes do `interrupt()`?
   - Qual etapa foi feita com **MCP** e qual com **tool local**? Por que essa escolha?
   - O que você mudaria para colocar este sistema em produção?
4. Faça commit do código (sem o `.env`!) e entregue o link ou o `.zip`.

---

## Critérios de avaliação (100 pontos)

| Etapa | Pontos | O que conta |
|---|---|---|
| 1 a 2 | 10 | agente com tool; saída Pydantic com enum e descrições |
| 3 | 10 | dois guardrails distintos (regex e LLM), bloqueios com mensagens claras |
| 4 | 10 | retry com backoff, falha tolerada, protocolo idempotente, limites de execução |
| 5 | 15 | MCP Server com 4 tools bem descritas, testado no Inspector e usado por um agente |
| 6 | 10 | especialistas com uma responsabilidade cada; coordenador com `as_tool` |
| 7 | 15 | grafo com 3 decisões, fan-out/fan-in, ciclo com parada e `caminho` correto |
| 8 | 10 | checkpoint, `interrupt()`, retomada em outro processo, limite de rejeições |
| 9 | 10 | privilégio mínimo, token no server, auditoria ALLOW/DENY, guardrail de saída |
| 10 a 11 | 10 | métricas por nó, 8 casos demonstrados, respostas de reflexão |

**Faixas:** até a Etapa 6 (Marco mínimo) ≈ 55 pontos; até a Etapa 9 (Marco completo) ≈ 90; o resto, Etapas 10–11 e bônus.

## Bônus (para quem terminar antes; até +10 pontos, sem passar de 100)

| Bônus | Onde olhar |
|---|---|
| Publicar `ocorrencia/registrada` via **MQTT** e um assinante que conta ocorrências por bairro | `aula4/ex04_mqtt_pub.py`, `aula4/ex06_mqtt_estatistica.py` |
| Expor o sistema com **FastAPI**: `POST /ocorrencias` e `POST /ocorrencias/{thread_id}/aprovacao` | `aula2/main.py` |
| Subir o MCP Server via **HTTP com token Bearer** em vez de stdio | `aula5/exemplos/14_mcp_http_basico/`, `aula5/exemplos/16_mcp_http_autenticado/` |
| Trocar a decisão de gravidade por um decisor **tipado com confiança** (JEV), pedindo esclarecimento quando a confiança for baixa | `aula6/desafio3/` |
| Mensagens entre agentes no formato **FIPA-ACL** ou disputa de viaturas por **Contract Net** | `aula4/ex08_fipa_acl.py`, `exercicios_resolvidos/aula4/ex12_cnp_coordenador.py` |
| **Memória** entre relatos do mesmo cidadão (`SQLiteSession`): "e aquele assalto de ontem?" | `aula2/agente_memoria.py`, `aula2/agente_sessao2.py` |

## Regras

- Use **dados fictícios**. Nunca coloque CPF, nomes ou endereços reais nos testes.
- A chave da API fica **só** no `.env`, que não vai para o git.
- Como o LLM varia, **compare estado e caminho, não texto**: "foi bloqueado?", "pausou?", "gerou protocolo?".
- Pode consultar todo o material das aulas, a documentação oficial e os colegas. Explique no `ENTREGA.md` o que veio de onde.
