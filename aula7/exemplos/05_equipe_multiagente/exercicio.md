# Exercício 05 — Inclua a Comunicação na equipe

**Objetivo:** estender o grafo com um novo nó e ler o caminho percorrido.

## Preparação

```powershell
copy exemplos\05_equipe_multiagente\main.py exemplos\05_equipe_multiagente\exercicio.py
```

## Tarefa

1. Acrescente ao `Estado` o campo `parecer_comunicacao`.
2. Crie o nó `comunicacao` (roda `agentes.comunicacao`): lê `recomendacao`, escreve `parecer_comunicacao`.
3. Ligue `analista -> comunicacao -> END` (remova a aresta `analista -> END`).
4. Atualize a mensagem do `orquestrador` para refletir o novo plano.
5. Rode e compare o **caminho** impresso com o do exemplo original.
6. **Experimento:** apague, de propósito, `construtor.add_edge("juridico", "analista")` e rode.
   Dá erro? O que aparece no caminho e no estado final? (Dica: `recomendacao` ficou como?) Volte a aresta.
   O que isso ensina sobre "falhas silenciosas" em grafos e como você as detectaria (ex.: um teste que confere o caminho)?

## Como saber que deu certo

- O caminho é `orquestrador -> investigador -> juridico -> analista -> comunicacao`.
- O estado final tem o parecer da Comunicação.
- Você sabe dizer quem é o orquestrador nesta equipe (e por que não é um LLM).

## Para ir além

Faça o `orquestrador` decidir **se** a Comunicação roda (ex.: só quando a recomendação tiver menos de
80 caracteres) usando `add_conditional_edges`. É controle no grafo, não no prompt.
