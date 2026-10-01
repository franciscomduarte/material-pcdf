# Desafio 2 — Despacho de viatura

Monte, sozinho, o grafo que trata uma ocorrência em texto livre e emite uma **ordem de serviço**. Use o exemplo 11 (`exemplos/11_grafo_real`) como modelo: ele mistura os mesmos tipos de nó.

Exemplos de entrada: *"Assalto em andamento em Taguatinga, preciso de uma viatura"*, *"Barulho excessivo em festa na Asa Sul"*.

> **Enunciado completo:** [`ENUNCIADO.md`](ENUNCIADO.md) (o problema, as regras e os casos de aceitação). Este README é o guia de como fazer.

## Qual LLM roda

Este desafio **não usa Mock**: tudo é de verdade (LLM, MCP Server e API do clima).

- O `main.py` e o `conferir.py` usam **LLM real**: OpenAI por padrão (`OPENAI_API_KEY` no `.env`, como nas Aulas 4 e 5) ou Ollama (`$env:PROVEDOR = "ollama"`, com `ollama serve` no ar). Sem chave ou com o Ollama fora do ar, o programa **para** e diz o que fazer.
- Como o texto do LLM varia, os testes conferem o **caminho** do grafo (a estrutura), não as palavras da ordem. O `conferir.py` leva cerca de 1 minuto quando todos os pontos já passam (cada teste chama o LLM e sobe o MCP Server).
- O caminho pode diferir dos "Caminhos esperados" abaixo (por exemplo, a 1ª ordem pode passar direto na validação e o ciclo de revisão não aparecer).
- Sem internet, a API do clima fica indisponível e o grafo **segue** (é uma regra do desafio): `$env:CLIMA_OFFLINE = "1"`.

## Como fazer: 8 pontos de controle

**Não monte o grafo inteiro de uma vez.** O arquivo `main.py` já está organizado em duas fases dentro de `construir_grafo()`: **FASE A** (construir as funções: nós e roteadores) e **FASE B** (ligar os pontos). Trabalhe ponto a ponto: a função do ponto N, a ligação do ponto N, e confira:

```powershell
python desafio2\conferir.py
```

Ele mostra ✓/✗ por ponto, o que o teste encontrou, o que fazer e, no final, o **Mermaid do grafo como está agora** (cole em https://mermaid.live, ou abra `desafio2/saida/grafo_atual.md` no VS Code): você **vê o grafo crescer** a cada ponto.

| Ponto | Você acrescenta | Teste confere |
|---|---|---|
| 1 | `receber` (14 campos) | todos os campos existem no estado |
| 2 | `extrair` (LLM) | tipo, gravidade e bairro extraídos |
| 3 | `localizar` (tool local), `pedir_endereco` e o 1º roteador | sem bairro termina em `pedir_endereco` |
| 4 | `buscar_unidades` (MCP), `escalar` e o 2º roteador | sem unidade termina em `escalar` |
| 5 | `consultar_clima` (API) e `calcular_tempo` | o grafo segue sem clima; chuva aumenta o tempo em 50% |
| 6 | `acionar_apoio`, o roteador de apoio e `gerar_ordem` | apoio só se gravidade alta E tempo > 8 min |
| 7 | `validar`, `revisar` e o ciclo | 1 revisão no caso do assalto |
| 8 | a **parada**, no roteador de validar | para em `MAX_TENTATIVAS` |

## O que já vem pronto (`main.py`)

- `Estado`, `BAIRROS` e as constantes (`MAX_TENTATIVAS`, `LIMITE_APOIO_MIN`, `VELOCIDADE_KMH`);
- `chamar_mcp()` (cliente do MCP Server `mcp_unidades.py`) e `buscar_chuva()` (API Open-Meteo, já tolerante a falhas; `CLIMA_OFFLINE=1` a desliga);
- os **prompts** (`prompt_*`) e as funções que interpretam o LLM (`interpretar_extracao`, `ordem_aprovada`);
- `executar()` e, no fim do arquivo, as funções de visualização (`mostrar_execucao`, `mermaid_do_grafo`, `salvar_mermaid`, `mermaid_por_tipo`) e as **5 perguntas de teste** (`PERGUNTAS_DE_TESTE`, `rodar_perguntas`);
- `mcp_unidades.py` + `unidades.csv` (o MCP Server) e `provedor.py` (pasta acima, que escolhe o LLM real).

## O que você escreve (`main.py`, nesta pasta)

Os nós e roteadores (Fase A) e a montagem (Fase B), com **estes nomes de nó** (o tipo de cada um aparece colorido no desenho do `main.py`):

| Nó | Tipo | O que faz |
|---|---|---|
| `receber` | função | limpa a entrada e inicializa **todos** os campos do estado |
| `extrair` | LLM | devolve JSON com `tipo`, `gravidade` (`alta`/`baixa`) e `bairro` |
| `localizar` | tool local | converte o bairro em latitude/longitude (use o dicionário `BAIRROS`) |
| `pedir_endereco` | função | bairro desconhecido: pede o bairro e **encerra** |
| `buscar_unidades` | MCP | chama `unidades_proximas` (raio de 20 km, limite 2) |
| `escalar` | função | nenhuma unidade no raio: escala ao comando e **encerra** |
| `consultar_clima` | API | Open-Meteo; se a API falhar, **o grafo segue** |
| `calcular_tempo` | tool local | distância ÷ 40 km/h, em minutos; **+50% se estiver chovendo** |
| `acionar_apoio` | função | inclui a 2ª unidade, se houver |
| `gerar_ordem` | LLM | redige a ordem usando **só** os fatos do estado |
| `validar` | LLM | a ordem é válida se citar a unidade despachada |
| `revisar` | função | devolve o feedback para `gerar_ordem` |

Regras de decisão:

1. Sem coordenadas (bairro desconhecido) → `pedir_endereco`.
2. Nenhuma unidade com viatura no raio → `escalar`.
3. Gravidade **alta** e tempo **> 8 min** → `acionar_apoio` antes de `gerar_ordem`.
4. Validação reprovada → `revisar` → `gerar_ordem`, com **no máximo 3 tentativas** (lidas do estado).

## Caminhos esperados (podem variar um pouco com o LLM real)

| Solicitação | Caminho |
|---|---|
| Assalto em andamento em Taguatinga | `receber → extrair → localizar → buscar_unidades → consultar_clima → calcular_tempo → gerar_ordem → validar → revisar → gerar_ordem → validar` |
| Homem ferido em briga em Sobradinho | igual, com `acionar_apoio` entre `calcular_tempo` e `gerar_ordem` |
| Tiro disparado no Gama | `receber → extrair → localizar → buscar_unidades → escalar` |
| Barulho excessivo em festa na Asa Sul | como o 1º (gravidade baixa, sem apoio) |
| Preciso de ajuda urgente | `receber → extrair → localizar → pedir_endereco` |

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

## Perguntas

1. Por que `calcular_tempo` é uma tool local e não um LLM?
2. O que acontece com o grafo se a API de clima estiver fora do ar? Onde essa falha é tratada?
3. Por que `escalar` é um nó com aresta própria, e não um texto no prompt do `gerar_ordem`?
