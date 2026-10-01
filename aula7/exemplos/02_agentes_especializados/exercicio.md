# Exercício 02 — Adicione um quarto especialista

**Objetivo:** criar um especialista novo, com uma única responsabilidade, e encaixá-lo na cadeia.

## Preparação

```powershell
copy exemplos\02_agentes_especializados\main.py exemplos\02_agentes_especializados\exercicio.py
```

## Tarefa

O arquivo `prompts.py` já traz o prompt `prompts.comunicar(texto)` (um parecer sobre a **clareza** do texto final).

1. Crie a função `comunicacao(recomendacao: str) -> str` que chama `modelo.gerar(prompts.comunicar(recomendacao))` e
   imprime `[COMUNICAÇÃO] ...` como os outros especialistas.
2. Gere a recomendação com `modelo.gerar(prompts.recomendar(fatos, enquadramento, risco))` e chame a Comunicação
   **depois** do Analista, passando a recomendação. Imprima o resultado.
3. Escreva, num comentário acima da função, a responsabilidade dela **em uma frase** e o que ela
   **não** faz (ex.: não muda o conteúdo jurídico).

## Como saber que deu certo

- A saída mostra os quatro especialistas, na ordem: Investigador → Jurídico → Analista → Comunicação.
- A resposta da Comunicação é um parecer curto sobre a clareza do texto da recomendação.
- Você repara que o encadeamento continua sendo **variáveis soltas** no script (é o problema do exemplo 03).

## Para ir além

Quantas variáveis soltas você tem agora? Anote o número; no exemplo 03 elas viram **um estado**.
