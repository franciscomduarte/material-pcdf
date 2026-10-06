# Desafio 2 — Parecer em paralelo com aprovação em dois níveis

Junta tudo da aula: **especialistas em paralelo** (ex. 08), **revisão limitada** (ex. 07) e
**humano no circuito** (ex. 06), agora com **duas pessoas** decidindo. O **gestor** aprova todo
parecer; se o risco for **alto**, o **diretor** também precisa aprovar.

```
START → receber → investigar ─┬─→ juridico ─┐
                              └─→ risco ────┴─→ consolidar  (tentativas + 1; lê feedback_humano)
                                                    ↓
                                          aprovacao_gestor   ← interrupt()
                            ┌───────────────────┼──────────────────────┐
                        rejeita               aprova               rejeita e
                     (restam tent.)              |            tentativas >= MAX_TENTATIVAS
                            ↓        risco baixo → finalizar             ↓
                         revisar          risco alto                  encerrar (limite_de_revisoes)
                            ↓                    ↓
                        consolidar       aprovacao_diretor  ← interrupt()
                                           sim ↙     ↘ não
                                       finalizar      negar (negada_pelo_diretor)
```

## O que já vem pronto (`main.py`)

- `Estado`, `MAX_TENTATIVAS = 3`, `FEEDBACK_PADRAO`;
- `executar(app, solicitacao, decisoes)`: roda o grafo e responde **cada pausa, na ordem**, com a
  próxima decisão (`"sim"`/`"nao"`); devolve `(estado_final, caminho)`;
- `agentes.py` (na pasta acima): os agentes prontos (`Agent`), `prompts.py`: as instruções e as entradas deles; `caso.py`: as denúncias (`DENUNCIA_045`, de alto risco, e `DENUNCIA_BAIXO_VALOR`). O LLM é **REAL** (`PROVEDOR` no `.env`).

## O que você escreve

Tudo em `construir_grafo(checkpointer)`, com **estes nomes de nó**:

| Nó | Tipo | Escreve |
|---|---|---|
| `receber` | função | inicializa **todos** os campos |
| `investigar` | agente `agentes.investigador` | `investigacao` |
| `juridico` | agente `agentes.juridico` | `analise_juridica` |
| `risco` | **dois** agentes: `agentes.risco` (o parecer) e `agentes.classificador` + `prompts.nivel_de` (o nível que decide o caminho) | `analise_risco`, `nivel_risco` (`"alto"`/`"baixo"`) |
| `consolidar` | agente `agentes.redator` (entrada `prompts.entrada_recomendar`, que já recebe o feedback do humano) | `parecer`, `tentativas` |
| `aprovacao_gestor` | `interrupt()` | `aprovado`, `feedback_humano` |
| `revisar` | função | (nada) |
| `aprovacao_diretor` | `interrupt()` | `aprovado` |
| `finalizar` / `encerrar` / `negar` | função | `status` = `"aprovada"` / `"limite_de_revisoes"` / `"negada_pelo_diretor"` |

A resposta do humano chega ao `interrupt()` como `{"aprovado": bool, "feedback": str}`.

## Regras que os testes verificam

1. `juridico` e `risco` rodam **em paralelo** (dois `add_edge` saindo de `investigar`) e **`consolidar` espera os dois** (`add_edge([...], "consolidar")`).
2. Os ramos paralelos escrevem em **campos diferentes** (senão o LangGraph reclama).
3. **Risco baixo**: só o gestor decide. **Risco alto**: gestor **e** diretor.
4. Rejeição do gestor → `revisar → consolidar`, com o feedback no prompt, no máximo `MAX_TENTATIVAS` versões (lido do **estado**).
5. O diretor que nega **encerra** o caso: não há revisão depois do diretor.

## Como conferir

A partir de `aula7/`, com o ambiente virtual ativo:

```powershell
python -m unittest desafio2.test_desafio2 -v
python desafio2\main.py          # os 5 casos, com o caminho percorrido
```

> A ordem entre `juridico` e `risco` no caminho pode variar entre execuções: é esperado.

### Caminhos esperados (ignorando a ordem do par paralelo)

| # | Decisões | Caminho |
|---|---|---|
| 1 | baixo risco; `sim` | `receber → investigar → {juridico, risco} → consolidar → aprovacao_gestor → finalizar` |
| 2 | alto; `sim, sim` | `... → aprovacao_gestor → aprovacao_diretor → finalizar` |
| 3 | alto; `nao, sim, sim` | `... → aprovacao_gestor → revisar → consolidar → aprovacao_gestor → aprovacao_diretor → finalizar` |
| 4 | alto; `sim, nao` | `... → aprovacao_gestor → aprovacao_diretor → negar` |
| 5 | alto; `nao, nao, nao` | 3 × `consolidar`, termina em `encerrar` |

## Perguntas

1. Por que `juridico` e `risco` podem rodar em paralelo aqui, mas não poderiam se o risco dependesse do parecer jurídico?
2. Por que a decisão *"precisa do diretor?"* fica na **aresta** (roteador) e não dentro de `aprovacao_gestor`?
3. Se o diretor nega, por que **não** voltar para `revisar`? Que decisão de processo isso reflete?

## Para ir além (opcional)

- Persista com `SqliteSaver` e deixe o gestor e o diretor decidirem em **processos diferentes**, cada um com `--retomar`.
- Dê ao diretor a opção de **devolver com feedback** (novo rótulo do roteador) sem contar como negação.
