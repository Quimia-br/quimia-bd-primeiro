--=============================
-- CONSTRAINTS DE VALIDAÇÃO
--============================

ALTER TABLE usuario_empresa
ADD CONSTRAINT chk_porte CHECK (porte IN ('Pequeno', 'Médio', 'Desconhecido', 'Micro', 'Grande'));

UPDATE localizacao
SET cep = REPLACE(cep, '-', '') WHERE cep LIKE '%-%';

ALTER TABLE localizacao
ADD CONSTRAINT chk_cep CHECK (cep ~ '^\d{8}$'); 

ALTER TABLE localizacao
ADD CONSTRAINT regex_latitude CHECK (latitude ~ '^-?\d{1,2}(\.\d+)?$');

ALTER TABLE localizacao
ADD CONSTRAINT regex_longitude CHECK (longitude ~ '^-?\d{1,3}(\.\d+)?$');

ALTER TABLE usuario
ADD CONSTRAINT chk_data_de_nascimento_valida CHECK (data_nascimento <= CURRENT_DATE);

ALTER TABLE usuario
RENAME CONSTRAINT usuario_tipo_check TO chk_tipo_usuario;