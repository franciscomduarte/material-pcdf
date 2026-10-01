# Enunciado — Desafio 1: análise de solicitação de atendimento

## O problema

Um órgão público recebe solicitações de atendimento em texto livre. Você vai montar, com **LangGraph**, o grafo que decide **como cada solicitação é tratada**. O sistema não pode ser um LLM respondendo tudo: há regras que precisam ser cumpridas **sempre**.

Exemplos de solicitações:

- *"Estou sem medicação e passando mal, preciso de atendimento agora"*
- *"Preciso saber como solicitar uma segunda via de um documento"*
- *"Qual o prazo de restituição do imposto de renda de 2031?"*

## O que o sistema deve fazer

1. **Classificar a urgência** da solicitação (`urgente` ou `normal`). Quem classifica é um **LLM**.
2. **Solicitação urgente:** **não passa por análise nenhuma**. É encaminhada ao plantão (tool `encaminhar_plantao`) e o usuário recebe uma resposta informando isso.
3. **Solicitação normal:** o sistema **pesquisa na base de conhecimento** (tool `buscar_procedimentos`).
   - **A base não sabe responder** (nada encontrado): o sistema **admite que não sabe** e encaminha a um atendente. **Não pode inventar uma resposta.**
   - **A base tem a informação:** um LLM **analisa** a solicitação usando **somente** as informações pesquisadas e indica passos numerados.
4. **Validar a análise:** um LLM confere se ela traz **pelo menos três passos numerados e concretos**.
   - Válida: segue para a resposta.
   - Inválida: a análise é **revisada** (volta à análise, com o motivo da reprovação) e validada de novo.
   - No máximo **3 tentativas**. Se ainda assim não for válida, o sistema **responde avisando que a análise não passou pela validação**.
5. **Responder** ao usuário (LLM), com o que existir no estado: encaminhamento, aviso de "sem base" ou a análise.

```
START → receber → classificar_urgencia (LLM) ─┬─ urgente → encaminhar (tool) ─────────────→ responder → END
                                              └─ normal  → pesquisar (tool) ─┬─ sem_base ──→ responder
                                                                             └─ com_base
                                                                                  ↓
                                                                        ┌──→ analisar (LLM)
                                                                        │        ↓
                                                                     revisar ← erro ← validar (LLM) ─ ok ─→ responder
                                                                     (desistir após 3 tentativas → responder)
```

## Entrada e saída

- **Entrada:** o texto da solicitação.
- **Saída:** o estado final, com a `resposta` ao usuário, e o **caminho percorrido** (a lista de nós que rodaram, na ordem).

## Base de conhecimento (já definida em `main.py`)

| Assunto | Informação |
|---|---|
| segunda via | Agendar atendimento; levar documento com foto; pagar a taxa de emissão. |
| passaporte | Preencher o formulário online; agendar a Polícia Federal; pagar a GRU. |
| horário | Atendimento de segunda a sexta, das 8h às 17h. |

## Regras que o seu grafo precisa respeitar

1. **Urgente não passa por análise.** O caminho é `receber → classificar_urgencia → encaminhar → responder`.
2. **O ciclo de revisão é do grafo**, não de um `while` dentro de uma função: `revisar → analisar` é uma **aresta**.
3. **O ciclo tem condição de parada lida do estado** (`tentativas`), nunca de uma variável local.
4. **Sem base, sem invenção.** Se `pesquisar` não achou nada, o caminho vai direto para `responder`, que **admite** não ter a informação. `analisar` **nem roda**.
5. **O grafo não conhece o provedor de LLM.** Trocar `PROVEDOR` (mock, ollama, openai) não muda uma linha do grafo.
6. Um nó devolve **só o que mudou** no estado; um roteador só **lê** o estado e devolve um rótulo. Todos os campos do estado são inicializados em `receber`.

## Casos de aceitação (com o Mock)

| # | Solicitação | Caminho esperado |
|---|---|---|
| 1 | *Estou sem medicação e passando mal, preciso de atendimento agora* | `receber → classificar_urgencia → encaminhar → responder` |
| 2 | *Preciso saber como solicitar uma segunda via de um documento* | `receber → classificar_urgencia → pesquisar → analisar → validar → revisar → analisar → validar → responder` |
| 3 | *Qual o prazo de restituição do imposto de renda de 2031?* | `receber → classificar_urgencia → pesquisar → responder` |
| 4 | o mesmo do caso 2, com um validador que reprova sempre | 3 × `analisar`, termina em `responder` (a resposta avisa que não passou pela validação) |

Com um LLM real o caminho pode variar (por exemplo, a 1ª análise pode passar direto na validação). Os casos acima valem para o Mock.

## Parte B — os tipos de nó: MCP, API e tool (depois que a Parte A estiver pronta)

Na Parte A, os nós eram LLMs e funções simples. Em um sistema real, cada nó é de um **tipo**: o grafo não se
importa com o tipo (para ele, todo nó é "uma função que lê o estado e devolve uma atualização"), mas **você** precisa saber
o que cada tipo é. Na Parte B você troca e acrescenta nós até ter os quatro tipos no mesmo grafo:

| Tipo | O que é | No desafio |
|---|---|---|
| **LLM** | o modelo escreve ou decide | `classificar_urgencia`, `analisar`, `validar`, `responder` |
| **MCP** | um **serviço** externo, chamado pelo contrato (nome da tool + parâmetros), como na Aula 5 | `pesquisar`: a base de conhecimento passa a ser o MCP Server `mcp_base.py` |
| **API** | uma chamada **HTTP** a um sistema de fora, que pode falhar | `consultar_feriados`: BrasilAPI (o grafo segue se ela falhar) |
| **tool** | uma **função de cálculo**, determinística, sem IA | `calcular_prazo` (usa a tool `somar_dias_uteis`) e `encaminhar` |
| função | lógica simples do próprio grafo | `receber`, `revisar` |

O que a Parte B acrescenta ao sistema: quando a solicitação tem base, o usuário recebe também a **data de entrega**.
O prazo (em dias úteis) vem do **MCP**; os **feriados** vêm da **API**; a **tool** calcula a data (pulando fins de semana e
feriados); e o **LLM** usa essa data na análise e na resposta.

```
... → pesquisar (MCP) ─┬─ sem_base ──────────────────────────────────────────→ responder
                       └─ com_base → consultar_feriados (API) → calcular_prazo (tool) → analisar (LLM) → ...
```

**Os pontos da Parte B** (continuam o `conferir.py`):

| Ponto | O que você faz | O teste confere |
|---|---|---|
| 8 | `pesquisar` passa a chamar o **MCP** (`chamar_mcp("consultar_base", ...)`) e guarda também o prazo; `receber` ganha os campos novos | o MCP é chamado; `prazo_dias` = 5 para segunda via; sem base, lista vazia |
| 9 | novo nó `consultar_feriados` (**API**), só no caminho **com base** | o caminho passa pelo nó; `feriados` no estado; urgente e sem base **não** passam |
| 10 | escreve a **tool** `somar_dias_uteis` e o nó `calcular_prazo` | segunda via → `2026-10-06`; passaporte → `2026-10-14` (pula o feriado de 12/10); o prazo chega ao LLM |

**Casos de aceitação da Parte B (com o Mock):**

| Solicitação | Caminho |
|---|---|
| *Preciso saber como solicitar uma segunda via de um documento* | `receber → classificar_urgencia → pesquisar → consultar_feriados → calcular_prazo → analisar → validar → revisar → analisar → validar → responder` |
| *Preciso renovar o passaporte* | igual; `prazo_final` = `2026-10-14` |
| *Qual o horário de atendimento?* | igual, com `prazo_final` vazio (prazo 0) |
| *Qual o prazo de restituição do imposto de renda de 2031?* | `receber → classificar_urgencia → pesquisar → responder` (sem base: **não** chama a API) |

Ao terminar, `python desafio\main.py` mostra o grafo **colorido pelo tipo de cada nó**.

## Como fazer

O `main.py` já traz o estado, as tools, os **prompts** e as funções que interpretam o LLM. Você escreve os **nós**, os **roteadores** e a **montagem** do grafo, em **10 pontos de controle** (Parte A: 1 a 7; Parte B: 8 a 10; funções primeiro, depois a ligação). Confira cada ponto:

```powershell
python desafio\conferir.py
```

Veja o [`README.md`](README.md) para o passo a passo.

## Você terminou quando

- `python desafio\conferir.py` mostra os **10 pontos ✓** (Parte A e Parte B);
- `python -m unittest desafio.test_desafio -v` passa os **4 testes**;
- `python desafio\main.py` mostra os casos, o desenho do grafo (Mermaid) com o caminho percorrido e o grafo colorido pelos **tipos de nó**.
- `python desafio\main.py --perguntas` mostra **5 de 5** perguntas no caminho esperado (veja a seção abaixo).

## Para testar o grafo: 5 perguntas, caminhos diferentes

Quando o grafo estiver completo (Partes A e B), rode as **5 perguntas** abaixo. Cada uma percorre o grafo por um caminho
diferente (urgente, com base e prazo, com base e outro prazo, com base sem prazo, sem base). O programa confere o caminho de cada uma:

```powershell
python desafio\main.py --perguntas
```

| # | Pergunta | O caminho começa por | `prazo_final` | O que você deve observar |
|---|---|---|---|---|
| 1 | *Estou sem medicação e passando mal, preciso de atendimento agora* | `receber → classificar_urgencia → encaminhar → responder` | vazio | URGENTE: não pesquisa, não chama a API, não analisa. Vai direto ao plantão. |
| 2 | *Preciso saber como solicitar uma segunda via de um documento* | `receber → classificar_urgencia → pesquisar → consultar_feriados → calcular_prazo → analisar → ...` | `2026-10-06` | COM BASE: MCP (prazo 5 dias úteis) -> API (feriados) -> tool (data) -> LLM analisa e valida. |
| 3 | *Preciso renovar o passaporte* | `receber → classificar_urgencia → pesquisar → consultar_feriados → calcular_prazo → analisar → ...` | `2026-10-14` | O MESMO caminho, outro DADO: 10 dias úteis atravessam o feriado de 12/10, e a tool o pula. |
| 4 | *Qual o horário de atendimento?* | `receber → classificar_urgencia → pesquisar → consultar_feriados → calcular_prazo → analisar → ...` | vazio | COM BASE, SEM PRAZO (0 dias): calcular_prazo roda, mas devolve prazo_final vazio. |
| 5 | *Qual o prazo de restituição do imposto de renda de 2031?* | `receber → classificar_urgencia → pesquisar → responder` | vazio | SEM BASE: o grafo admite que não sabe. Não chama a API, não analisa, não inventa. |

Em todos os casos o caminho **termina em `responder`**. Com o Mock, as perguntas 2 a 4 ainda passam pelo ciclo `validar → revisar → analisar`
depois de `analisar`. Com um LLM real, o ciclo pode não aparecer: o que o teste confere é o **começo** do caminho e o `prazo_final`.

**Para pensar:** o que muda nos nós percorridos entre a pergunta 2 e a 3? (Nada: muda só o **dado** que a tool calcula.) E entre a 4 e a 5? (O grafo decide, na aresta `sem_base`, não consultar a API nem o LLM.)

## Desafio conceitual: o LLM sabe tudo?

Responda por escrito, em poucas linhas:

1. O que acontece se o grafo mandar a pergunta do imposto de renda de 2031 para `analisar`, mesmo sem informação na base?
2. Em qual ponto do grafo você impediu isso, e **por que ali** e não dentro do prompt?
3. Um prompt dizendo *"não invente"* resolveria sozinho? Por que a decisão é melhor como **aresta** do que como pedido educado ao modelo?

## Para ir além (opcional)

- Ao desistir depois de 3 tentativas, **encaminhe a um atendente humano** em vez de responder "sem validação" (novo nó e novo rótulo no roteador).
- Faça `classificar_urgencia` e `pesquisar` rodarem **em paralelo** (como o DAG do exemplo 07). Que campos cada ramo pode escrever sem sobrescrever o outro?
