CREATE TABLE admin(
    id_admin INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    CONSTRAINT chk_data_cadastro CHECK (data_cadastro <= CURRENT_TIMESTAMP),
    CONSTRAINT chk_senha_hash CHECK (LENGTH(senha_hash) >= 8) 
);

CREATE TABLE admin_log_edicao(
    id_admin_log_edicao INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_admin INT,
    tabela_afetada VARCHAR(150) NOT NULL,
    id_registro INT NOT NULL,
    acao VARCHAR(50) NOT NULL,
    dados_anteriores JSONB,
    dados_novos JSONB,
    data_edicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_acao CHECK (acao IN ('INSERT', 'UPDATE', 'DELETE'))
);





