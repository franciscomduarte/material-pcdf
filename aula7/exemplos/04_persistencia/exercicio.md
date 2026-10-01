# Exercício 04 — Mude o breakpoint e crie duas execuções

**Objetivo:** dominar `interrupt_before`, `get_state` e `thread_id`.

## Preparação

```powershell
copy exemplos\04_persistencia\main.py exemplos\04_persistencia\exercicio.py
```

> No `exercicio.py`, troque o nome do arquivo `.db` (ex.: `exercicio.db`) para não misturar com o do exemplo.

## Tarefa

1. **Mude o breakpoint:** em vez de parar antes de `analista`, pare antes de `juridico`
   (`interrupt_before=["juridico"]`). Rode, e confira com `get_state(config).next` que o próximo nó é `juridico`
   e que só `solicitacao` e `investigacao` estão preenchidos.
2. **Retome em outro processo** (`--retomar`) e confirme que o estado final é o mesmo do exemplo original.
3. **Duas execuções, um banco:** use dois `thread_id` diferentes (ex.: `denuncia-045` e `denuncia-051`) com
   denúncias diferentes. Pare **as duas** no breakpoint e retome **só a 051**. A 045 continua pausada?
   Prove com `get_state`.
4. Use `--historico` (ou `get_state_history`) e conte quantos checkpoints cada execução tem.

## Como saber que deu certo

- O `next` mostrado é `('juridico',)` na pausa.
- As duas denúncias não se misturam: cada `thread_id` tem seu próprio estado.
- Você explica, em uma frase, para que serve o `thread_id`.

## Para ir além

Apague o arquivo `.db` no meio e tente retomar. Qual é a mensagem? O que isso ensina sobre onde o
checkpoint precisa morar em produção?
