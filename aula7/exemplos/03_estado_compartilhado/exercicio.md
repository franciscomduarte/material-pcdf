# Exercício 03 — Um campo novo no estado

**Objetivo:** ampliar o estado compartilhado respeitando "cada um escreve só o que é seu".

## Preparação

```powershell
copy exemplos\03_estado_compartilhado\main.py exemplos\03_estado_compartilhado\exercicio.py
```

## Tarefa

1. Acrescente ao `Estado` o campo `parecer_comunicacao: str`.
2. Crie o especialista **Comunicação** (rode `agentes.comunicacao` com `Runner.run_sync`): ele **lê** `recomendacao` e
   **escreve só** `parecer_comunicacao`. Registre a leitura no mesmo log `lê: ...` dos outros.
3. Encaixe-o depois do Analista e imprima o estado final.
4. Rode **duas denúncias seguidas** (como o exemplo já faz) e confira: o **estado** recomeça vazio
   (o campo novo volta a `""`), mas a **memória** (o histórico) continua crescendo.
5. Faça a memória guardar também o `parecer_comunicacao` de cada análise.

## Como saber que deu certo

- O log mostra `[COMUNICAÇÃO] lê: recomendacao`.
- Nenhum outro especialista foi alterado para acomodar o novo campo.
- Na 2ª execução, `parecer_comunicacao` começa vazio, e o histórico tem 2 itens.

## Para ir além

O que aconteceria se a Comunicação escrevesse em `recomendacao`, sobrescrevendo o Analista?
Por que isso torna difícil descobrir quem errou?
