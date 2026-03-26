-- Transparência Brasil — Schema PostgreSQL
-- Execute: psql -U postgres -d transparencia_brasil -f schema.sql

CREATE DATABASE IF NOT EXISTS transparencia_brasil;
\c transparencia_brasil;

-- Estados brasileiros
CREATE TABLE IF NOT EXISTS estados (
    id       SERIAL PRIMARY KEY,
    uf       CHAR(2)      NOT NULL UNIQUE,
    nome     VARCHAR(100) NOT NULL,
    regiao   CHAR(2)      NOT NULL CHECK (regiao IN ('N','NE','CO','SE','S')),
    capital  VARCHAR(100),
    area_km2 NUMERIC(12,2)
);

-- Indicadores brutos por estado e ano
CREATE TABLE IF NOT EXISTS indicadores (
    id          SERIAL PRIMARY KEY,
    estado_id   INTEGER      NOT NULL REFERENCES estados(id) ON DELETE CASCADE,
    ano         SMALLINT     NOT NULL,
    categoria   VARCHAR(50)  NOT NULL, -- educacao, saude, seguranca, economia
    nome        VARCHAR(200) NOT NULL,
    valor       NUMERIC(15,4),
    unidade     VARCHAR(50),
    fonte       VARCHAR(100),
    data_coleta DATE,
    UNIQUE (estado_id, ano, categoria, nome)
);

-- Scores calculados por estado e ano
CREATE TABLE IF NOT EXISTS scores_estados (
    id          SERIAL PRIMARY KEY,
    estado_id   INTEGER  NOT NULL REFERENCES estados(id) ON DELETE CASCADE,
    ano         SMALLINT NOT NULL,
    educacao    NUMERIC(5,2) DEFAULT 0,
    saude       NUMERIC(5,2) DEFAULT 0,
    seguranca   NUMERIC(5,2) DEFAULT 0,
    economia    NUMERIC(5,2) DEFAULT 0,
    score_geral NUMERIC(5,2) DEFAULT 0,
    UNIQUE (estado_id, ano)
);

-- Políticos (Fase 3)
CREATE TABLE IF NOT EXISTS politicos (
    id            SERIAL PRIMARY KEY,
    nome          VARCHAR(200) NOT NULL,
    partido       VARCHAR(30),
    uf            CHAR(2),
    cargo         VARCHAR(50),  -- deputado_federal, senador
    id_externo    INTEGER,
    foto_url      TEXT,
    email         VARCHAR(200),
    ativo         BOOLEAN DEFAULT TRUE
);

-- Votações (Fase 3)
CREATE TABLE IF NOT EXISTS votacoes (
    id            SERIAL PRIMARY KEY,
    politico_id   INTEGER REFERENCES politicos(id),
    data_votacao  DATE,
    proposicao    VARCHAR(500),
    voto          VARCHAR(50),   -- Sim, Não, Abstenção, Faltou
    fonte         VARCHAR(100)
);

-- Índices de performance
CREATE INDEX IF NOT EXISTS idx_indicadores_estado_ano ON indicadores(estado_id, ano);
CREATE INDEX IF NOT EXISTS idx_scores_estado_ano      ON scores_estados(estado_id, ano);
CREATE INDEX IF NOT EXISTS idx_politicos_uf           ON politicos(uf);
CREATE INDEX IF NOT EXISTS idx_votacoes_politico      ON votacoes(politico_id);

-- Municípios (Fase 4)
CREATE TABLE IF NOT EXISTS municipios (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  codigo_ibge TEXT UNIQUE,
  nome        TEXT NOT NULL,
  uf          TEXT NOT NULL,
  regiao      TEXT,
  populacao   INTEGER,
  area_km2    REAL,
  educacao    REAL,
  saude       REAL,
  seguranca   REAL,
  economia    REAL,
  score       REAL,
  ano         INTEGER DEFAULT 2023
);

CREATE INDEX IF NOT EXISTS idx_municipios_uf    ON municipios(uf);
CREATE INDEX IF NOT EXISTS idx_municipios_score ON municipios(score);
