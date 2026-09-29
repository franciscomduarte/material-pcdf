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

Comece pelo caminho **urgente** (o mais curto), rode, e vá crescendo o grafo. Um teste passando de cada vez é um bom ritmo.

### Caminhos esperados

| # | Solicitação | Caminho |
|---|---|---|
| 1 | *Estou sem medicação e passando mal, preciso de atendimento agora* | `receber → classificar_urgencia → encaminhar → responder` |
| 2 | *Preciso saber como solicitar uma segunda via de um documento* | `receber → classificar_urgencia → pesquisar → analisar → validar → revisar → analisar → validar → responder` |
| 3 | *Qual o prazo de restituição do imposto de renda de 2031?* | `receber → classificar_urgencia → pesquisar → responder` |
| 4 | o mesmo do Caso 2, com validador que reprova sempre | 3 × `analisar`, termina em `responder` |

## Desafio conceitual: o LLM sabe tudo?

O Caso 3 existe para uma pergunta: **por que não deixamos o LLM responder o prazo da restituição do imposto de renda de 2031?** Responda por escrito, em poucas linhas:

1. O que acontece se o grafo mandar essa pergunta para `analisar` mesmo sem informação na base?
2. Em qual ponto do grafo você impediu isso, e **por que ali** e não dentro do prompt?
3. Um prompt dizendo *"não invente"* resolveria sozinho? Por que a decisão é melhor como **aresta** do que como **pedido educado** ao modelo?

## Para ir além (opcional)

- Se o validador reprovar 3 vezes, em vez de responder "sem validação", **encaminhe a um atendente humano** (um novo nó e um novo rótulo no roteador).
- Faça `pesquisar` e `classificar_urgencia` rodarem **em paralelo** (DAG do exemplo 07) e junte os dois antes de decidir. Que campos cada ramo pode escrever sem sobrescrever o outro?
- Rode o desafio com `PROVEDOR=ollama` e observe: o caminho do Caso 2 continua o mesmo? Por que o ciclo de revisão pode **não aparecer** com um LLM real?
