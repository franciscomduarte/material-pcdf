# Enunciado — Desafio 3: decisões tipadas com o JEV

## O problema

No desafio 1, o LLM **decidia** o caminho: você pedia "responda com UMA palavra" e depois interpretava o texto. Isso funciona, mas
tem três problemas: o texto livre precisa ser interpretado, a resposta não diz **quão seguro** o modelo está, e o modelo
que escreve bem não é necessariamente o melhor para decidir.

Neste desafio você usa o **JEV** ([jev-ai.pro](https://jev-ai.pro/)), um modelo que **não escreve texto**: ele responde **perguntas
sobre um texto** com **números** (probabilidades) e com a **confiança** da resposta. O grafo usa esses números para
escolher entre 5 caminhos. A regra de ouro do desafio:

> **LLM para ESCREVER, JEV para DECIDIR.**

## O que é o JEV (o que você precisa saber)

O JEV recebe um **texto** e um **conjunto de perguntas** e devolve uma resposta **tipada** para cada pergunta. Várias perguntas vão em
**uma única chamada**. Usamos dois tipos:

| Tipo | Pergunta de exemplo | O que o JEV devolve |
|---|---|---|
| `noul` (sim/não) | "A pessoa pede atendimento imediato?" | um número de 0 a 1: a **probabilidade** de "sim" (`0.98`) |
| `choice` (escolha) | "Qual é o assunto?" (opções: segunda via, passaporte, horário, outro) | a **opção escolhida**, a probabilidade de cada uma e a **confiança** (`confidence`, de 0 a 1) |

Exemplo (o que o grafo recebe para *"Estou sem medicação e passando mal, preciso de atendimento agora"*):

```json
{"urgente":  {"type": "noul",   "noul": 0.98},
 "sensivel": {"type": "noul",   "noul": 0.02},
 "assunto":  {"type": "choice", "choice": "outro", "confidence": 1.0, "probabilities": {"outro": 1.0, "...": 0.0}}}
```

## O que o sistema deve fazer

1. **Receber** a solicitação e preparar o estado.
2. **Avaliar** (nó do **JEV**): uma única chamada com 3 perguntas: *é urgente?* (`noul`), *contém dado sensível (CPF, senha, cartão)?* (`noul`)
   e *qual o assunto?* (`choice`). O nó guarda **os números** no estado (`p_urgente`, `p_sensivel`, `assunto`, `confianca`).
3. **Decidir pelos números** (um **roteador**, que só lê o estado), nesta **ordem de prioridade**:

   | Ordem | Regra | Caminho |
   |---|---|---|
   | 1º | `p_urgente >= LIMIAR_URGENTE` (0,8) | **urgente**: encaminha ao plantão e o LLM redige a resposta |
   | 2º | `p_sensivel >= LIMIAR_SENSIVEL` (0,8) | **dado sensível**: recusa, alerta e **encerra** (o texto nem chega ao LLM) |
   | 3º | `confianca < LIMIAR_CONFIANCA` (0,6) | **incerto**: em vez de adivinhar, **pede esclarecimento** e encerra |
   | 4º | o assunto está na base | **com base**: pesquisa o procedimento e o LLM redige a resposta |
   | 5º | o assunto é "outro" | **sem base**: o LLM admite que não sabe (sem inventar) |

```
START → receber → avaliar (JEV) ─┬─ urgente  ──→ encaminhar ──→ responder (LLM) ──→ END
                                 ├─ sensivel ──→ alertar_dado_sensivel ───────────→ END
                                 ├─ incerto  ──→ pedir_esclarecimento ────────────→ END
                                 ├─ com_base ──→ pesquisar ──→ responder (LLM) ───→ END
                                 └─ sem_base ──────────────→ responder (LLM) ──────→ END
```

## Entrada e saída

- **Entrada:** o texto da solicitação.
- **Saída:** o estado final, com a `resposta` ao usuário, e o **caminho percorrido**.

## O que já vem pronto (`main.py` e `jev.py`)

O estado, os **limiares**, as `PERGUNTAS_JEV`, a base, a tool `encaminhar_plantao`, o prompt do `responder` e o `executar()`. E o **cliente do JEV**
(`jev.py`): `JevReal` (chama a API) e `JevMock` (decide por palavras-chave, para os testes).

## Regras que o seu grafo precisa respeitar

1. **Quem decide é o roteador, pelos números.** O JEV só dá os números; a regra "o que fazer com 0,98?" é do **grafo** (e dos limiares).
2. **A ordem das regras é a prioridade.** Um texto pode ser urgente **e** conter dado sensível: o risco vem primeiro.
3. **Incerteza é um caminho do grafo.** Com confiança baixa, o grafo **não adivinha**: pergunta.
4. **Sem base, sem invenção.** O assunto "outro" não está na base: o grafo admite que não sabe.
5. **O dado sensível não vai para o LLM.** O nó `alertar_dado_sensivel` encerra o caso antes de qualquer geração de texto.
6. Um nó devolve **só o que mudou**; o roteador só **lê** o estado e devolve um rótulo. Todos os campos são inicializados em `receber`.

## Casos de aceitação (com o JevMock; o JEV real dá os mesmos caminhos)

| Pergunta | Caminho |
|---|---|
| *Estou sem medicação e passando mal, preciso de atendimento agora* | `receber → avaliar → encaminhar → responder` |
| *Meu CPF é 123.456.789-00 e a senha do portal é abc123...* | `receber → avaliar → alertar_dado_sensivel` |
| *Quero o passaporte, ou melhor, a segunda via do documento, não sei qual* | `receber → avaliar → pedir_esclarecimento` |
| *Preciso saber como solicitar uma segunda via de um documento* | `receber → avaliar → pesquisar → responder` |
| *Qual o prazo de restituição do imposto de renda de 2031?* | `receber → avaliar → responder` |

## Como fazer

Você escreve os **nós**, o **roteador** e a **montagem**, em **6 pontos de controle** (funções primeiro, depois a ligação). Confira cada ponto:

```powershell
python desafio3\conferir.py
```

Os testes usam o `JevMock`: **não gastam créditos**. Veja o [`README.md`](README.md) para o passo a passo.

## Você terminou quando

- `python desafio3\conferir.py` mostra os **6 pontos ✓**, o grafo e o grafo **colorido pelos tipos de nó** (modelo de decisão, LLM, tool, função);
- `python desafio3\main.py --perguntas` mostra o caminho de cada uma das 5 perguntas. Com o **JEV real** (gasta **5 créditos**) o resultado esperado é **5 de 5**.
  Com o **Laya** local, que não é calibrado para este domínio, o resultado pode ser menor (3 de 5 nas nossas medições): é parte do que você vai investigar.

## Chave e créditos do JEV

- A chave vai em `JEV_AI_API_KEY` no `.env` (copie o `.env.example`). **Nunca no código, nunca no git.** Sem a chave, o `main.py` **para** e diz o que fazer: não há decisor de mentira nos exemplos. Alternativa grátis e local: o **Laya** (`pip install laya` e `$env:JEV = "laya"`).
- Cada pergunta ao JEV real gasta **1 crédito** (uma chamada, mesmo com 3 perguntas dentro). Rode `--perguntas` poucas vezes.
- Use só textos **fictícios**: o texto é enviado a um serviço externo.

## Para pensar

1. O que muda no grafo se você trocar `LIMIAR_CONFIANCA` de 0,6 para 0,2? Qual pergunta de teste passa a ir por outro caminho?
2. Por que o grafo guarda `confianca` no estado, e não só o `assunto`?
3. Um texto que é urgente **e** traz um CPF vai para onde? Por quê? E se você trocar a ordem das regras?
4. Por que o JEV decide e o LLM escreve, e não o contrário?

## Para ir além (opcional)

- Acrescente uma 4ª pergunta ao JEV (`score`, de 1 a 3: o quanto o tom é agressivo) e um caminho para atendimento humano quando for alto.
- Troque os limiares por valores lidos de variáveis de ambiente e rode as 5 perguntas com valores diferentes.
