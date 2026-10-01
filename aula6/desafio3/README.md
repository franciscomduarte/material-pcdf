# Desafio 3 — Decisões tipadas com o JEV

> **Enunciado completo:** [`ENUNCIADO.md`](ENUNCIADO.md) (o problema, o que é o JEV, as regras e os casos de aceitação). Este README é o guia de como fazer.

O grafo decide o caminho por **probabilidades** do **JEV** (um modelo de decisões tipadas) e usa o **LLM** só para escrever a resposta.

## O que já vem pronto

- `jev.py`: o cliente do JEV (`JevReal` chama a API; `JevMock` decide por palavras-chave, para os testes) e `obter_jev()`;
- em `main.py`: `Estado`, os limiares, as `PERGUNTAS_JEV`, a base, a tool `encaminhar_plantao`, o prompt do `responder`, `executar()`, as
  funções para ver o que aconteceu e as **5 perguntas** de teste;
- `modelo_mock.py`: o LLM de mentira (só para os testes).

## Como fazer: 6 pontos de controle

**Não monte o grafo inteiro de uma vez.** O `main.py` está organizado em **FASE A** (as funções) e **FASE B** (ligar os pontos). Trabalhe ponto a ponto
(a função do ponto N, a ligação do ponto N) e confira:

```powershell
python desafio3\conferir.py
```

Ele mostra ✓/✗ por ponto, o que o teste encontrou, o que fazer e o **grafo como está agora** (cole em https://mermaid.live ou abra
`desafio3/saida/grafo_atual.md` no VS Code). Ao terminar, mostra também o grafo colorido pelos **tipos de nó**.

| Ponto | Você acrescenta | O grafo fica assim |
|---|---|---|
| 1 | `receber` | `START → receber → END` |
| 2 | `avaliar` (**JEV**): guarda os números no estado | `… → avaliar → END` |
| 3 | `encaminhar`, `responder` e o **roteador** (`urgente` ou `outros`) | `avaliar → (urgente) encaminhar → responder` |
| 4 | `alertar_dado_sensivel` e a regra do **dado sensível** | `avaliar → (sensivel) alertar_dado_sensivel` |
| 5 | `pedir_esclarecimento` e a regra do **incerto** | `avaliar → (incerto) pedir_esclarecimento` |
| 6 | `pesquisar` e a regra final (**com base** / **sem base**) | `avaliar → (com_base) pesquisar → responder`; `(sem_base) → responder` |

## Qual JEV e qual LLM rodam

- `python desafio3\conferir.py` e os testes usam **sempre** o `JevMock` e o `ModeloMock`: determinísticos, sem internet e **sem gastar créditos**.
- `python desafio3\main.py` usa o **JEV real** se houver `JEV_AI_API_KEY` no `.env` (cada pergunta = **1 crédito**) e o **LLM real** (OpenAI por padrão, como nas outras aulas).
  Sem a chave, avisa e usa os de mentira. `$env:JEV = "mock"` força o `JevMock`.

## Para testar o grafo: 5 perguntas, 5 caminhos

```powershell
python desafio3\main.py --perguntas
```

| # | Pergunta | Caminho | O que observar |
|---|---|---|---|
| 1 | *Estou sem medicação e passando mal, preciso de atendimento agora* | `receber → avaliar → encaminhar → responder` | urgente (≈0,98): o risco vence |
| 2 | *Meu CPF é 123.456.789-00 e a senha do portal é abc123...* | `receber → avaliar → alertar_dado_sensivel` | sensível (≈0,99): nem chega ao LLM |
| 3 | *Quero o passaporte, ou melhor, a segunda via do documento, não sei qual* | `receber → avaliar → pedir_esclarecimento` | confiança baixa (≈0,3): não adivinha |
| 4 | *Preciso saber como solicitar uma segunda via de um documento* | `receber → avaliar → pesquisar → responder` | com base, confiança 1,0 |
| 5 | *Qual o prazo de restituição do imposto de renda de 2031?* | `receber → avaliar → responder` | sem base: admite que não sabe |

## Troubleshooting

- **`AVISO: JEV_AI_API_KEY não está definida`**: normal sem a chave; o programa usa o `JevMock`. Para o real, preencha o `.env`.
- **`JEV respondeu 402`**: acabaram os créditos da conta. **`401`**: chave inválida. **`429`**: muitas chamadas; aguarde.
- **O esqueleto "passa tudo"**: `$env:DESAFIO_DIR` ficou definida; limpe com `Remove-Item Env:DESAFIO_DIR`.
