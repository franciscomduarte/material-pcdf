# Exercício 02 — Adicione um quarto especialista

**Objetivo:** criar um especialista novo, com uma única responsabilidade, e encaixá-lo na cadeia.

## Preparação

```powershell
copy exemplos\02_agentes_especializados\main.py exemplos\02_agentes_especializados\exercicio.py
```

## Tarefa

O arquivo `prompts.py` já traz as instruções `prompts.INSTR_COMUNICACAO` (um parecer sobre a **clareza** do texto final)
e `prompts.INSTR_REDATOR` (a recomendação), além de `prompts.entrada_recomendar(...)`, que monta a entrada do redator.

1. Crie o agente `comunicacao = Agent(name="Comunicacao", instructions=prompts.INSTR_COMUNICACAO)` e rode-o com a
   função `executar`, que imprime `[COMUNICACAO]` como os outros especialistas.
2. Crie o agente `redator` (`prompts.INSTR_REDATOR`), gere a recomendação com
   `executar(redator, prompts.entrada_recomendar(fatos, enquadramento, risco))` e chame a Comunicação
   **depois** do Analista, passando a recomendação. Imprima o resultado.
3. Escreva, num comentário acima do agente, a responsabilidade dele **em uma frase** e o que ele
   **não** faz (ex.: não muda o conteúdo jurídico).

## Como saber que deu certo

- A saída mostra os quatro especialistas, na ordem: Investigador → Jurídico → Analista → Comunicação.
- A resposta da Comunicação é um parecer curto sobre a clareza do texto da recomendação.
- Você repara que o encadeamento continua sendo **variáveis soltas** no script (é o problema do exemplo 03).

## Para ir além

Quantas variáveis soltas você tem agora? Anote o número; no exemplo 03 elas viram **um estado**.
