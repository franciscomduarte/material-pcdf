# Exercício 01 — Desmonte o agente generalista

**Objetivo:** enxergar, sozinho, as responsabilidades escondidas numa resposta única.

## Preparação

```powershell
copy exemplos\01_agente_generalista\main.py exemplos\01_agente_generalista\exercicio.py
```

Trabalhe no `exercicio.py`; o `main.py` fica intacto para comparação.

## Tarefa

1. Rode o exemplo e leia a **resposta única**. Sublinhe, no papel, cada trecho que pertence a uma
   responsabilidade diferente (fatos, enquadramento legal, risco, recomendação).
2. Escreva, num comentário no início do `exercicio.py`, uma **tabela de especialistas** com 4 linhas:
   nome | recebe (entrada) | devolve (saída) | precisaria de qual ferramenta (Aula 5)?
3. Troque a denúncia por outra (use `DENUNCIA_051` de `caso.py`, ou escreva a sua, **com os fatos no texto**)
   e rode de novo. O que **mudou** na resposta do LLM? O que **não** mudou (a estrutura, a mistura de papéis)?
   Uma resposta bem escrita prova que cada parte foi feita certa?
4. Acrescente ao final do script três `print` respondendo, em uma frase cada:
   *quem errou, se a recomendação estiver ruim? como eu testaria só a parte jurídica? onde estão os fatos?*

## Como saber que deu certo

- Sua tabela tem 4 especialistas com entradas e saídas **diferentes** (nenhum "faz tudo").
- Você consegue dizer por que o próximo exemplo separa os especialistas.

## Para ir além

Rode com `PROVEDOR=claude` (se tiver chave) e compare: o modelo real separa melhor as partes? Mesmo assim,
você consegue **auditar** cada uma?
