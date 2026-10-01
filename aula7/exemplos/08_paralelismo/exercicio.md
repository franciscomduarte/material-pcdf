# Exercício 08 — Um terceiro ramo e o conflito de escrita

**Objetivo:** ampliar o fan-out/fan-in e ver por que ramos paralelos escrevem em campos diferentes.

## Preparação

```powershell
copy exemplos\08_paralelismo\main.py exemplos\08_paralelismo\exercicio.py
```

## Tarefa

1. **Terceiro especialista:** acrescente ao `Estado` o campo `analise_conformidade` e crie o nó
   `conformidade` (mesmo formato de `juridico`: chama o modelo com `prompts.conformidade(...)` e escreve só o seu campo).
   Ligue-o em **paralelo** (`investigador -> conformidade`) e inclua-o no fan-in:
   `add_edge(["juridico", "risco", "conformidade"], "consolidar")`.
2. Rode e compare os tempos (cada nó faz uma chamada **real** ao LLM): com **3** ramos, o paralelo leva ~o tempo
   de UMA chamada? E o sequencial? (Com Ollama local as chamadas podem ser atendidas uma por vez; com OpenAI, não.)
3. **Fan-in por lista x arestas separadas:** dê ao `risco` um segundo passo: crie o nó `risco_detalhe`
   (só imprime e devolve `{}`) e ligue `risco -> risco_detalhe`. Agora o ramo do risco tem **2 passos** e o
   jurídico só 1. Ligue o fim dos ramos ao `consolidar` de duas formas e compare o log:
   a) `add_edge(["juridico", "risco_detalhe"], "consolidar")` (lista);
   b) `add_edge("juridico", "consolidar")` e `add_edge("risco_detalhe", "consolidar")` (separadas).
   Quantas vezes aparece `[CONSOLIDAR]` em cada uma? Na (b), com que informação incompleta ele rodou na 1ª vez?
4. **Conflito:** faça `conformidade` escrever no campo `analise_risco` (o mesmo de `risco`). Rode e leia o
   erro do LangGraph (`InvalidUpdateError`). Depois desfaça.

## Como saber que deu certo

- Com OpenAI, o paralelo fica próximo do tempo de UMA chamada e o sequencial cresce com o número de ramos. Com Ollama
  local os dois podem ficar parecidos (o servidor atende uma requisição por vez): explique por quê.
- Em (a) o `[CONSOLIDAR]` roda **1** vez; em (b), **2** (a 1ª sem `analise_risco`). Só a lista faz "esperar todos".
- Você explica por que dois ramos no **mesmo campo** dão erro e como um *reducer* (exercício 07) resolveria.
- Você diz quando **não** dá para paralelizar (o segundo especialista depende da saída do primeiro).

## Para ir além

Faça `conformidade` depender do parecer jurídico (`juridico -> conformidade`). O tempo total volta a crescer?
Desenhe o novo grafo e marque onde ficou a fila.
