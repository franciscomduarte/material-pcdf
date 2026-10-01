# Exercício guiado — Do grafo ao desenho, e do desenho ao MCP

Você vai fazer, **sozinho e em passos pequenos**, três coisas que já viu na Aula 6 e na Aula 5:

1. pegar o **grafo** de um exemplo (o `app` do LangGraph) e gerar o seu **diagrama Mermaid**;
2. **ver** o diagrama e conferi-lo contra o código;
3. **expor** esse diagrama por um **MCP Server**, para um cliente (o seu teste, ou o Claude Code) pedir *"me mostra o grafo do exemplo X"*.

```
exemplos/10_agente_completo        passo 1                passo 3                    passo 4
        app (LangGraph)  ──►  draw_mermaid()  ──►  MCP Server (mcp_grafos.py)  ──►  cliente (Claude Code)
                                    │                       tools: listar_exemplos,
                                    ▼                       mermaid_do_grafo, descrever_grafo
                               passo 2: mermaid.live
```

Cada passo termina com **"Como saber que deu certo"**. Só siga para o próximo quando der certo.
Há **dicas** recolhidas (clique para abrir) — tente antes de abrir.

## O que já vem pronto

| Arquivo | Para quê |
|---|---|
| `carregar_grafo.py` | `carregar_app("10_agente_completo")` devolve o grafo compilado de um exemplo (leia o comentário: resolve duas armadilhas) |
| `cliente_teste.py` | um cliente MCP mínimo para testar o **seu** servidor sem Claude |
| `test_guiado.py` | os testes de cada passo |
| `mcp.json.example` | modelo de configuração do MCP no Claude Code (passo 4) |

Você escreve: **`passo1_mermaid.py`** e **`mcp_grafos.py`** (os TODOs). Rode tudo **a partir de `aula6/`**, com o ambiente virtual ativo.

---

## Passo 0 — Conferir o ambiente (2 min)

```powershell
python -c "import langgraph, mcp; print('langgraph e mcp OK')"
python exemplos\10_agente_completo\main.py
```

Você deve ver o agente da Aula 6 rodando com o Mock. É **esse** grafo que vamos desenhar.

## Passo 1 — Gerar o Mermaid (10 min)

Abra `exercicio_guiado\passo1_mermaid.py` e complete os TODOs 1 a 4.

<details><summary>Dica TODO 1 e 2</summary>

```python
app = carregar_app(exemplo)
mermaid = app.get_graph().draw_mermaid()
```
</details>

<details><summary>Dica TODO 3 e 4</summary>

`(pasta_saida / f"{exemplo}.mmd").write_text(mermaid, encoding="utf-8")` — e, para o `.md`, uma
f-string com `# {exemplo}`, uma linha em branco, <code>```mermaid</code>, o texto e <code>```</code>.
</details>

Rode:

```powershell
python exercicio_guiado\passo1_mermaid.py            # exemplo 10
python exercicio_guiado\passo1_mermaid.py 07_dag     # outro exemplo
```

**Como saber que deu certo**
- O terminal mostra um texto que começa em `---` / `config:` e depois `graph TD;`.
- Existem `saida\10_agente_completo.mmd` e `saida\10_agente_completo.md`.
- `python -m unittest exercicio_guiado.test_guiado.TestPasso1 -v` passa.

## Passo 2 — Ver e conferir o desenho (10 min)

1. Abra `saida\10_agente_completo.mmd`, copie o conteúdo e cole em **https://mermaid.live**.
   (No VS Code, abra `saida\10_agente_completo.md` e use o *preview* do Markdown; precisa de uma extensão de Mermaid.)
2. Compare o desenho com o código de `exemplos\10_agente_completo\main.py`:
   - Quais setas **tracejadas**? São as arestas **condicionais** (`add_conditional_edges`).
   - Onde está o **ciclo**? Qual nó **decide** parar (a condição de parada)?
3. Responda por escrito (2 linhas cada):
   - Quantos nós o desenho tem? Bate com os `add_node` do código? (`__start__` e `__end__` são do LangGraph.)
   - Gere agora o `07_dag`. Onde estão o **fan-out** e o **fan-in**?

**Como saber que deu certo:** você aponta no desenho o ciclo do exemplo 10 e o "espere todos" do exemplo 07.

## Passo 3 — Transformar em um MCP Server (25 min)

Abra `exercicio_guiado\mcp_grafos.py`. Ele já cria o servidor (`MCPServer`) e declara 3 tools **vazias**.
Complete os TODOs 1 a 3.

> Lembre da Aula 5: uma **tool** é uma função com **nome**, **parâmetros tipados** e uma **docstring**
> que o cliente lê para decidir quando usá-la. O servidor faz o trabalho; o cliente só conhece o contrato.

<details><summary>Dica TODO 1</summary>

`return EXEMPLOS`
</details>

<details><summary>Dica TODO 2</summary>

```python
try:
    return carregar_app(exemplo).get_graph().draw_mermaid()
except ValueError as erro:
    return f"ERRO: {erro}"
```
Por que devolver `"ERRO: ..."` em vez de deixar a exceção subir? O cliente (e o LLM) precisa de uma
resposta que ele consiga **ler e explicar**.
</details>

<details><summary>Dica TODO 3</summary>

`grafo.nodes` é um dicionário (as chaves são os nomes dos nós) e `grafo.edges` uma lista de arestas
com `.source`, `.target` e `.conditional`. Devolva um `dict` simples (só texto, números, listas).
</details>

Teste **sem Claude**, com o cliente de teste:

```powershell
python exercicio_guiado\cliente_teste.py                                  # lista as tools
python exercicio_guiado\cliente_teste.py listar_exemplos
python exercicio_guiado\cliente_teste.py mermaid_do_grafo 07_dag
python exercicio_guiado\cliente_teste.py descrever_grafo 10_agente_completo
python exercicio_guiado\cliente_teste.py mermaid_do_grafo xyz             # deve responder ERRO, sem quebrar
```

**Como saber que deu certo**
- O cliente lista as **3 tools** com as suas descrições.
- `mermaid_do_grafo 07_dag` devolve o mesmo texto do passo 1.
- `python -m unittest exercicio_guiado.test_guiado -v` passa **todos** os testes.

> **Armadilha clássica:** se você colocar um `print()` no servidor, o cliente quebra (o `stdout` é o canal do
> protocolo MCP). Tente de propósito, veja o erro, e desfaça. Para depurar use `print(..., file=sys.stderr)`.

## Passo 4 — Conectar o servidor ao Claude Code (10 min)

Até aqui o **cliente** era o seu script. Agora o cliente é o **Claude Code**, que vai descobrir as tools sozinho.

1. Copie `mcp.json.example` para a **raiz do projeto** com o nome `.mcp.json` e ajuste os caminhos
   (Python do seu `.venv` e o caminho **absoluto** de `mcp_grafos.py`). Ou, em uma linha:

   ```powershell
   claude mcp add grafos -- C:\caminho\aula6\.venv\Scripts\python.exe C:\caminho\aula6\exercicio_guiado\mcp_grafos.py
   ```
2. Reinicie o Claude Code nesta pasta e rode `/mcp`: o servidor `grafos` deve aparecer como **connected**.
3. Peça em linguagem natural:
   > *"Use o MCP grafos para mostrar o Mermaid do exemplo 07_dag e explique onde estão o fan-out e o fan-in."*
   >
   > *"Compare o grafo do 06_fluxo_condicional com o do 10_agente_completo: quais nós o 10 acrescenta?"*

**Como saber que deu certo:** o Claude chama `mermaid_do_grafo` / `descrever_grafo` (você vê a chamada da tool)
e responde com base no **seu** servidor, não de memória.

## Passo 5 — Reflexão (5 min)

1. Por que o servidor devolve **texto Mermaid** e não uma imagem? Quem "desenha"?
2. O que o cliente **sabe** do seu servidor? (Só o contrato: nome, parâmetros, descrição.) O que **não** sabe?
3. Se amanhã você trocar o LangGraph por outra biblioteca dentro do servidor, o que muda para o cliente?

## Para ir além

- Acrescente a tool `caminho_percorrido(exemplo, solicitacao)`: executa o grafo (`app.stream(..., stream_mode="updates")`)
  e devolve a **lista de nós na ordem em que rodaram** (o caminho real, como no desafio 1). Depois peça ao Claude
  para desenhá-lo como um Mermaid destacando o caminho.
- Exponha o Mermaid também como **resource** (`@mcp.resource("grafo://{exemplo}")`) em vez de tool. Qual a diferença de uso?
- Adicione o exemplo `11_grafo_real` (já está em `EXEMPLOS`) e compare: o que o desenho mostra de MCP, API e LLM?

## Troubleshooting

- **`ModuleNotFoundError: mcp`** — `pip install -r requirements.txt` com o `.venv` ativo.
- **O cliente trava ou dá erro de protocolo** — há um `print()` no servidor (ou em algo que ele importa). Use `stderr`.
- **`/mcp` mostra `failed`** — caminho errado no `.mcp.json`; use o Python do `.venv` e caminhos **absolutos**.
- **Mermaid não renderiza no mermaid.live** — cole o conteúdo do `.mmd` inteiro, começando em `---`.
