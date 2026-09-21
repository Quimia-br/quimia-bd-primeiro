ALTER TABLE usuario DROP COLUMN tipo;
ALTER TABLE localizacao DROP CONSTRAINT chk_cep;
ALTER TABLE localizacao DROP CONSTRAINT regex_latitude
ALTER TABLE localizacao DROP CONSTRAINT regex_longitude
ALTER TABLE usuario DROP CONSTRAINT regex_email
ALTER TABLE usuario_empresa DROP CONSTRAINT regex_cnpj
ALTER TABLE produto DROP CONSTRAINT regex_cas_number