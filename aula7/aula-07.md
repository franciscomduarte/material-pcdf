# Aula 7 — Material teórico

Perguntas e respostas que acompanham os exemplos. Cenário: análise de uma denúncia sobre o
Pregão 045/2026 (dados fictícios). Como rodar: [`README.md`](README.md).

---

## Bloco 1 — Por que uma equipe de agentes? (exemplos 01 e 02)

**Qual o problema de um agente que faz tudo?**
Ele responde de forma rasa e **opaca**: no exemplo 01 a resposta única mistura investigação,
enquadramento jurídico, risco e recomendação. Não dá para saber onde termina cada etapa, quem
errou, nem testar uma etapa isoladamente.

**O que muda com especialistas?**
Cada agente faz **uma** coisa (Investigador → fatos; Jurídico → enquadramento; Analista → risco e
recomendação), com um prompt curto e focado. Ganhos: saídas auditáveis por etapa, ferramentas
diferentes por especialista (MCP da Aula 5), e troca de um especialista sem mexer nos outros.

**Então sempre é melhor dividir?**
Não. Cada agente a mais é mais uma chamada de LLM (custo, latência) e mais um ponto de falha.
Divida quando as etapas têm **responsabilidades, ferramentas ou critérios de qualidade diferentes**.

## Bloco 2 — Estado compartilhado (exemplo 03)

**Estado x memória?**

| | Estado | Memória |
|---|---|---|
| O que é | o que a execução **atual** precisa (`solicitacao`, `investigacao`, ...) | o que sobrevive **entre** execuções (histórico de análises) |
| Vida | nasce e morre com a execução | permanece |
| Analogia | caderno de rascunho | arquivo do órgão |

**Quem escreve o quê?**
Cada especialista escreve **apenas os seus campos** e lê os anteriores. Ninguém chama ninguém, e
nenhuma string é passada "à mão": o estado é o contrato entre os agentes.

## Bloco 3 — Persistência (exemplo 04)

**Por que persistir?**
Estado só em memória morre com o processo. Um processo que espera um humano por horas (ou que
cai no meio) precisa poder **continuar de onde parou**.

**Como o LangGraph faz?**
Um **checkpointer** (`SqliteSaver`) grava uma "foto" do estado a cada passo. Cada execução tem um
`thread_id`; mesma id = mesma execução. `app.get_state(config)` mostra o estado salvo e o `next`
(próximo nó). Como a foto está num arquivo, dá para retomar **em outro processo**.

**Checkpoint é o mesmo que memória?**
Não. Checkpoint é o estado **de uma execução**, para retomá-la. Memória é conhecimento que se
quer reaproveitar em execuções **diferentes**.

## Bloco 4 — Equipe como grafo (exemplo 05)

**Quem é o orquestrador?**
Quem decide a **ordem** e as **condições de passagem** entre especialistas. Aqui é o próprio
grafo (mais um nó que prepara o estado): a ordem é explícita e inspecionável. A alternativa é um
LLM escolher o próximo especialista: troca-se **controle** por **flexibilidade**. Em processos
com risco (como este), prefira o controle no grafo.

**O que dá para rodar em paralelo? (exemplo 08)**
Especialistas **independentes** (Jurídico e Risco dependem só dos fatos). No grafo: dois `add_edge`
saindo do mesmo nó (fan-out) e `add_edge([a, b], "consolidar")` para esperar todos (fan-in). O tempo
cai de "soma" para "o maior". Regras: ramos paralelos escrevem em **campos diferentes** (senão
`InvalidUpdateError`, salvo com *reducer*) e a **ordem** dos logs entre eles não é garantida. Se um
especialista precisa da saída do outro, volta a fila.

## Bloco 5 — Human-in-the-loop (exemplo 06)

**Por que um humano no meio?**
Porque algumas decisões têm consequência que o sistema não deve assumir sozinho (suspender um
contrato, acusar alguém). O humano entra **antes** de a recomendação valer.

**Por que `input()` não basta?**
Bloqueia o processo, perde tudo se o terminal fechar, e não há como o humano responder depois.

**Como o LangGraph resolve?**

```
invoke() → executa → interrupt() → checkpoint salvo → invoke() RETORNA com "__interrupt__"
   ...horas depois, até em outro processo...
invoke(Command(resume=resposta), config) → carrega o checkpoint → continua
```

**`interrupt_before` x `interrupt()`?**
`interrupt_before=["no"]` é **estático**: sempre para antes daquele nó, sem pergunta. `interrupt()`
é **dinâmico**: para **dentro** do nó, pode ser condicional e carrega uma pergunta e uma resposta.

**Pegadinha:** ao retomar, o nó que chamou `interrupt()` roda **de novo desde o início**. Nada
com efeito colateral antes dele.

## Bloco 6 — Aprovação e revisão (exemplo 07)

**O que a rejeição muda?**
No 06, rejeitar encerrava tudo. No 07 o humano dá **feedback**, o Analista refaz a recomendação
lendo `feedback_humano`, e o humano avalia de novo: um **ciclo** (Aula 6) com humano dentro.

**Como garantir que termina?**
Condição de parada lida do **estado**: `tentativas >= MAX_TENTATIVAS` leva a `encerrar_sem_aprovacao`
(encaminhar a um responsável). Nunca conte com o humano aprovar um dia.

**Erro técnico x rejeição humana?**

| | Erro técnico | Rejeição humana |
|---|---|---|
| Exemplo | a API do jurídico caiu | o revisor achou a recomendação vaga |
| Natureza | falha do **sistema** | decisão do **processo** |
| O que fazer | **retomar**: `invoke(None, config)` | **revisar**: volta ao analista com feedback |
| Conta tentativa? | não | sim |

## Fechamento

```
ESPECIALISTAS  →  ESTADO COMPARTILHADO  →  CHECKPOINT (SQLite)  →  HUMANO NO PONTO CRÍTICO
   (quem faz)        (o que circula)          (retomar)               (quem decide)
```

Agentes autônomos onde o risco é baixo; **humano no circuito onde o risco é alto**. Isso é o que
torna um sistema de agentes utilizável em processos reais.
