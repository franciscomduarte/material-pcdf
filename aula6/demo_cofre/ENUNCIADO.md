# Enunciado — O cofre

## O problema

Um cofre eletrônico guarda a senha `1234`. Uma pessoa tenta abri-lo digitando senhas, uma de cada vez.

- Se a senha estiver **certa**, o cofre **libera**.
- Se estiver **errada**, a pessoa **tenta de novo**.
- Se errar **3 vezes**, o cofre **bloqueia** e não aceita mais tentativas.

Você vai **modelar esse processo como um grafo** com LangGraph. O objetivo não é o cofre: é enxergar, no menor exemplo possível, as três peças que todo grafo de agentes usa.

| Peça | O que é | No cofre |
|---|---|---|
| **Estado** | o que o processo lembra | as senhas digitadas, quantas tentativas já houve, se acertou, o resultado |
| **Decisão** | escolher o próximo passo olhando o estado | acertou? errou? já errou demais? |
| **Ciclo com parada** | repetir, mas com limite | tentar de novo, no máximo 3 vezes |

## Entrada e saída

- **Entrada:** uma lista de senhas, na ordem em que a pessoa as digita. Exemplo: `["0000", "1234"]`.
- **Saída:** o estado final, com `status` igual a `"liberado"` ou `"bloqueado"`, e o número de `tentativas`.

## O estado (já definido em `main.py`)

| Campo | Tipo | Significado |
|---|---|---|
| `entradas` | lista de texto | as senhas que a pessoa digita (simuladas) |
| `tentativas` | inteiro | quantas vezes já tentou |
| `acertou` | verdadeiro/falso | a última senha estava certa? |
| `status` | texto | `""` enquanto decide; depois `"liberado"` ou `"bloqueado"` |

## O que o grafo deve fazer

1. **`receber`**: começa o processo com `tentativas` = 0, `acertou` = falso e `status` = vazio.
2. **`tentar`**: pega a senha da vez (`entradas[tentativas]`; se as senhas acabaram, conta como senha vazia), compara com `SENHA` e soma uma tentativa.
3. **`liberar`**: marca `status` = `"liberado"`.
4. **`bloquear`**: marca `status` = `"bloqueado"`.
5. **Decisão após `tentar`** (um roteador, que só **lê** o estado):
   - acertou → `liberar`;
   - errou e `tentativas >= MAX_TENTATIVAS` → `bloquear`;
   - errou e ainda há tentativas → `tentar` de novo.

## Regras que o seu grafo precisa respeitar

- O **ciclo é do grafo**: `tentar` volta para si mesmo por uma **aresta**. Nada de `while` dentro de uma função.
- A **parada** é lida do **estado** (`tentativas`), não de uma variável local.
- Uma função (nó) devolve **só o que mudou** no estado. O roteador só **lê** e devolve um rótulo.
- Não há LLM nem internet: cada nó é só uma função.

## Casos para conferir

| Senhas digitadas | Caminho esperado | Resultado |
|---|---|---|
| `["1234"]` | `receber → tentar → liberar` | liberado, 1 tentativa |
| `["0000", "1234"]` | `receber → tentar → tentar → liberar` | liberado, 2 tentativas |
| `["0", "1", "2", "1234"]` | `receber → tentar → tentar → tentar → bloquear` | bloqueado, 3 tentativas (a 4ª senha nem é usada) |
| `[]` | `receber → tentar → tentar → tentar → bloquear` | bloqueado, 3 tentativas |

## Como fazer

Siga os **5 pontos de controle** do `main.py` (funções primeiro, depois a ligação) e confira cada um:

```powershell
python demo_cofre\conferir.py
```

Veja o [`README.md`](README.md) para o passo a passo.

## Você terminou quando

- `python demo_cofre\conferir.py` mostra os **5 pontos ✓**;
- `python demo_cofre\main.py` imprime os 3 casos e o desenho do grafo, com o caminho percorrido em amarelo;
- você consegue apontar no desenho: o **estado**, uma **decisão** (seta tracejada), o **ciclo** e a **parada**.

## Para pensar

1. O que aconteceria se o roteador não olhasse `tentativas`? Quem interromperia o ciclo?
2. Por que `tentar` não decide sozinho para onde ir?
3. Se a senha certa pudesse mudar entre tentativas, qual campo do estado precisaria existir?
