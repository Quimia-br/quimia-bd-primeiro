-- ================================
-- HISTORICOS --> TIPOS_HISTORICOS
-- ================================

ALTER TABLE historicos ADD CONSTRAINT fk_historico_tipo_historico
    FOREIGN KEY (id_tipo_historico)
    REFERENCES tipos_historicos (id_tipo_historico);

-- ================================
-- HISTORICOS --> USUARIOS
-- ================================

ALTER TABLE historicos ADD CONSTRAINT fk_historico_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES usuarios (id_usuario);

-- ================================
-- HISTORICOS --> ESTANTES          
-- ================================

ALTER TABLE historicos ADD CONSTRAINT fk_historico_estante
    FOREIGN KEY (id_estante, id_usuario)
    REFERENCES estantes (id_estante, id_usuario);

-- ================================
-- PRODUTOS --> USUARIOS_EMPRESAS
-- ================================

ALTER TABLE produtos ADD CONSTRAINT fk_produto_usuario_empresa
    FOREIGN KEY (id_usuario_empresa)
    REFERENCES usuarios_empresas (id_usuario_empresa);

-- ================================
-- ESTANTES --> USUARIOS
-- ================================

ALTER TABLE estantes ADD CONSTRAINT fk_estante_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES usuarios (id_usuario);

-- ================================
-- PRODUTOS_USUARIOS --> USUARIOS
-- ================================

ALTER TABLE produtos_usuarios ADD CONSTRAINT fk_produto_usuario_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES usuarios (id_usuario);

-- ================================
-- PRODUTOS_USUARIOS --> PRODUTOS
-- ================================

ALTER TABLE produtos_usuarios ADD CONSTRAINT fk_produto_usuario_produto
    FOREIGN KEY (id_produto)
    REFERENCES produtos (id_produto);

-- ================================
-- LOCALIZACOES --> USUARIOS
-- ================================

ALTER TABLE localizacoes ADD CONSTRAINT fk_localizacao_usuario
    FOREIGN KEY (id_usuario) 
    REFERENCES usuarios (id_usuario);

-- ================================
-- DESCARTES_FDS --> PRODUTOS
-- ================================

ALTER TABLE descartes_fds ADD CONSTRAINT fk_descarte_fds_produto
    FOREIGN KEY (id_produto)
    REFERENCES produtos (id_produto);

-- ================================
-- ADMIN_LOG_EDICOES --> ADMINS
-- ================================

ALTER TABLE admin_log_edicoes ADD CONSTRAINT fk_admin_log_edicao_admin
    FOREIGN KEY (id_admin)
    REFERENCES admins (id_admin);

-- ================================
-- HISTORICOS_PRODUTOS --> HISTORICOS
-- ================================

ALTER TABLE historicos_produtos ADD CONSTRAINT fk_historico_produto_historico
    FOREIGN KEY (id_historico, id_usuario)
    REFERENCES historicos (id_historico, id_usuario);

-- ================================
-- HISTORICOS_PRODUTOS --> PRODUTOS_USUARIOS
-- ================================

ALTER TABLE historicos_produtos ADD CONSTRAINT fk_historico_produto_produto_usuario
    FOREIGN KEY (id_usuario, id_produto)
    REFERENCES produtos_usuarios (id_usuario, id_produto);

-- ================================
-- PRODUTOS_ESTANTES --> ESTANTES
-- ================================

ALTER TABLE produtos_estantes ADD CONSTRAINT fk_produto_estante_estante
    FOREIGN KEY (id_estante)
    REFERENCES estantes (id_estante);

-- ================================
-- PRODUTOS_ESTANTES --> PRODUTOS
-- ================================

ALTER TABLE produtos_estantes ADD CONSTRAINT fk_produto_estante_produto
    FOREIGN KEY (id_produto)
    REFERENCES produtos (id_produto);