# Aula 5 — MCP (Model Context Protocol) aplicado a Agentes de IA

Cenário: **CISP — Central Integrada de Segurança Pública** (fictícia). Todos os
dados são sintéticos e gerados de forma determinística.

Este README cobre o setup técnico. O conteúdo da aula (conceitos, exemplos e
atividades) acompanha os slides.

## Pré-requisitos (primeira vez)

- **Docker Desktop** instalado e **aberto** (`docker version` deve mostrar *Client* e *Server*).
  No Windows, com a virtualização ligada (WSL 2). Em Mac com chip Apple, o SQL Server
  roda por emulação e pode ser lento.
- Espaço livre de **cerca de 4 GB** para as imagens (SQL Server ≈ 2,3 GB, PostgreSQL ≈ 0,6 GB).
  O primeiro `docker compose up` baixa essas imagens e leva alguns minutos.
- Memória: o container do SQL Server precisa de **pelo menos 2 GB** livres no Docker
  (recomendado: máquina com 8 GB de RAM).
- Portas livres no seu computador: **5434** (PostgreSQL) e **1433** (SQL Server).
- **Python 3.10 ou mais novo**, **Node.js** (para o MCP Inspector) e uma chave da OpenAI
  (ou o Ollama, se preferir rodar local).

## Setup — Blocos 1 a 4 (só bancos)

```bash
git clone https://github.com/franciscomduarte/material-pcdf.git
cd material-pcdf/aula5
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt   # todas as dependências dos exemplos

cp .env.example .env              # Windows (cmd/PowerShell): copy .env.example .env
# abra o .env e preencha OPENAI_API_KEY

docker compose up -d postgres mssql
docker compose ps   # aguarde os dois ficarem "healthy"
```

O Postgres roda o `banco-postgres/init.sql` automaticamente (via
`docker-entrypoint-initdb.d`). O SQL Server **não** tem esse hook, então o
schema é aplicado manualmente:

Funciona em qualquer shell (PowerShell, cmd, bash), sem redirecionamento `<`:

```bash
docker cp banco-sqlserver/init.sql cisp-mssql:/tmp/init.sql
docker exec cisp-mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YourStrong@Password123' -C -i /tmp/init.sql
```

> A senha do `sa` é a `SA_PASSWORD` do `docker-compose.yml`. O SQL Server exige
> senha complexa (8+ caracteres, maiúscula, minúscula, número e símbolo); uma
> senha simples como `12345678` faz o container falhar ao iniciar. Se trocar a
> senha, troque também no `.env` (`MSSQL_PASSWORD`) e no healthcheck do compose.

> No Git Bash (Windows), se aparecer erro de path tipo `C:/Program Files/Git/opt/...`,
> rode com `MSYS_NO_PATHCONV=1` na frente do comando `docker exec`.

Depois, gere a massa de dados (determinística — mesmos resultados para toda a turma):

```bash
cd dados
python seed_postgres.py
python seed_sqlserver.py
cd ..
```

Saída esperada (`seed_postgres.py`): `OK: 20000 ocorrências inseridas...`,
com Região Bravo, Foxtrot e Kilo no topo do ranking (são os "hotspots"
intencionais da massa de dados — ver `dados/referencia.py`).

Agora os exemplos em `exemplos/01_tool_local` até `exemplos/11_observabilidade`
podem ser executados diretamente (`python exemplos/04_agente_mcp/agente.py`
etc.) — eles sobem os MCP Servers via **stdio**, conectando no Postgres/SQL
Server pelas portas publicadas em `localhost`.

## Bloco 5 — subindo tudo via Docker (Streamable HTTP)

A partir daqui, os MCP Servers passam a rodar como serviços HTTP
independentes, e o agente final conecta neles por rede (não mais stdio).
Isso usa o profile `full` do `docker-compose.yml`:

```bash
docker compose --profile full up -d --build mcp-ocorrencias mcp-operacoes mcp-servicos
docker compose --profile full run --rm agente python main.py "Quais as 3 regiões com mais ocorrências e quantas viaturas disponíveis as unidades responsáveis têm?"
```

Ou modo interativo (sem passar pergunta como argumento):

```bash
docker compose --profile full run --rm agente python main.py
```

Para voltar ao estado "só bancos" entre uma aula e outra:

```bash
docker compose --profile full stop mcp-ocorrencias mcp-operacoes mcp-servicos
```

## Extra — exemplos via HTTP (14 a 17)

Os exemplos 14 a 17 usam **Streamable HTTP** em vez de stdio: o MCP Server é um
serviço que fica de pé sozinho e o cliente chega nele por **URL**, então os dois
podem estar em máquinas diferentes. Não precisam de Docker nem de banco (só do
`pip install -r requirements.txt` e, nos agentes, da chave no `.env`).

| Exemplo | O que mostra | Como rodar |
|---|---|---|
| `14_mcp_http_basico` | Server HTTP, cliente Python e a conversa JSON-RPC "crua" | `python server.py` em um terminal; `python cliente.py` e `python requisicao_bruta.py` em outro |
| `15_agente_mcp_http` | Agente que só conhece a URL do server | server do 14 no ar; `python agente.py` |
| `16_mcp_http_autenticado` | Server protegido por token Bearer (401 sem token) | `MCP_TOKEN=segredo python server.py`; mesmo `MCP_TOKEN` no `python cliente.py` |
| `17_mcp_http_distribuido` | Agente com 2 servers remotos que segue funcionando se um cair | servers do 14 e do 16 no ar; `MCP_TOKEN=segredo python agente.py` |

No PowerShell, defina variáveis assim: `$env:MCP_TOKEN = "segredo"; python server.py`.

**Rodando em máquinas diferentes.** Por padrão o server escuta só em
`127.0.0.1` (a própria máquina). Para aceitar outras máquinas, suba-o com
`MCP_HOST=0.0.0.0` e, no cliente, aponte a URL para o IP dele:

```bash
# máquina A (server)
MCP_HOST=0.0.0.0 python server.py
# máquina B (cliente ou agente)
MCP_URL=http://IP_DA_MAQUINA_A:8000/mcp python agente.py
```

O firewall da máquina A precisa liberar a porta (8000, ou 8010 no exemplo 16). Como
a turma é remota e não compartilha rede, uma alternativa é publicar a porta com um
túnel (por exemplo `cloudflared tunnel --url http://localhost:8000`) e usar a URL
`https://...` gerada como `MCP_URL`. **Mesmo com túnel, suba o server com
`MCP_HOST=0.0.0.0`**: com `127.0.0.1` o SDK rejeita, com `421 Invalid Host header`, qualquer
requisição cujo `Host` não seja o da própria máquina. **Nunca exponha o exemplo 14 (sem
autenticação) na internet com dados reais**: para isso existe o 16.

## Estrutura

```
aula5/
├── docker-compose.yml       # bancos (padrão) + MCP Servers/agente (profile "full")
├── dados/                   # referência canônica + geradores de massa
├── banco-postgres/init.sql  # schema OCORRÊNCIAS
├── banco-sqlserver/init.sql # schema OPERAÇÕES
├── exemplos/                # 01..11, cada um = 1 passo da aula; 14..17 = MCP via HTTP
├── mcp-ocorrencias/         # MCP Server 1 (Postgres)
├── mcp-operacoes/           # MCP Server 2 (SQL Server)
├── mcp-servicos/            # MCP Server 3 (sem banco)
├── agente/                  # Agente final (OpenAI Agents SDK) via Streamable HTTP
└── Dockerfile.dev-runner    # imagem auxiliar p/ troubleshooting de rede (ver aula-05.md)
```

## Troubleshooting

Ver a seção **TROUBLESHOOTING** em `aula-05.md` — cobre porta ocupada,
credencial incorreta, MCP Server que não sobe, schema de tool mal
descrito, timeout, e um bug específico de proxy de porta do Docker
Desktop para Windows que pode aparecer em algumas máquinas.

## Usando Ollama (llama local) em vez da OpenAI

O `provedor.py` é o mesmo das aulas anteriores. No `.env`:

```
PROVEDOR=ollama
OPENAI_DEFAULT_MODEL=llama3.1     # o SDK usa esta variável como nome do modelo
OLLAMA_BASE_URL=http://localhost:11434/v1
```

Limitações observadas: o contexto padrão do Ollama é 4096 tokens e os
resultados das tools (dezenas de linhas) podem estourá-lo; em CPU, cada
chamada é bem lenta. Para a aula, prefira a OpenAI; com Ollama, aumente
`num_ctx` (ex.: `OLLAMA_CONTEXT_LENGTH=16384`) e use modelo com GPU.
