ALTER TABLE localizacao 
ALTER COLUMN longitude TYPE NUMERIC(9,6)
USING longitude::numeric(9,6);

ALTER TABLE localizacao
ALTER COLUMN latitude TYPE NUMERIC(9,6)
USING latitude::numeric(9,6);