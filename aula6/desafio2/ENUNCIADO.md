# Enunciado — Desafio 2: despacho de viatura

## O problema

Uma central recebe ocorrências em texto livre e precisa **emitir uma ordem de serviço** para a unidade certa. Você vai montar, com **LangGraph**, o grafo que trata a ocorrência do início ao fim, combinando **LLM**, **MCP Server**, **API externa** e **ferramentas locais**. O grafo só decide a **ordem** e as **decisões**; cada nó cuida do seu trabalho (e das suas falhas).

Exemplos de ocorrências:

- *"Assalto em andamento em Taguatinga, preciso de uma viatura"*
- *"Homem ferido em briga em Sobradinho"*
- *"Tiro disparado no Gama"*
- *"Barulho excessivo em festa na Asa Sul"*
- *"Preciso de ajuda urgente"* (sem local)

## O que o sistema deve fazer

1. **Receber** a ocorrência e preparar o estado.
2. **Extrair** dela, com um **LLM**, o **tipo**, a **gravidade** (`alta` ou `baixa`) e o **bairro**. A resposta do LLM é texto: transforme-a em campos do estado.
3. **Localizar** o bairro (ferramenta local, com o dicionário `BAIRROS`: bairro → latitude/longitude).
   - Bairro **desconhecido**: **pede o endereço** ao usuário e **encerra**.
4. **Buscar unidades** com viatura disponível, em um raio de **20 km** (limite **2**), chamando o **MCP Server** (`unidades_proximas`).
   - **Nenhuma** unidade no raio: **escala a ocorrência ao comando** e **encerra**.
5. **Consultar o clima** (API **Open-Meteo**). Se a API falhar, **o grafo segue** (o clima fica "indisponível").
6. **Calcular o tempo** de chegada da unidade mais próxima: distância ÷ **40 km/h**, em minutos; **+50%** se estiver chovendo.
7. **Acionar apoio**, quando a gravidade for **alta** **e** o tempo estimado for **maior que 8 minutos**: inclui a 2ª unidade (se houver) na observação.
8. **Gerar a ordem de serviço** (LLM), usando **somente** os fatos que estão no estado.
9. **Validar a ordem** (LLM): ela é válida se **citar a unidade despachada**.
   - Inválida: a ordem é **revisada** (volta à geração, com o motivo) e validada de novo.
   - No máximo **3 tentativas**; depois disso o grafo termina.

```
START → receber → extrair → localizar ─┬─ ok ────────> buscar_unidades ─┬─ ok ──────> consultar_clima
                                       │                                │                   │
                                       └─ sem_local -> pedir_endereco   └─ sem_unidade      v
                                                           │               │        calcular_tempo
                                                           v               v                │
                                                          END           escalar -> END      ├─ normal ──┐
                                                                                            └─ apoio    │
                                                                                               │        │
                                                                                        acionar_apoio   │
                                                                                               └───┬────┘
                                                                                                   v
                                                                                 ┌────────> gerar_ordem
                                                                                 │               │
                                                                              revisar            v
                                                                                 ^            validar ─ fim ─> END
                                                                                 └─── erro ─────┘
```

## Entrada e saída

- **Entrada:** o texto da ocorrência.
- **Saída:** o estado final, com a `ordem` (a ordem de serviço, a mensagem de pedir endereço ou a de escalada), e o **caminho percorrido**.

## O que já vem pronto (`main.py`)

O estado, o dicionário de bairros, as constantes, o cliente do MCP Server (`chamar_mcp`), a busca do clima (`buscar_chuva`, já tolerante a falhas), os **prompts** e as funções que interpretam o LLM. O MCP Server (`mcp_unidades.py`, com `unidades.csv`) também já está pronto: a tool `unidades_proximas(latitude, longitude, raio_km, limite)` já descarta as unidades sem viatura.

## Regras que o seu grafo precisa respeitar

1. **Desvios no grafo.** `pedir_endereco` e `escalar` são **nós com aresta própria** (e encerram), não um texto escondido no prompt de outro nó.
2. **Falha da API não derruba o grafo.** O nó de clima trata a falha e o grafo segue (o tempo sai sem ajuste por chuva).
3. **Conta é ferramenta local, não LLM.** O tempo de chegada é calculado em código.
4. **O ciclo de revisão é do grafo** (`revisar → gerar_ordem` é uma aresta), com **parada lida do estado** (`tentativas`).
5. **A ordem usa só os fatos do estado.** Nada inventado.
6. Um nó devolve **só o que mudou**; um roteador só **lê** o estado e devolve um rótulo. Todos os campos são inicializados em `receber`.
7. **O grafo não conhece o provedor de LLM.** Trocar `PROVEDOR` (ollama, openai) não muda uma linha do grafo.

## Os tipos de nó: LLM, MCP, API, tool e função

O grafo não se importa com o tipo de um nó (para ele, todo nó é "uma função que lê o estado e devolve uma atualização"), mas **você** precisa saber o que cada tipo é:

| Tipo | O que é | No desafio |
|---|---|---|
| **LLM** | o modelo escreve ou decide | `extrair`, `gerar_ordem`, `validar` |
| **MCP** | um **serviço** externo, chamado pelo contrato (nome da tool + parâmetros), como na Aula 5 | `buscar_unidades`: o MCP Server `mcp_unidades.py` |
| **API** | uma chamada **HTTP** a um sistema de fora, que pode falhar | `consultar_clima`: Open-Meteo (o grafo segue se ela falhar) |
| **tool** | uma **função de cálculo ou consulta local**, determinística, sem IA | `localizar`, `calcular_tempo` |
| função | lógica simples do próprio grafo | `receber`, `pedir_endereco`, `escalar`, `acionar_apoio`, `revisar` |

Ao terminar, `python desafio2\main.py` mostra o grafo **colorido pelo tipo de cada nó**.

## Casos de aceitação (com LLM real)

| Ocorrência | Caminho esperado |
|---|---|
| Assalto em andamento em Taguatinga | `receber → extrair → localizar → buscar_unidades → consultar_clima → calcular_tempo → gerar_ordem → validar → revisar → gerar_ordem → validar` |
| Homem ferido em briga em Sobradinho | igual, com `acionar_apoio` entre `calcular_tempo` e `gerar_ordem` |
| Tiro disparado no Gama | `receber → extrair → localizar → buscar_unidades → escalar` |
| Barulho excessivo em festa na Asa Sul | como o 1º (gravidade baixa, sem apoio) |
| Preciso de ajuda urgente | `receber → extrair → localizar → pedir_endereco` |

Este desafio **não usa Mock**: o LLM, o MCP Server e a API do clima são reais. O caminho pode variar um pouco (por exemplo, o ciclo de revisão pode não aparecer se o LLM aprovar a 1ª ordem).

## Como fazer

Você escreve os **nós**, os **roteadores** e a **montagem**, em **8 pontos de controle** (funções primeiro, depois a ligação). Confira cada ponto:

```powershell
python desafio2\conferir.py
```

É preciso ter o pacote `mcp` instalado (`pip install -r requirements.txt`). Veja o [`README.md`](README.md) para o passo a passo.

## Você terminou quando

- `python desafio2\conferir.py` mostra os **8 pontos ✓**;
- `python desafio2\main.py` mostra as 5 ocorrências, o desenho do grafo (Mermaid) com o caminho percorrido e o grafo colorido pelos **tipos de nó**;
- `python desafio2\main.py --perguntas` mostra **5 de 5** perguntas no caminho esperado (veja a seção abaixo).

## Para testar o grafo: 5 perguntas, caminhos diferentes

Quando o grafo estiver completo (os 8 pontos ✓), rode as **5 ocorrências** abaixo. Cada uma percorre o grafo por um caminho diferente
(sem apoio, com apoio, escalada, gravidade baixa, sem local). O programa confere o caminho de cada uma:

```powershell
python desafio2\main.py --perguntas
```

| # | Ocorrência | O caminho começa por | Termina em | O que você deve observar |
|---|---|---|---|---|
| 1 | *Assalto em andamento em Taguatinga, preciso de uma viatura* | `receber → extrair → localizar → buscar_unidades → consultar_clima → calcular_tempo → gerar_ordem → ...` | `validar` | GRAVIDADE ALTA, MAS PERTO: o tempo fica abaixo de 8 min, então **não** aciona apoio. |
| 2 | *Homem ferido em briga em Sobradinho* | `... → calcular_tempo → acionar_apoio → gerar_ordem → ...` | `validar` | GRAVIDADE ALTA E LONGE: tempo acima de 8 min, então aciona apoio. |
| 3 | *Tiro disparado no Gama* | `receber → extrair → localizar → buscar_unidades → escalar` | `escalar` | NINGUÉM NO RAIO: o MCP devolve lista vazia. Não consulta o clima, não gera ordem. |
| 4 | *Barulho excessivo em festa na Asa Sul* | `... → calcular_tempo → gerar_ordem → ...` | `validar` | GRAVIDADE BAIXA: mesmo caminho da 1, sem apoio. A decisão veio do **dado**. |
| 5 | *Preciso de ajuda urgente* | `receber → extrair → localizar → pedir_endereco` | `pedir_endereco` | SEM BAIRRO: não localiza, não chama o MCP nem a API. Pede o endereço e encerra. |

Depois de `gerar_ordem`, as ocorrências 1, 2 e 4 passam por `validar`; se o LLM reprovar a ordem, aparece o ciclo `revisar → gerar_ordem → validar`. Ele pode ou
não aparecer: o que o teste confere é o **começo** do caminho e **onde ele termina**.

**Para pensar:** o que muda nos nós percorridos entre a ocorrência 1 e a 4? (Nada: muda só o **dado** de gravidade, que o LLM extraiu.) E entre a 2 e a 3? (O que o MCP devolveu: lista com unidades, ou vazia.)

## Desafio conceitual

1. Por que `calcular_tempo` é uma **tool local** e não um LLM?
2. O que acontece com o grafo se a API de clima estiver fora do ar? **Onde** essa falha é tratada?
3. Por que `escalar` é um **nó com aresta própria** e não um texto no prompt do `gerar_ordem`?

## Para ir além (opcional)

- Ao esgotar as 3 tentativas sem ordem válida, **encaminhe a um operador humano** (novo nó e novo rótulo no roteador).
- `consultar_clima` depende só das **coordenadas**, não das unidades: pense em como rodá-lo **em paralelo** com `buscar_unidades` e que campos cada ramo escreveria.
