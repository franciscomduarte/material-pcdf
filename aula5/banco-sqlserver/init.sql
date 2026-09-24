-- CISP - Central Integrada de Segurança Pública
-- Sistema 2: OPERAÇÕES (SQL Server)
-- Este script cria apenas o ESQUEMA. A massa de dados é gerada por
-- dados/seed_sqlserver.py (determinística, 20-30 unidades, 100-150 viaturas,
-- 200-400 equipes).
-- Diferente do Postgres: este banco não é inicializado automaticamente por
-- docker-entrypoint-initdb.d (a imagem oficial do mssql não tem esse hook).
-- Por isso ele é aplicado manualmente com sqlcmd -- veja README.md.

IF DB_ID('cisp_operacoes') IS NULL
BEGIN
    CREATE DATABASE cisp_operacoes;
END
GO

USE cisp_operacoes;
GO

IF OBJECT_ID('dbo.equipes', 'U') IS NOT NULL DROP TABLE dbo.equipes;
IF OBJECT_ID('dbo.historico_viaturas', 'U') IS NOT NULL DROP TABLE dbo.historico_viaturas;
IF OBJECT_ID('dbo.viaturas', 'U') IS NOT NULL DROP TABLE dbo.viaturas;
IF OBJECT_ID('dbo.unidades', 'U') IS NOT NULL DROP TABLE dbo.unidades;
GO

CREATE TABLE dbo.unidades (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    codigo      VARCHAR(20)  NOT NULL UNIQUE,   -- mesmo código usado no MCP Ocorrências
    nome        VARCHAR(80)  NOT NULL,
    regiao      VARCHAR(60)  NOT NULL,          -- texto livre: nome da região (sem FK entre bancos)
    tipo        VARCHAR(30)  NOT NULL,          -- DELEGACIA / BATALHAO / BASE_COMUNITARIA / CIA_PM
    latitude    DECIMAL(9,6) NOT NULL,
    longitude   DECIMAL(9,6) NOT NULL
);
GO

CREATE TABLE dbo.viaturas (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    prefixo             VARCHAR(20)  NOT NULL UNIQUE,   -- ex: 'VTR-0231'
    unidade_id          INT          NOT NULL FOREIGN KEY REFERENCES dbo.unidades(id),
    tipo                VARCHAR(20)  NOT NULL,          -- VTR / MOTO / BLINDADO / RESGATE
    status              VARCHAR(20)  NOT NULL,          -- DISPONIVEL / EM_ATENDIMENTO / EM_DESLOCAMENTO / MANUTENCAO / INDISPONIVEL
    latitude            DECIMAL(9,6) NOT NULL,
    longitude            DECIMAL(9,6) NOT NULL,
    ultima_atualizacao  DATETIME2    NOT NULL
);
GO

CREATE TABLE dbo.equipes (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    unidade_id          INT          NOT NULL FOREIGN KEY REFERENCES dbo.unidades(id),
    turno               VARCHAR(20)  NOT NULL,   -- DIURNO / NOTURNO / INTEGRAL
    quantidade_agentes  INT          NOT NULL,
    especialidade       VARCHAR(30)  NOT NULL,   -- PATRULHAMENTO / INVESTIGACAO / TATICO / TRANSITO
    status              VARCHAR(20)  NOT NULL    -- EM_SERVICO / FOLGA / TREINAMENTO
);
GO

CREATE TABLE dbo.historico_viaturas (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    viatura_id          INT          NOT NULL FOREIGN KEY REFERENCES dbo.viaturas(id),
    status              VARCHAR(20)  NOT NULL,
    data_hora_inicio    DATETIME2    NOT NULL,
    data_hora_fim       DATETIME2    NULL
);
GO

CREATE INDEX idx_viaturas_unidade ON dbo.viaturas (unidade_id);
CREATE INDEX idx_viaturas_status ON dbo.viaturas (status);
CREATE INDEX idx_equipes_unidade ON dbo.equipes (unidade_id);
CREATE INDEX idx_historico_viatura ON dbo.historico_viaturas (viatura_id);
GO
