-- CISP - Central Integrada de Segurança Pública
-- Sistema 1: OCORRÊNCIAS (PostgreSQL)
-- Este script cria apenas o ESQUEMA. A massa de dados é gerada por
-- dados/seed_postgres.py (determinística, ~20.000 ocorrências).
-- Executado automaticamente pelo container postgres (docker-entrypoint-initdb.d).

CREATE TABLE IF NOT EXISTS regioes (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(10)  NOT NULL UNIQUE,   -- ex: 'ALFA'
    nome        VARCHAR(60)  NOT NULL,           -- ex: 'Região Alfa'
    zona        VARCHAR(20)  NOT NULL            -- NORTE / SUL / LESTE / OESTE / CENTRO
);

CREATE TABLE IF NOT EXISTS tipos_ocorrencia (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(30) NOT NULL UNIQUE,  -- ex: 'ROUBO'
    nome            VARCHAR(60) NOT NULL,          -- ex: 'Roubo'
    categoria       VARCHAR(30) NOT NULL,          -- PATRIMONIAL / VIOLENTO / TRANSITO / OUTROS
    gravidade_base  VARCHAR(10) NOT NULL           -- BAIXA / MEDIA / ALTA / CRITICA
);

CREATE TABLE IF NOT EXISTS unidades (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(20)  NOT NULL UNIQUE,   -- ex: 'DP-ALFA-01' (mesmo código usado no MCP Operações)
    nome        VARCHAR(80)  NOT NULL,
    regiao_id   INTEGER      NOT NULL REFERENCES regioes(id)
);

CREATE TABLE IF NOT EXISTS ocorrencias (
    id                  BIGSERIAL PRIMARY KEY,
    data_hora           TIMESTAMP    NOT NULL,
    tipo_ocorrencia_id  INTEGER      NOT NULL REFERENCES tipos_ocorrencia(id),
    regiao_id           INTEGER      NOT NULL REFERENCES regioes(id),
    gravidade           VARCHAR(10)  NOT NULL,   -- BAIXA / MEDIA / ALTA / CRITICA
    status              VARCHAR(20)  NOT NULL,   -- REGISTRADA / EM_ANDAMENTO / CONCLUIDA / ARQUIVADA
    unidade_responsavel_id INTEGER   NOT NULL REFERENCES unidades(id),
    latitude            NUMERIC(9,6) NOT NULL,
    longitude           NUMERIC(9,6) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ocorrencias_data_hora ON ocorrencias (data_hora);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_regiao ON ocorrencias (regiao_id);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_tipo ON ocorrencias (tipo_ocorrencia_id);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_unidade ON ocorrencias (unidade_responsavel_id);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_gravidade ON ocorrencias (gravidade);
