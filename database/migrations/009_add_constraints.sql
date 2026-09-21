--=============================
-- CONSTRAINTS DE VALIDAÇÃO
--============================

ALTER TABLE usuario_empresa
ADD CONSTRAINT chk_porte CHECK (porte IN ('Pequeno', 'Médio', 'Desconhecido', 'Micro', 'Grande'));

UPDATE localizacao
SET cep = REPLACE(cep, '-', '') WHERE cep LIKE '%-%';

ALTER TABLE usuario
ADD CONSTRAINT chk_data_de_nascimento_valida CHECK (data_nascimento <= CURRENT_DATE);

ALTER TABLE usuario
RENAME CONSTRAINT usuario_tipo_check TO chk_tipo_usuario;

ALTER TABLE localizacao
ADD CONSTRAINT chk_longitude CHECK(longitude BETWEEN -180 AND 180);

ALTER TABLE localizacao
ADD CONSTRAINT chk_latitude CHECK(latitude BETWEEN -90 AND 90);

ALTER TABLE usuario
RENAME CONSTRAINT chk_data_de_nascimento_valido TO chk_data_nascimento;

ALTER TABLE usuario
DROP COLUMN tipo;

ALTER TABLE estante
DROP COLUMN id_comodo;

ALTER TABLE estante
ADD COLUMN comodo VARCHAR(150) NOT NULL;

ALTER TABLE admin_log_edicao ADD CONSTRAINT fk_admin_log_edicao_admin
    FOREIGN KEY (id_admin) 
    REFERENCES admin (id_admin);

ALTER TABLE admin_log_edicao ADD CONSTRAINT fk_admin_log_edicao_admin
    FOREIGN KEY (id_admin)
    REFERENCES admin (id_admin);
