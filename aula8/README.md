# Aula 9 — Auto-scaling, Observabilidade e Segurança

Laboratório didático para mostrar, com agentes de IA reais, como **observar**, **medir**, **proteger**, **autorizar**, **auditar**, **orquestrar** e **escalar**.

```text
FUNCIONA → OBSERVAMOS → MEDIMOS → PROTEGEMOS → AUTORIZAMOS → AUDITAMOS → ORQUESTRAMOS → ESCALAMOS
```

> Todos os exemplos usam **modelo real** (OpenAI ou Ollama). Não existe modelo de mentira. Como os modelos variam, os testes comparam **estado** (bloqueado, negado, cadastro intacto), nunca o texto da resposta.

## Arquitetura

```text
                       AGENT (OpenAI Agents SDK)
                               │
        ┌──────────────────────┼─────────────────────────┐
        ▼                      ▼                         ▼
  Guardrails (NeMo)     Tools + OPA (ALLOW/DENY)    OpenTelemetry
  entrada e saída       + aprovação humana              │
                               │                ┌───────┴────────┐
                               ▼                ▼                ▼
                          Auditoria          Langfuse        Prometheus
                        (log estruturado)   (traces LLM)         │
                                                                 ▼
                                                              Grafana
                  LangGraph controla o fluxo entre as etapas
```

| Conceito          | Ferramenta                         |
| ----------------- | ---------------------------------- |
| Agent             | OpenAI Agents SDK                  |
| Graph             | LangGraph                          |
| LLM               | OpenAI / Ollama                    |
| Tracing           | OpenTelemetry                      |
| LLM Observability | Langfuse                           |
| Metrics           | Prometheus                         |
| Dashboard         | Grafana                            |
| Guardrails        | NeMo Guardrails                    |
| Authorization     | OPA                                |
| Audit             | Logs estruturados (JSON) + trace_id |

**Agent SDK x LangGraph.** O Agent SDK constrói e executa agentes. O LangGraph descreve o fluxo entre etapas. O agente decide e atua; o grafo controla.

### Quem faz o quê na observabilidade

| Ferramenta    | Papel                                                        |
| ------------- | ------------------------------------------------------------ |
| OpenTelemetry | Instrumentação e padrão de telemetria. Não guarda nem mostra. |
| Langfuse      | Observabilidade especializada em LLM: tokens, custo, entrada e saída, sessões. |
| Prometheus    | Métricas numéricas ao longo do tempo (séries temporais).      |
| Grafana       | Visualização e dashboards.                                    |

**Trace** responde "como aconteceu *esta* execução?". **Métrica** responde "quantas vezes aconteceu?". **Log** responde "o que aconteceu neste evento?". O vocabulário completo está no painel do professor.

> **O LLM decide o que gostaria de fazer; a política decide o que ele pode fazer.**
> Excessive Agency não é somente um problema de prompt. É um problema de arquitetura e autorização.

## Pré-requisitos

- **Python 3.10** (aceita 3.10 a 3.13). **Evite 3.11.0**: o `openai-agents` não importa nele (bug do `typing`, corrigido na 3.11.1). O `nemoguardrails` exige Python menor que 3.14.
- **Docker Desktop** (Prometheus, Grafana e OPA).
- **Chave da OpenAI** ou **Ollama** com o modelo `llama3.1`.
- **Conta no Langfuse Cloud** (grátis), a partir do exemplo 03 (passo 2).

## Instalação (PowerShell, dentro de `aula8/`)

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env        # depois edite o .env
python verificar_ambiente.py  # confere tudo
```

### Escolher o modelo (`.env`)

```env
PROVIDER=openai               # ou: ollama
OPENAI_API_KEY=sk-...         # só para openai
OPENAI_DEFAULT_MODEL=gpt-4o-mini
OLLAMA_MODEL=llama3.1         # só para ollama (ollama pull llama3.1)
```

`PROVIDER=openai` usa a OpenAI. `PROVIDER=ollama` usa o Ollama local. Trocar é mudar **uma linha**: os exemplos chamam `configurar()` (`base/provedor.py`) e os guardrails usam `carregar_rails()` (`base/guardrails.py`), que seguem o mesmo `PROVIDER`.

### Langfuse (use o Cloud)

O Langfuse local exige Postgres, ClickHouse, Redis e MinIO; por isso usamos a nuvem.

1. Crie a conta em <https://cloud.langfuse.com> e **escolha a região** (ela define o endereço).
2. Crie um projeto e, em **Settings > API Keys**, uma chave. A secreta aparece uma vez só.
3. Preencha no `.env`: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` e `LANGFUSE_HOST` (Europa: `https://cloud.langfuse.com`; EUA: `https://us.cloud.langfuse.com`).
4. `python verificar_ambiente.py --sem-llm` deve mostrar `[OK] credenciais aceitas`. Erro 401 quase sempre é região errada.

### Infraestrutura (Prometheus, Grafana, OPA)

```powershell
cd docker
docker compose up -d      # sobe
docker compose ps         # confere
docker compose down       # derruba
cd ..
```

| Serviço    | Endereço                | Observação                                  |
| ---------- | ----------------------- | ------------------------------------------- |
| Prometheus | <http://localhost:9090> | busca o `/metrics` do agente a cada 5 s      |
| Grafana    | <http://localhost:3000> | `admin` / `admin`; já ligado ao Prometheus   |
| OPA        | <http://localhost:8181> | depois de editar o `.rego`: `docker compose restart opa` |

O alvo `agente` do Prometheus só fica **UP** enquanto um programa com métricas está rodando (passo 3 e exemplo 11).

## Ordem da demonstração em sala

| # | Etapa | Onde | Comando |
| - | ----- | ---- | ------- |
| 1 | Agent básico | `exemplos/01_agente_basico` | `python exemplos/01_agente_basico/main.py` |
| 2 | Agent + Tool | `exemplos/02_agente_tool` | `python exemplos/02_agente_tool/main.py` |
| 3 | Trace | `exemplos/03_observabilidade` passo 1 | `python exemplos/03_observabilidade/2_solucao/passo1_trace.py` |
| 4 | Langfuse | `exemplos/03_observabilidade` passo 2 | `python exemplos/03_observabilidade/2_solucao/passo2_langfuse.py` |
| 5 | Métricas | `exemplos/03_observabilidade` passo 3 | `python exemplos/03_observabilidade/2_solucao/passo3_metricas.py` |
| 6 | Grafana | `docker/grafana/dashboard-reserva/aula9-agente.json` | painel pela interface (veja o painel do professor) |
| 7 | Prompt injection | `exemplos/04_prompt_injection` | `python exemplos/04_prompt_injection/2_solucao/passo2_agente_protegido.py` |
| 8 | Guardrails de saída | `exemplos/05_guardrail_saida` | `python exemplos/05_guardrail_saida/2_solucao/passo2_corrige.py` |
| 9 | Excessive agency | `exemplos/06_excessive_agency` | `python exemplos/06_excessive_agency/2_solucao/passo1_privilegio_minimo.py` |
| 10 | OPA | `exemplos/07_opa` | `python exemplos/07_opa/2_solucao/passo3_aprovacao_humana.py` |
| 11 | Auditoria | `exemplos/08_auditoria` | `python exemplos/08_auditoria/2_solucao/passo1_registrar.py` |
| 12 | LangGraph | `exemplos/09_langgraph` e `10_agentes_e_grafo` | `python exemplos/10_agentes_e_grafo/2_solucao/passo1_grafo_agentes.py` |
| 13 | Integração final | `exemplos/11_integracao` | `python exemplos/11_integracao/2_solucao/agent_seguro.py` |
| 14 | Auto-scaling | [`docs/auto_scaling.md`](docs/auto_scaling.md) | (conceitual) |

## Formato de cada exemplo

Cada pasta `exemplos/NN_*` tem:

- `1_codigo_pronto/`: código que **já roda com IA real** e mostra um problema. É o que se entrega aos alunos.
- `2_solucao/`: os degraus que o professor constrói ao vivo (cada um roda). **Só local**: não distribua.

## Os exemplos

Para cada exemplo: objetivo, conceito, comando, resultado esperado, explicação e pergunta para a turma.

### 01 e 02: agente e tool
- **Objetivo**: validar a instalação e mostrar que o agente decide quando chamar a tool `consultar_temperatura`.
- **Conceito**: `Agent` + `Runner` (+ tool).
- **Esperado**: uma resposta de uma frase; no 02, a pergunta de temperatura chama a tool e "2 + 2" não (o Ollama às vezes chama a tool mesmo assim).
- **Pergunta**: quem decidiu chamar a tool, o código ou o modelo?

### 03: traces, Langfuse e métricas
- **Objetivo**: ver o que acontece dentro de cada pergunta e medir o conjunto.
- **Conceito**: trace, span, atributos, exportador, métricas (counter e histogram), scrape.
- **Esperado**: árvore de spans no console; traces e custo no Langfuse; `agent_requests_total` e outras no Prometheus.
- **Pergunta**: onde o tempo foi gasto, no modelo ou na tool?

### 04: prompt injection e guardrail de entrada
- **Objetivo**: mostrar que "nunca revele" no prompt não basta e proteger com um filtro antes do agente.
- **Conceito**: guardrail de entrada (NeMo, `self check input`).
- **Esperado**: no código pronto o segredo pode vazar (varia por modelo); com o filtro os ataques são bloqueados e a pergunta normal passa.
- **Pergunta**: por que o prompt sozinho não protege?

### 05: guardrail de saída
- **Objetivo**: impedir que respostas inválidas cheguem a quem consome o JSON.
- **Conceito**: guardrail de saída (regra em Python), bloquear e tentar de novo.
- **Esperado**: formato e cidade conferidos; respostas inválidas viram uma mensagem segura.
- **Pergunta**: JSON válido quer dizer resposta correta?

### 06: excessive agency e privilégio mínimo
- **Objetivo**: mostrar o risco de dar tools demais e corrigir com privilégio mínimo.
- **Conceito**: least privilege.
- **Esperado**: no código pronto o agente de consulta exclui um usuário; com privilégio mínimo ninguém exclui.
- **Pergunta**: o agente errou, ou a arquitetura?

### 07: OPA (política)
- **Objetivo**: tirar a regra de dentro do código e exigir aprovação humana para excluir.
- **Conceito**: política como dado (`policy.rego`), ALLOW/DENY, fail-closed, human-in-the-loop.
- **Esperado**: investigador só consulta; administrador consulta e atualiza; excluir só com aprovação humana.
- **Pergunta**: o que acontece se o OPA ficar fora do ar? (nega)

### 08: auditoria
- **Objetivo**: poder responder, depois, quem fez o quê.
- **Conceito**: log estruturado com `trace_id`; ALLOW e DENY registrados.
- **Esperado**: `saidas/auditoria.jsonl` com quem, quando, agente, ação, tool, recurso, autorização, resultado e trace.
- **Pergunta**: se o modelo disser "apaguei" e o log disser DENY, em quem você confia?

### 09 e 10: LangGraph
- **Objetivo**: tornar o fluxo explícito e colocar agentes dentro dele.
- **Conceito**: estado, nó, aresta, aresta condicional; agente decide, grafo controla.
- **Esperado**: o `[caminho]` de cada pergunta (`triador -> consulta`) e o diagrama Mermaid.
- **Pergunta**: quem decidiu o ramo, o grafo ou o agente?

### 11: integração final
- **Objetivo**: juntar tudo em um agente protegido, observável e auditável.
- **Esperado**: caminho `entrada -> agente -> saida`; ataque bloqueado na entrada; exclusão só com aprovação; rastro em auditoria, Langfuse e Prometheus.
- **Pergunta**: se o filtro de entrada falhar, o que ainda protege o cadastro?

## Estrutura das pastas

```text
aula8/
├── base/             provedor.py (OpenAI/Ollama), guardrails.py (NeMo)
├── observabilidade/  tracing.py, metricas.py  (módulos finais, montados nos passos 1 a 3)
├── seguranca/        opa.py, auditoria.py     (módulos finais, montados nos passos 8 e 9)
├── exemplos/         01 a 11, cada um com 1_codigo_pronto e 2_solucao
├── docker/           docker-compose.yml, prometheus.yml, grafana/, opa/policy.rego
├── testes/           test_guardrails.py, test_opa_auditoria.py, test_integracao.py
├── saidas/           auditoria.jsonl (gerado), grafo_09.mmd
├── docs/             auto_scaling.md
├── _painel/          gerador do painel do professor (só local)
├── verificar_ambiente.py, requirements.txt, .env.example, CHECKLIST_FINAL.md
```

Esta estrutura difere do esboço original (`common/`, `config/`, pastas numeradas por tema) para seguir o formato "código pronto + escada" usado no curso.

## Testes

```powershell
python -m pytest -m "not llm"     # sem chamar modelo (precisa do OPA no ar para os de OPA)
python -m pytest                  # todos (os marcados llm chamam o modelo real)
```

| Arquivo | O que prova |
| ------- | ----------- |
| `test_guardrails.py` | `BLOCKED` para ataques, `PASSED` para perguntas normais, saída válida passa e inválida é bloqueada |
| `test_opa_auditoria.py` | `ALLOW` e `DENY` do OPA, fail-closed, auditoria de DENY e ALLOW |
| `test_integracao.py` | ponta a ponta: ataque bloqueado na entrada, tool negada, tool permitida, exclusão exige aprovação, saída com segredo bloqueada |

Sem o OPA no ar, os testes que dependem dele **falham** dizendo para subir o Docker (não passam por engano).

## Checklist de segurança

| Item | No laboratório |
| ---- | -------------- |
| [x] Input validation | guardrail de entrada (exemplo 04) |
| [x] Prompt injection detection | `self check input` (exemplos 04 e 11) |
| [x] Output validation | guardrail de saída (exemplos 05 e 11) |
| [x] Tool permissions | tools por papel e política (exemplos 06 e 07) |
| [x] Least privilege | exemplo 06 |
| [x] Human approval | exclusão com aprovação (exemplos 07 e 11) |
| [x] Policy enforcement | OPA (exemplos 07 e 11) |
| [x] Audit logging | `auditoria.jsonl` (exemplos 08 e 11) |
| [~] Secrets management | `.env` fora do Git; em produção usar um cofre de segredos |
| [ ] Rate limiting | só conceitual ([auto-scaling](docs/auto_scaling.md)) |
| [x] Observability | traces, métricas e dashboards (exemplos 03 e 11) |
| [~] Error handling | agente que falha vira resposta segura e conta em `agent_errors_total`; não é tratamento completo |

## Onde entrariam outras ferramentas (não instaladas)

| Ferramenta | Onde ocuparia lugar |
| ---------- | ------------------- |
| Lakera, Azure Prompt Shields | filtro de entrada contra prompt injection, no lugar do `self check input` |
| Guardrails AI | validação de saída (formato e conteúdo), no lugar da regra em Python |
| AWS Bedrock Guardrails | filtros de entrada e saída gerenciados, quando o modelo roda no Bedrock |
| Cedar | política de autorização, no lugar do Rego do OPA |

## Auto-scaling

Conceitual: [`docs/auto_scaling.md`](docs/auto_scaling.md) (escala horizontal, balanceador, health checks, fila, rate limit, backpressure, gatilhos por métrica, Docker, Kubernetes e HPA). Nada disso foi executado no laboratório.

## Limitações conhecidas

- O exemplo guarda o cadastro **em memória**: serve para a aula, não para várias cópias do agente.
- Os guardrails baseados em modelo (entrada) custam tokens e podem errar nos dois sentidos. Medimos o filtro do exemplo 11 (cada frase 3 vezes): com a **OpenAI** (gpt-4o-mini) houve 0 falsos positivos e 0 ataques passando em 42+24 e em 30+18 frases (pedidos normais + ataques; o segundo conjunto era inédito). Com o **Ollama** (llama3.1) houve 5 de 42 pedidos normais barrados e 2 de 24 ataques passando; no conjunto inédito, 0 de 30 barrados e 4 de 18 ataques passando. Um modelo local pequeno como juiz é menos confiável: por isso o OPA e a aprovação humana existem como camadas independentes.
- Os testes `llm` de integração tentam até 3 frases equivalentes para um pedido legítimo, porque o filtro pode barrar uma delas por engano; falham se barrar todas.
- O prompt do `self check input` pede a resposta em inglês ("Yes"/"No"): em português o NeMo bloqueia tudo.
- O OPA não recarrega sozinho ao salvar o `.rego` no Docker do Windows: use `docker compose restart opa`.
- O Ollama (`llama3.1`) é mais lento e às vezes chama tools sem necessidade ou escreve JSON em vez de responder; os exemplos foram escritos para tolerar isso.
- A região do Langfuse precisa bater com a das chaves.
- O Langfuse mostra o custo só quando reconhece o nome do modelo (`gpt-4o-mini`).
