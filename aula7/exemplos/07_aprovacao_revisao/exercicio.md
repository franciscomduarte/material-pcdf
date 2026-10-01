# Exercício 07 — Histórico de feedbacks e novo limite

**Objetivo:** acumular dados entre voltas do ciclo (reducer) e mexer na condição de parada.

## Preparação

```powershell
copy exemplos\07_aprovacao_revisao\main.py exemplos\07_aprovacao_revisao\exercicio.py
```

> No `exercicio.py`, use outro nome de banco (ex.: `exercicio.db`).

## Tarefa

1. **Limite:** mude `MAX_TENTATIVAS` para `2` e rode `--auto nao,nao,nao`. Quantas versões foram geradas?
   A condição de parada continua sendo lida do **estado**?
2. **Histórico:** hoje `feedback_humano` guarda só o **último** feedback (cada rejeição sobrescreve o anterior).
   Acrescente ao `Estado` o campo `historico_feedback` **acumulando** todos:

   ```python
   import operator
   from typing import Annotated
   historico_feedback: Annotated[list[str], operator.add]
   ```

   Faça `validacao_humana` devolver `{"historico_feedback": [feedback]}` quando rejeitar.
   (`operator.add` é o **reducer**: em vez de sobrescrever, concatena as listas.)
3. No `resultado` final, imprima o histórico numerado.
4. Rode `--auto nao,nao,sim` (com `MAX_TENTATIVAS = 3`) e confira 2 itens no histórico.
5. Rode `--falha-tecnica` e depois `--retomar --auto sim`. O histórico e as tentativas foram afetados
   pelo erro técnico? Por que **não** deveriam ser?

## Como saber que deu certo

- Com `nao,nao,sim` o histórico tem 2 feedbacks e o status é `aprovada`.
- Você distingue, em uma frase, **erro técnico** (retomar) de **rejeição humana** (revisar, conta tentativa).

## Para ir além

Troque o destino do limite: em vez de `encerrar_sem_aprovacao`, crie o nó `encaminhar_responsavel`
que imprime o histórico completo de feedbacks para quem assumir o caso.
