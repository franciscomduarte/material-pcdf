# Exercício 06 — Registre o motivo da rejeição

**Objetivo:** usar o valor devolvido pelo `interrupt()` e entender que o nó roda de novo na retomada.

## Preparação

```powershell
copy exemplos\06_human_in_the_loop\main.py exemplos\06_human_in_the_loop\exercicio.py
```

> No `exercicio.py`, use outro nome de banco (ex.: `exercicio.db`).

## Tarefa

1. Acrescente ao `Estado` o campo `motivo: str`.
2. Mude a resposta do humano de `"sim"`/`"nao"` para um dicionário
   `{"aprovado": bool, "motivo": str}` (em `--retomar`, aceite `sim` ou `nao:texto do motivo`).
3. Guarde o `motivo` no estado e **imprima-o** no nó `rejeitada`.
4. **Prove a pegadinha:** ponha um `print("ANTES do interrupt")` no início de `validacao_humana`.
   Rode até pausar e retome. Quantas vezes a mensagem aparece? Por quê?
5. **Experimento:** tente retomar duas vezes seguidas com `--retomar sim`. O que acontece na 2ª?
   (Dica: use `get_state(config).next`.)

## Como saber que deu certo

- `--retomar nao:faltam prazos` termina em `[REJEITADA]` mostrando `faltam prazos`.
- Você explica por que o `print` aparece **duas vezes** e por que isso proíbe efeitos colaterais
  (enviar e-mail, gravar, cobrar) antes do `interrupt()`.

## Para ir além

Aceite uma resposta inválida (ex.: `talvez`). Hoje ela vira "rejeitada" em silêncio. Mude o comportamento:
repita a pergunta (chame `interrupt()` de novo dentro do nó, em um laço curto).
