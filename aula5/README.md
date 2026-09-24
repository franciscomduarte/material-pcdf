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

## Estrutura

```
aula5/
├── docker-compose.yml       # bancos (padrão) + MCP Servers/agente (profile "full")
├── dados/                   # referência canônica + geradores de massa
├── banco-postgres/init.sql  # schema OCORRÊNCIAS
├── banco-sqlserver/init.sql # schema OPERAÇÕES
├── exemplos/                # 01..11, cada um = 1 passo da aula
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
