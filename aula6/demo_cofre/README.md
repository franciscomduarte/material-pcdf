# Demonstração: o cofre

O menor exemplo que tem as três peças de um grafo. Uma pessoa digita a senha de um cofre: acertou, libera; errou, tenta de novo; errou 3 vezes, bloqueia.

```
START → receber → tentar ─┬─ ok ──────> liberar ──> END
                   ^      ├─ bloquear -> bloquear -> END   (errou MAX_TENTATIVAS vezes)
                   └─ erro ┘                                (tenta de novo)
```

| Peça do grafo | No cofre |
|---|---|
| **Estado** (o que o processo lembra) | `entradas`, `tentativas`, `acertou`, `status` |
| **Nó** (uma função: estado → o que mudou) | `receber`, `tentar`, `liberar`, `bloquear` |
| **Decisão** (uma função que só lê o estado e devolve um rótulo) | `rotear_apos_tentar` → `ok` / `erro` / `bloquear` |
| **Ciclo** (uma aresta que volta) | `tentar` → `tentar` |
| **Parada** (limite lido do estado) | `tentativas >= MAX_TENTATIVAS` |

Não há LLM aqui de propósito: um nó é só uma função. No desafio 1 e no desafio 2, alguns nós passam a chamar um LLM, um MCP ou uma API, mas a decisão, o ciclo e a parada são **exatamente** estes.

> **Enunciado completo:** [`ENUNCIADO.md`](ENUNCIADO.md) (o problema, as regras e os casos). Este README é o guia de como fazer.

## Como fazer

O `main.py` é um esqueleto em **5 pontos de controle**, organizado em duas fases dentro de `construir_grafo()`: **FASE A** (as funções) e **FASE B** (ligar os pontos). Trabalhe ponto a ponto: a função do ponto N, a ligação do ponto N, e confira:

```powershell
python demo_cofre\conferir.py
```

Ele mostra ✓/✗ por ponto, o que o teste encontrou, o que fazer e, no final, o **Mermaid do grafo como está agora** (cole em https://mermaid.live, ou abra `demo_cofre/saida/grafo_atual.md` no VS Code).

| Ponto | Você acrescenta | O grafo fica assim |
|---|---|---|
| 1 | `receber` | `START → receber → END` |
| 2 | `tentar` | `… → tentar → END` |
| 3 | `liberar` e a decisão | `tentar → (ok) liberar` |
| 4 | o ciclo | `tentar → (erro) tentar` |
| 5 | a parada e `bloquear` | `tentar → (bloquear) bloquear` |

Quando terminar, rode `python demo_cofre\main.py`: ele executa 3 casos e mostra, nó a nó, tudo o que aconteceu, com o desenho do grafo e o caminho percorrido em amarelo.

Depois, você está pronto para o **desafio 1** (`desafio/`) e o **desafio 2** (`desafio2/`), que têm o mesmo formato.
