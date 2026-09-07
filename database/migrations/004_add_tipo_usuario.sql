ALTER TABLE usuario
ADD COLUMN tipo VARCHAR(20) NOT NULL DEFAULT 'comum'
CHECK (tipo IN ('admin', 'comum'));