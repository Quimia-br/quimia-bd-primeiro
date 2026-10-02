-- =================================
-- DROP TABLES
-- =================================

DROP TABLE IF EXISTS historicos_produtos CASCADE;
DROP TABLE IF EXISTS historicos CASCADE;
DROP TABLE IF EXISTS produtos_usuarios CASCADE;
DROP TABLE IF EXISTS descartes_fds CASCADE;
DROP TABLE IF EXISTS admin_log_edicoes CASCADE;
DROP TABLE IF EXISTS estantes CASCADE;
DROP TABLE IF EXISTS localizacoes CASCADE;
DROP TABLE IF EXISTS produtos CASCADE;
DROP TABLE IF EXISTS tipos_historicos CASCADE;
DROP TABLE IF EXISTS admins CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS usuarios_empresas CASCADE;
DROP TABLE IF EXISTS produtos_estantes CASCADE;

-- ================================
-- TABELAS INDEPENDENTES
-- ================================

CREATE TABLE usuarios_empresas(
    id_usuario_empresa INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cnpj VARCHAR (14) NOT NULL UNIQUE,
    nome VARCHAR (150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    porte VARCHAR (15) NOT NULL DEFAULT 'DESCONHECIDO',
    data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    senha_hash VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    url_foto TEXT,
    CONSTRAINT chk_porte CHECK (porte IN ('PEQUENO', 'MEDIO', 'DESCONHECIDO', 'MICRO', 'GRANDE')),
    CONSTRAINT chk_url_foto CHECK(url_foto LIKE 'http://%' OR url_foto LIKE 'https://%'),
    CONSTRAINT chk_status CHECK (status IN ('ATIVO', 'INATIVO', 'PENDENTE','BLOQUEADO', 'DESATIVADO'))
 );

CREATE TABLE admins(
    id_admin INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    CONSTRAINT chk_status CHECK (status IN ('ATIVO', 'INATIVO', 'PENDENTE','BLOQUEADO', 'DESATIVADO'))
);

CREATE TABLE tipos_historicos(
    id_tipo_historico INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE usuarios(   
    id_usuario INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    data_nascimento DATE, 
    email VARCHAR(150) NOT NULL UNIQUE,
    data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    senha_hash VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    url_foto TEXT,
    CONSTRAINT chk_status CHECK (status IN ('ATIVO', 'INATIVO', 'PENDENTE','BLOQUEADO', 'DESATIVADO')),
    CONSTRAINT chk_url_foto CHECK(url_foto LIKE 'http://%' OR url_foto LIKE 'https://%')

);

-- ============================
-- TABELAS DEPENDENTES
-- ============================

CREATE TABLE produtos(
    id_produto INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario_empresa INT NOT NULL,
    cas_number VARCHAR(12) NOT NULL UNIQUE, 
    nome VARCHAR(150) NOT NULL,
    marca VARCHAR(150) NOT NULL DEFAULT 'DESCONHECIDO',
    instrucao_de_uso TEXT NOT NULL,
    dosagem_tecnica TEXT NOT NULL
);

CREATE TABLE produtos_usuarios( 
    id_produto INT NOT NULL,
    id_usuario INT NOT NULL,
    PRIMARY KEY(id_usuario, id_produto)
);

CREATE TABLE admin_log_edicoes(
    id_admin_log_edicao INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_admin INT NOT NULL,
    tabela_afetada VARCHAR(150) NOT NULL,
    id_registro INT NOT NULL,
    acao VARCHAR(50) NOT NULL,
    dado_anterior TEXT,
    data_edicao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_acao CHECK (acao IN ('INSERT', 'UPDATE', 'DELETE'))
);

CREATE TABLE localizacoes(
    id_localizacao INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE,
    cep VARCHAR(8) NOT NULL, 
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    CONSTRAINT chk_latitude CHECK(latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_longitude CHECK(longitude BETWEEN -180 AND 180)
);

CREATE TABLE estantes( 
    id_estante INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario INT NOT NULL,
    comodo VARCHAR(150) NOT NULL DEFAULT 'DESCONHECIDO',
    UNIQUE(id_estante, id_usuario),
    UNIQUE(id_usuario, comodo)
);

CREATE TABLE historicos( 
    id_historico INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_estante INT,
    id_usuario INT NOT NULL,
    id_tipo_historico INT NOT NULL,
    data_execucao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    descricao_resultado VARCHAR(255),
    UNIQUE(id_historico, id_usuario)
);

CREATE TABLE produtos_estantes(
    id_estante INT NOT NULL,
    id_produto INT NOT NULL,
    data_adicao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(id_estante, id_produto)
);

-- ==========================
-- TABELA FDS
-- ==========================

CREATE TABLE descartes_fds( 
    id_descarte_fds INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_produto INT NOT NULL UNIQUE,
    metodo_descarte_produto TEXT,
    metodo_descarte_embalagem TEXT,
    restricao_descarte TEXT,
    precaucao_ambiental TEXT
);

-- ===========================
-- TABELA ASSOCIATIVA
-- ===========================

CREATE TABLE historicos_produtos(
    id_historico_produto INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_produto INT NOT NULL,
    id_historico INT NOT NULL,
    id_usuario INT NOT NULL,
    UNIQUE(id_historico, id_produto)
);
