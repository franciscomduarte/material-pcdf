# Desafio — Parecer com aprovação humana condicionada ao risco

Nem todo caso precisa de um humano. Uma denúncia de **baixo valor** pode ser encerrada
automaticamente; uma de **alto risco** só vale depois que uma pessoa aprova. Você vai montar
esse grafo, com **revisão limitada** quando o humano rejeita.

```
START → receber → investigar → avaliar_risco (LLM) ─┬─ baixo → finalizar → END   (aprovada_automaticamente)
                                                    └─ alto
                                                        ↓
                                              ┌──→ recomendar (LLM; lê feedback_humano; tentativas + 1)
                                              │        ↓
                                           revisar   validacao_humana  ← interrupt()
                                              ↑        ↓
                                              └─ nao ──┼── sim → finalizar → END   (aprovada)
                                                       └─ nao e tentativas >= MAX_TENTATIVAS → encerrar → END
                                                                                              (limite_de_revisoes)
```

## O que já vem pronto (`main.py`)

- `Estado` (o `TypedDict`), `MAX_TENTATIVAS = 3` e `FEEDBACK_PADRAO`;
- `executar(app, solicitacao, decisoes)`: roda o grafo, responde cada pausa com a próxima decisão
  (`"sim"`/`"nao"`) e devolve `(estado_final, caminho_percorrido)`;
- `prompts.py` (na pasta acima): os prompts dos especialistas; `caso.py`: as denúncias (`DENUNCIA_045`, de alto risco, e `DENUNCIA_BAIXO_VALOR`). O LLM é **REAL** (`PROVEDOR` no `.env`).

## O que você escreve

Tudo em `construir_grafo(modelo, checkpointer)`. Use **exatamente** estes nomes de nó
(os testes conferem o caminho):

| Nó | Tipo | Escreve |
|---|---|---|
| `receber` | função | inicializa **todos** os campos |
| `investigar` | LLM (`prompts.investigar`) | `investigacao` |
| `avaliar_risco` | LLM (`prompts.classificar_risco` + `prompts.nivel_de`) | `nivel_risco` (`"alto"`/`"baixo"`) |
| `recomendar` | LLM (`prompts.recomendar`, que já recebe o feedback do humano) | `recomendacao`, `tentativas` |
| `validacao_humana` | `interrupt()` | `aprovado`, `feedback_humano` |
| `revisar` | função | (nada; só marca a volta) |
| `finalizar` | função | `status` |
| `encerrar` | função | `status = "limite_de_revisoes"` |

Roteadores: `avaliar_risco` → `"baixo"`/`"alto"`; `validacao_humana` → `"aprovada"`/`"revisar"`/`"desistir"`.
A resposta do humano chega ao `interrupt()` como `{"aprovado": bool, "feedback": str}`.

## Regras que os testes verificam

1. **Baixo risco não chama o humano**: caminho `receber → investigar → avaliar_risco → finalizar`, sem pausa.
2. **Alto risco pausa** em `validacao_humana` e só segue com a decisão.
3. **Rejeição gera revisão com feedback**: `revisar → recomendar`, e a 2ª recomendação leva o feedback.
4. **O ciclo tem condição de parada** lida do **estado** (`tentativas`), não de um `while`.
5. **Nada com efeito colateral antes do `interrupt()`** (o nó roda de novo na retomada).

## Como conferir

A partir de `aula7/`, com o ambiente virtual ativo:

```powershell
python -m unittest desafio.test_desafio -v
```

Comece pelo caminho **baixo risco** (o mais curto) e vá crescendo o grafo.

## Desafio conceitual

1. Por que a decisão *"precisa de humano?"* é melhor como **aresta** do que como um `if` escondido dentro de um nó?
2. Se `avaliar_risco` classificar **errado** um caso grave como baixo, o que o sistema perde? Que salvaguarda você adicionaria?
3. O que aconteceria se `recomendar` enviasse um e-mail ao órgão **antes** do `interrupt()`?

## Para ir além (opcional)

- Ao atingir o limite, em vez de encerrar, **encaminhe a um responsável** (novo nó, novo rótulo).
- Persista em SQLite (`SqliteSaver`) e retome o caso em **outro processo**, como no exemplo 06.
- Adicione um erro técnico simulado em `investigar` e retome com `invoke(None, config)` sem contar tentativa.
