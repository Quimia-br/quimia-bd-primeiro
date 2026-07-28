-- =================================
-- DROP TABLES
-- =================================
DROP TABLE IF EXISTS historico_produto_mistura;
DROP TABLE IF EXISTS descarte_fds;
DROP TABLE IF EXISTS composto_fds;
DROP TABLE IF EXISTS localizacao;
DROP TABLE IF EXISTS historico;
DROP TABLE IF EXISTS tipo_historico;
DROP TABLE IF EXISTS produto_usuario;
DROP TABLE IF EXISTS produto_superficie;
DROP TABLE IF EXISTS produto;
DROP TABLE IF EXISTS estante;
DROP TABLE IF EXISTS comodo;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS superficie;
DROP TABLE IF EXISTS usuario_empresa;

-- ================================
-- TABELAS PRINCIPAIS
-- ================================
CREATE TABLE usuario_empresa(
    id_usuario_empresa INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cnpj VARCHAR (14) NOT NULL UNIQUE,
    nome VARCHAR (150) NOT NULL,
    porte VARCHAR (15) NOT NULL DEFAULT 'Desconhecido',
    CONSTRAINT regex_cnpj CHECK (cnpj ~ '^\d{14}$')
);

CREATE TABLE superficie(
    id_superficie INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    material VARCHAR(50) NOT NULL DEFAULT 'Sem informação'
);

CREATE TABLE tipo_historico(
    id_tipo_historico INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150) NOT NULL
);

CREATE TABLE usuario(   
    id_usuario INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    data_nascimento DATE, 
    email VARCHAR(150) NOT NULL UNIQUE,
    CONSTRAINT regex_email CHECK (email ~ '^[^\s@]+@[^\s@]+\.[^\s@]+$') -- REGRA PARA VERIFICAR FORMATO DO EMAIL
);

CREATE TABLE comodo(
    id_comodo INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150) NOT NULL DEFAULT 'Desconhecido'
);

-- ============================
-- TABELAS PRODUTO
-- ============================

CREATE TABLE produto( -- PRECISA DE VERIFICAÇÃO RELACIONAMENTO
    id_produto INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario_empresa INT NOT NULL,
    cas_number VARCHAR(12) NOT NULL UNIQUE, -- ALTEREI O TIPO DE DADO PARA VARCHAR, PORQUE GERALMENTE O CAS NUMBER USA HIFEN
    nome VARCHAR(150) NOT NULL,
    marca VARCHAR(150) DEFAULT 'Sem informação',
    intrucoes_de_uso VARCHAR(255) NOT NULL,
    dosagem_tecnica VARCHAR(255) NOT NULL,
    CONSTRAINT regex_cas_number CHECK (cas_number ~ '^\d{2,7}-\d{2}-\d$')-- REGRA REGEX PARA VERIFICAR CAS NUMBER
);

CREATE TABLE produto_usuario( -- PRECISA VERIFICAR RELACIONAMENTO
    id_produto_usuario INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_produto INT NOT NULL,
    id_usuario INT NOT NULL
);

CREATE TABLE produto_superficie( -- PRECISA VERIFICAR RELACIONAMENTO
    id_produto_superficie INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_produto INT NOT NULL,
    id_superficie INT NOT null
);

-- ============================
-- TABELAS FDS
-- ============================
CREATE TABLE descarte_fds( 
    id_descarte_fds INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_produto INT NOT NULL UNIQUE,
    metodo_descarte_produto VARCHAR(255),
    metodo_descarte_embalagem VARCHAR(255),
    restricao_descarte VARCHAR(255),
    precaucao_ambiental VARCHAR(255)
);

CREATE TABLE composto_fds( 
    id_composto_fds INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_produto INT NOT NULL, 
    percentual_min NUMERIC(10, 4),
    percentual_max NUMERIC(10, 4),
    classificacao_ghs VARCHAR(255)
);

-- ==========================
-- TABELAS DEPENDENTES
-- ==========================
CREATE TABLE estante( -- VERIFICAR RELACIONAMENTO
    id_estante INT GENERATED ALWAYS AS IDENTITY  PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_comodo INT
);

CREATE TABLE localizacao(
    id_localizacao INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario INT,
    cep VARCHAR(18) NOT NULL, -- MUDEI PARA VARCHAR POR CAUSA DOS HIFENS
    latitude VARCHAR(255),
    longitude VARCHAR(255)
);

CREATE TABLE historico( -- VERIFICAR RELACIONAMENTO
    id_historico INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_estante INT NOT NULL,
    id_usuario INT,
    id_tipo_historico INT NOT NULL, 
    id_produto_superficie INT,
    id_produto_usuario INT,
    data_execucao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    horario TIME,
    descricao_resultado VARCHAR(255)
);

-- ===========================
-- TABELA ASSOCIATIVA
-- ===========================
CREATE TABLE historico_produto_mistura(
    id_produto INT NOT NULL,
    id_historico INT NOT NULL,
    PRIMARY KEY (id_produto, id_historico)
);

