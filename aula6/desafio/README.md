# Desafio — Análise de solicitação de atendimento

Você vai montar, sozinho, o grafo de um **sistema de atendimento**. Tudo o que precisa foi visto nos exemplos 01 a 10; o exemplo 10 é o seu melhor ponto de partida.

## O problema

Chegam solicitações de atendimento. Algumas são **urgentes** e não podem esperar análise nenhuma; as demais são **normais** e passam por pesquisa, análise, validação e, se preciso, revisão. E há um terceiro caso: perguntas que **a base não sabe responder**. Nesse caso o sistema **não pode deixar o LLM inventar**.

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

## O que já vem pronto (`main.py`)

- `Estado` (o `TypedDict` com os 9 campos), a base de conhecimento e as duas **tools** (`buscar_procedimentos`, `encaminhar_plantao`);
- os **prompts** (`prompt_classificar`, `prompt_analisar`, `prompt_validar`, `prompt_responder`) e as funções que interpretam a resposta do LLM (`normalizar_urgencia`, `analise_aprovada`): você não escreve texto de prompt, só os nós;
- `executar(app, texto)`, que roda o grafo e devolve `(estado_final, caminho_percorrido)`;
- `modelo_mock.py`: o LLM de mentira, para rodar sem API Key.

## O que você escreve

Tudo dentro de `construir_grafo(modelo)`: os **nós**, os **roteadores** e a **montagem** do grafo.

| Nó | Tipo | Lê | Escreve |
|---|---|---|---|
| `receber` | função | `solicitacao` | inicializa **todos** os campos do estado |
| `classificar_urgencia` | LLM | `solicitacao` | `urgencia` (`"urgente"` ou `"normal"`) |
| `encaminhar` | tool | `solicitacao` | `encaminhamento` |
| `pesquisar` | tool | `solicitacao` | `informacao` (`""` se não achou) |
| `analisar` | LLM | `solicitacao`, `informacao`, `feedback` | `analise`, `tentativas` |
| `validar` | LLM | `analise` | `valida`, `feedback` |
| `revisar` | função | `feedback` | `feedback` |
| `responder` | LLM | tudo que existir | `resposta` |

| Roteador | Devolve | Regra |
|---|---|---|
| `rotear_apos_classificar` | `"urgente"` / `"normal"` | lê `urgencia` |
| `rotear_apos_pesquisar` | `"com_base"` / `"sem_base"` | `informacao` vazia = sem base |
| `rotear_apos_validar` | `"ok"` / `"erro"` / `"desistir"` | válida → ok; tentativas ≥ `MAX_TENTATIVAS` → desistir; senão erro |

> **Enunciado completo:** [`ENUNCIADO.md`](ENUNCIADO.md) (o problema, as regras e os casos de aceitação). Este README é o guia de como fazer.

## Qual LLM roda

- `python desafio\\main.py` usa **LLM real**: OpenAI por padrão (`OPENAI_API_KEY` no `.env`, como nas Aulas 4 e 5) ou Ollama (`$env:PROVEDOR = "ollama"`, com `ollama serve` no ar). Sem chave ou com o Ollama fora do ar, ele **avisa e roda com o Mock**.
- O `conferir.py` e os testes usam **sempre o Mock**: são determinísticos e rodam sem internet. `$env:PROVEDOR = "mock"` força o Mock no `main.py`.
- Com LLM real, o caminho pode diferir dos "Caminhos esperados" abaixo (por exemplo, a 1ª análise pode passar direto na validação e o ciclo de revisão não aparecer). Os caminhos esperados valem para o Mock.

## Como fazer: 10 pontos de controle (Parte A: 1 a 7 · Parte B: 8 a 10)

**Não monte o grafo inteiro de uma vez.** Ele cresce em 10 pontos, e cada um tem um teste. Faça um, confira, siga para o próximo:

```powershell
python desafio\conferir.py
```

Ele mostra quais pontos já passaram (✓), qual é o seu ponto atual, o que o teste encontrou e o que fazer. O detalhe de cada ponto está no docstring de `construir_grafo()` em `main.py`.

| Ponto | Você acrescenta | O grafo fica assim | Teste confere |
|---|---|---|---|
| 1 | `receber` com os 9 campos | `START → receber → END` | todos os campos existem no estado |
| 2 | `classificar_urgencia` (LLM) | `… → classificar_urgencia → END` | urgência `urgente` / `normal` certa |
| 3 | `encaminhar`, `responder` e o 1º roteador | urgente: `→ encaminhar → responder` | caminho urgente exato |
| 4 | `pesquisar` e o 2º roteador | normal: `→ pesquisar` ; sem base: `→ responder` | `analisar` **não** roda sem base |
| 5 | `analisar` e `validar` | `com_base → analisar → validar → responder` | passa por `analisar` e `validar`, `tentativas ≥ 1` |
| 6 | `revisar` e o 3º roteador | `validar → (erro) revisar → analisar` | caminho do caso 2, com 1 revisão |
| 7 | a **parada** no roteador | `… → (desistir) responder` | para em `MAX_TENTATIVAS` |

Um ponto por vez. Ao terminar a Parte A, rode também os testes finais do grafo completo (abaixo).

**Parte B (pontos 8 a 10), os tipos de nó.** Depois que os 7 primeiros estiverem ✓, o grafo ganha nós de **tipos** diferentes
(MCP, API e tool, além do LLM). O que vem pronto: o MCP Server `mcp_base.py` (e `base_conhecimento.csv`), `chamar_mcp()`
e `buscar_feriados()`. Você escreve o que muda nos nós. Veja a explicação completa no [`ENUNCIADO.md`](ENUNCIADO.md).

| Ponto | Você faz | O grafo fica assim |
|---|---|---|
| 8 | `pesquisar` chama o **MCP** (e guarda o prazo); `receber` ganha 3 campos | (mesmo desenho; muda o que `pesquisar` faz) |
| 9 | nó `consultar_feriados` (**API**) | `pesquisar → (com_base) consultar_feriados → analisar` |
| 10 | tool `somar_dias_uteis` + nó `calcular_prazo` (**tool**) | `pesquisar → consultar_feriados → calcular_prazo → analisar` |

## Regras que os testes verificam

1. **Urgente não passa por análise.** O caminho é `receber → classificar_urgencia → encaminhar → responder`.
2. **O ciclo de revisão é do grafo**, não de um `while` dentro de um nó (`revisar → analisar`).
3. **O ciclo tem condição de parada** lida do **estado** (`tentativas`). Com um validador que reprova sempre, o grafo para na 3ª tentativa e responde avisando que a análise **não foi validada**.
4. **Sem base, sem invenção.** Se `pesquisar` não achou nada, o caminho vai direto para `responder`, que **admite** não ter a informação e encaminha a um atendente. `analisar` nem roda.
5. **O grafo não conhece o provedor.** Trocar `PROVEDOR` (mock, ollama, openai, claude) não muda uma linha do grafo.

## Como conferir

A partir de `aula6/`, com o ambiente virtual ativo:

```powershell
python desafio\main.py                       # os 3 casos, com o caminho percorrido
python -m unittest desafio.test_desafio -v   # 4 testes (o Caso 4 usa um validador que reprova sempre)
```

Siga os 7 pontos de controle acima: um de cada vez, conferindo no `conferir.py`.

### Caminhos esperados

| # | Solicitação | Caminho |
|---|---|---|
| 1 | *Estou sem medicação e passando mal, preciso de atendimento agora* | `receber → classificar_urgencia → encaminhar → responder` |
| 2 | *Preciso saber como solicitar uma segunda via de um documento* | `receber → classificar_urgencia → pesquisar → analisar → validar → revisar → analisar → validar → responder` |
| 3 | *Qual o prazo de restituição do imposto de renda de 2031?* | `receber → classificar_urgencia → pesquisar → responder` |
| 4 | o mesmo do Caso 2, com validador que reprova sempre | 3 × `analisar`, termina em `responder` |

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

O Caso 3 existe para uma pergunta: **por que não deixamos o LLM responder o prazo da restituição do imposto de renda de 2031?** Responda por escrito, em poucas linhas:

1. O que acontece se o grafo mandar essa pergunta para `analisar` mesmo sem informação na base?
2. Em qual ponto do grafo você impediu isso, e **por que ali** e não dentro do prompt?
3. Um prompt dizendo *"não invente"* resolveria sozinho? Por que a decisão é melhor como **aresta** do que como **pedido educado** ao modelo?

## Para ir além (opcional)

- Se o validador reprovar 3 vezes, em vez de responder "sem validação", **encaminhe a um atendente humano** (um novo nó e um novo rótulo no roteador).
- Faça `pesquisar` e `classificar_urgencia` rodarem **em paralelo** (DAG do exemplo 07) e junte os dois antes de decidir. Que campos cada ramo pode escrever sem sobrescrever o outro?
- Rode o desafio com `PROVEDOR=ollama` e observe: o caminho do Caso 2 continua o mesmo? Por que o ciclo de revisão pode **não aparecer** com um LLM real?
